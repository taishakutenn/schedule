"""
Service layer для бэкапа и восстановления базы данных.
"""

import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Any
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from db.models import Base

logger = logging.getLogger(__name__)


class BackupService:
    """Сервис для операций бэкапа/восстановления БД"""
    
    BACKUP_DIR = Path("data/backups")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    def _get_table_names(self) -> List[str]:
        """Получить список всех таблиц из метаданных SQLAlchemy."""
        return sorted(Base.metadata.tables.keys())
    
    def _deserialize_value(self, value: Any, column) -> Any:
        """Конвертирует сериализованные значения обратно в исходные типы."""
        if value is None:
            return None
        
        # Безопасное получение имени типа как строки
        col_type_name = type(column.type).__name__
        
        if isinstance(value, str):
            if col_type_name == 'Date':
                try:
                    return datetime.fromisoformat(value).date()
                except (ValueError, AttributeError):
                    return value
            
            elif col_type_name == 'DateTime':
                try:
                    return datetime.fromisoformat(value.replace(' ', 'T'))
                except (ValueError, AttributeError):
                    return value
            
            elif col_type_name in ('UUID', '_UUID'):
                try:
                    return UUID(value)
                except (ValueError, AttributeError):
                    return value
            
            elif col_type_name in ('Numeric', 'Float', 'Double', 'DoublePrecision'):
                try:
                    return Decimal(value)
                except:
                    try:
                        return float(value)
                    except:
                        return value
            
            elif col_type_name in ('Integer', 'BigInteger', 'SmallInteger'):
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return value
            
            elif col_type_name == 'Boolean':
                if value.lower() in ('true', '1', 'yes'):
                    return True
                elif value.lower() in ('false', '0', 'no'):
                    return False
        
        return value
    
    async def _get_table_data(self, session: AsyncSession, table_name: str) -> List[Dict[str, Any]]:
        """Получить все данные из таблицы."""
        table = Base.metadata.tables.get(table_name)
        if table is None:
            return []
        
        query = select(table)
        result = await session.execute(query)
        rows = result.fetchall()
        
        data = []
        for row in rows:
            row_dict = {}
            for key, value in row._mapping.items():
                if hasattr(value, 'isoformat'):
                    row_dict[key] = value.isoformat()
                elif isinstance(value, UUID):
                    row_dict[key] = str(value)
                elif isinstance(value, Decimal):
                    row_dict[key] = float(value)
                else:
                    row_dict[key] = value
            data.append(row_dict)
        
        return data
    
    async def create_backup(self, session: AsyncSession) -> Dict[str, Any]:
        """Создать бэкап всей базы данных."""
        try:
            backup_data = {
                "backup_timestamp": datetime.now().isoformat(),
                "tables": {}
            }
            
            table_names = self._get_table_names()
            for table_name in table_names:
                backup_data["tables"][table_name] = await self._get_table_data(session, table_name)
            
            backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            backup_path = self.BACKUP_DIR / backup_filename
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            return {
                "message": "Бэкап успешно создан",
                "filename": backup_filename,
                "path": str(backup_path),
                "tables_count": len(table_names),
                "timestamp": backup_data["backup_timestamp"]
            }
            
        except Exception as e:
            logger.error(f"Ошибка при создании бэкапа: {e}")
            raise HTTPException(status_code=500, detail=f"Ошибка при создании бэкапа: {str(e)}")
    
    def _get_table_insert_order(self) -> List[str]:
        """Порядок вставки таблиц на основе внешних ключей."""
        return [
            "teacher_categories", "payment_forms", "session_types", "buildings", "users",
            "teachers", "teachers_buildings",
            "specialties", "groups",
            "plans", "chapter_in_plan", "cycle_in_chapter", "module_in_cycle", 
            "subjects_in_cycle", "subjects_in_cycle_hours", "semesters",
            "certifications", "teachers_in_plans", "streams",
            "cabinets", "sessions", "schedule"
        ]

    async def _validate_fk_integrity(self, backup_tables: Dict[str, List[Dict]]) -> List[str]:
        """Проверяет целостность внешних ключей в бэкапе."""
        errors = []
        for table_name, data in backup_tables.items():
            table = Base.metadata.tables.get(table_name)
            # ✅ ИСПРАВЛЕНО: явная проверка на None вместо булевой оценки объекта Table
            if table is None or not data:
                continue
                
            for fk in table.foreign_keys:
                ref_table = fk.column.table.name
                ref_col = fk.column.name
                local_col = fk.parent.name
                
                if ref_table not in backup_tables:
                    continue
                
                ref_values = {r.get(ref_col) for r in backup_tables[ref_table]}
                local_values = {r.get(local_col) for r in data if r.get(local_col) is not None}
                
                missing = local_values - ref_values - {None}
                if missing:
                    sample = sorted(missing)[:3]
                    errors.append(
                        f"{table_name}.{local_col}: значения {sample} "
                        f"не найдены в {ref_table}.{ref_col}"
                    )
        return errors

    async def restore_backup(self, session: AsyncSession, file_content: bytes) -> Dict[str, Any]:
        """Восстановить базу данных из JSON файла."""
        try:
            backup_data = json.loads(file_content.decode('utf-8'))

            if "tables" not in backup_data:
                raise HTTPException(status_code=400, detail="Неверный формат файла бэкапа")

            fk_errors = await self._validate_fk_integrity(backup_data["tables"])
            if fk_errors:
                raise HTTPException(
                    status_code=400, 
                    detail="Нарушения целостности данных: " + "; ".join(fk_errors)
                )

            ordered_tables = self._get_table_insert_order()
            backup_tables_set = set(backup_data["tables"].keys())
            tables_to_restore = [t for t in ordered_tables if t in backup_tables_set]
            
            for table_name in backup_tables_set:
                if table_name not in tables_to_restore:
                    tables_to_restore.append(table_name)

            # Этап 1: Очистка
            for table_name in tables_to_restore:
                table = Base.metadata.tables.get(table_name)
                if table is not None:
                    await session.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))

            # Этап 2: Вставка с десериализацией
            tables_restored = []
            for table_name in tables_to_restore:
                table = Base.metadata.tables.get(table_name)
                if table is None:
                    continue

                data = backup_data["tables"][table_name]
                if not data:
                    tables_restored.append(table_name)
                    continue

                for row in data:
                    clean_row = {}
                    for key, value in row.items():
                        column = table.c.get(key)
                        if column is not None:
                            clean_row[key] = self._deserialize_value(value, column)
                        else:
                            clean_row[key] = value
                    if clean_row:
                        await session.execute(insert(table).values(clean_row))

                tables_restored.append(table_name)

            # Этап 3: Сброс последовательностей
            for table_name in tables_to_restore:
                table = Base.metadata.tables.get(table_name)
                if table is not None:
                    try:
                        await session.execute(
                            text(f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), "
                                 f"COALESCE((SELECT MAX(id) FROM {table_name}), 1), true)")
                        )
                    except Exception:
                        pass

            await session.commit()

            return {
                "message": "База данных успешно восстановлена",
                "tables_restored": tables_restored,
                "tables_count": len(tables_restored)
            }

        except json.JSONDecodeError:
            await session.rollback()
            raise HTTPException(status_code=400, detail="Неверный формат JSON файла")
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Ошибка при восстановлении: {e}")
            raise HTTPException(status_code=500, detail=f"Ошибка при восстановлении: {str(e)}")
    
    async def list_backups(self) -> Dict[str, Any]:
        """Получить список доступных файлов бэкапа."""
        try:
            if not self.BACKUP_DIR.exists():
                return {"backups": [], "count": 0}
            
            backups = sorted(
                [f.name for f in self.BACKUP_DIR.glob("backup_*.json")],
                reverse=True
            )
            return {"backups": backups, "count": len(backups)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка при получении списка бэкапов: {str(e)}")
    
    def get_backup_path(self, filename: str) -> Path:
        """Получить путь к файлу бэкапа."""
        if not filename.startswith("backup_") or not filename.endswith(".json"):
            raise HTTPException(status_code=400, detail="Неверный формат имени файла")
        
        backup_path = self.BACKUP_DIR / filename
        if not backup_path.exists():
            raise HTTPException(status_code=404, detail=f"Файл бэкапа не найден: {filename}")
        return backup_path