"""
Service layer для бэкапа и восстановления базы данных.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, insert, text
from uuid import UUID

from db.models import Base


class BackupService:
    """Сервис для операций бэкапа/восстановления БД"""
    
    BACKUP_DIR = Path("data/backups")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    def _get_table_names(self) -> List[str]:
        """Получить список всех таблиц из метаданных SQLAlchemy."""
        return sorted(Base.metadata.tables.keys())
    
    async def _get_table_data(self, session: AsyncSession, table_name: str) -> List[Dict[str, Any]]:
        """Получить все данные из таблицы."""
        table = Base.metadata.tables.get(table_name)
        if table is None:
            return []
        
        query = select(table)
        result = await session.execute(query)
        rows = result.fetchall()
        
        # Преобразуем строки в словари
        data = []
        for row in rows:
            row_dict = {}
            for key, value in row._mapping.items():
                # Сериализуем специальные типы
                if hasattr(value, 'isoformat'):
                    row_dict[key] = value.isoformat()
                elif isinstance(value, UUID):
                    row_dict[key] = str(value)
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
            raise HTTPException(status_code=500, detail=f"Ошибка при создании бэкапа: {str(e)}")
    
    def _get_table_insert_order(self) -> List[str]:
        """
        Получить порядок вставки таблиц на основе внешних ключей.
        Таблицы без FK идут первыми, затем с зависимостями.
        """
        # Порядок определён на основе анализа внешних ключей в models.py
        # Таблицы без внешних ключей или с минимальными зависимостями идут первыми
        return [
            # Базовые справочники (без FK)
            "teacher_category",
            "buildings",
            "payment_forms",
            "session_type",
            "users",
            
            # Преподаватели и здания
            "teachers",
            "teachers_buildings",
            
            # Специальности и группы
            "specialties",
            "groups",
            
            # Потоки
            "streams",
            
            # Учебные планы и связанные таблицы
            "semesters",
            "modules",
            "cycles",
            "chapters",
            "subjects_in_cycles",
            "plans",
            
            # Часы и назначения
            "subjects_in_cycles_hours",
            "certifications",
            "teachers_in_plans",
            
            # Сессии
            "sessions",
            
            # Расписание
            "schedule"
        ]

    async def restore_backup(self, session: AsyncSession, file_content: bytes) -> Dict[str, Any]:
        """Восстановить базу данных из JSON файла."""
        try:
            backup_data = json.loads(file_content.decode('utf-8'))

            if "tables" not in backup_data:
                raise HTTPException(status_code=400, detail="Неверный формат файла бэкапа")

            # Получаем правильный порядок вставки
            ordered_tables = self._get_table_insert_order()
            
            # Фильтруем только те таблицы, что есть в бэкапе
            backup_tables = set(backup_data["tables"].keys())
            tables_to_restore = [t for t in ordered_tables if t in backup_tables]
            
            # Добавляем таблицы, которых нет в порядке (на всякий случай)
            for table_name in backup_tables:
                if table_name not in tables_to_restore:
                    tables_to_restore.append(table_name)

            # Этап 1: Очищаем все таблицы через TRUNCATE CASCADE
            for table_name in tables_to_restore:
                table = Base.metadata.tables.get(table_name)
                if table is not None:
                    await session.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))

            # Этап 2: Вставляем данные в правильном порядке
            tables_restored = []
            for table_name in tables_to_restore:
                table = Base.metadata.tables.get(table_name)
                if table is None:
                    continue

                data = backup_data["tables"][table_name]
                if not data:
                    tables_restored.append(table_name)
                    continue

                # Вставляем новые данные
                for row in data:
                    clean_row = {k: v for k, v in row.items()}
                    if clean_row:
                        await session.execute(insert(table).values(clean_row))

                tables_restored.append(table_name)

            # Этап 3: Сбрасываем последовательности (sequences)
            # Это нужно, чтобы при создании новых записей не было конфликтов ID
            for table_name in tables_to_restore:
                table = Base.metadata.tables.get(table_name)
                if table is not None:
                    # Сбрасываем sequence для каждой таблицы с autoincrement ID
                    try:
                        await session.execute(text(f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), COALESCE((SELECT MAX(id) FROM {table_name}), 1), true)"))
                    except Exception:
                        # Если в таблице нет sequence или нет колонки id - пропускаем
                        pass

            # Коммитим транзакцию
            await session.commit()

            return {
                "message": "База данных успешно восстановлена",
                "tables_restored": tables_restored,
                "tables_count": len(tables_restored)
            }

        except json.JSONDecodeError:
            await session.rollback()
            raise HTTPException(status_code=400, detail="Неверный формат JSON файла")
        except Exception as e:
            await session.rollback()
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
