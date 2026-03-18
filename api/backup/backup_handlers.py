"""
API endpoints для бэкапа и восстановления базы данных.
"""

from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from api.backup.backup_services import BackupService
from api.backup.backup_pydantic import BackupResponse, RestoreResponse, BackupListResponse

backup_router = APIRouter(prefix="/db", tags=["database"])

backup_service = BackupService()


@backup_router.get("/backup", response_model=BackupResponse)
async def backup_database(session: AsyncSession = Depends(get_db)):
    """
    Экспорт всей базы данных в JSON файл.
    Возвращает информацию о созданном файле.
    """
    return await backup_service.create_backup(session)


@backup_router.post("/restore", response_model=RestoreResponse)
async def restore_database(
    file: UploadFile = File(..., description="JSON файл с бэкапом базы данных"),
    session: AsyncSession = Depends(get_db)
):
    """
    Восстановление базы данных из JSON файла.
    Внимание: Все существующие данные будут удалены!
    """
    content = await file.read()
    return await backup_service.restore_backup(session, content)


@backup_router.get("/backup/list", response_model=BackupListResponse)
async def list_backups():
    """Получить список доступных файлов бэкапа."""
    return await backup_service.list_backups()


@backup_router.get("/backup/download/{filename}")
async def download_backup(filename: str):
    """Скачать файл бэкапа."""
    backup_path = backup_service.get_backup_path(filename)
    
    return FileResponse(
        path=str(backup_path),
        filename=filename,
        media_type="application/json"
    )
