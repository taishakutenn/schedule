"""Pydantic модели для backup/restore API"""

from api.models import TunedModel
from typing import List, Dict, Any


class BackupResponse(TunedModel):
    """Ответ при создании бэкапа"""
    message: str
    filename: str
    path: str
    tables_count: int
    timestamp: str


class RestoreResponse(TunedModel):
    """Ответ при восстановлении из бэкапа"""
    message: str
    tables_restored: List[str]
    tables_count: int


class BackupListResponse(TunedModel):
    """Список доступных бэкапов"""
    backups: List[str]
    count: int
