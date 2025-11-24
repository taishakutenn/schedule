from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import SessionType
from config.decorators import log_exceptions


class SessionTypeDAL:
    """Data Access Layer for operating session type info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_session_type(self, name: str) -> SessionType:
        new_type = SessionType(
            name=name
        )
        self.db_session.add(new_type)
        await self.db_session.flush()
        return new_type

    @log_exceptions
    async def delete_session_type(self, name: str) -> SessionType | None:
        query = delete(SessionType).where(SessionType.name == name).returning(SessionType)
        res = await self.db_session.execute(query)
        deleted_type = res.scalar_one_or_none()
        return deleted_type

    @log_exceptions
    async def get_all_session_types(self, page: int, limit: int) -> list[SessionType]:
        if page == 0:
            query = select(SessionType).order_by(SessionType.name.asc())
        else:
            query = select(SessionType).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        types = list(result.scalars().all())
        return types

    @log_exceptions
    async def get_session_type(self, name: str) -> SessionType | None:
        query = select(SessionType).where(SessionType.name == name)
        res = await self.db_session.execute(query)
        type_row = res.scalar_one_or_none()
        return type_row

    @log_exceptions
    async def update_session_type(self, tg_name: str, **kwargs) -> SessionType | None:
        query = update(SessionType).where(SessionType.name == tg_name).values(**kwargs).returning(SessionType)
        res = await self.db_session.execute(query)
        updated_type = res.scalar_one_or_none()
        return updated_type