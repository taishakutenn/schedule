from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Module
from config.decorators import log_exceptions


class ModuleDAL:
    """Data Access Layer for operating module info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_module(self, name: str, code: str, cycle_in_chapter_id: int) -> Module:
        new_module = Module(
            name=name,
            code=code,
            cycle_in_chapter_id=cycle_in_chapter_id
        )
        self.db_session.add(new_module)
        await self.db_session.flush()
        return new_module

    @log_exceptions
    async def delete_module(self, id: int) -> Module | None:
        query = delete(Module).where(Module.id == id).returning(Module)
        res = await self.db_session.execute(query)
        deleted_module = res.scalar_one_or_none()
        return deleted_module

    @log_exceptions
    async def get_all_modules(self, page: int, limit: int) -> list[Module]:
        if page == 0:
            query = select(Module).order_by(Module.id.asc())
        else:
            query = select(Module).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        modules = list(result.scalars().all())
        return modules

    @log_exceptions
    async def get_module_by_id(self, id: int) -> Module | None:
        query = select(Module).where(Module.id == id)
        res = await self.db_session.execute(query)
        module_row = res.scalar_one_or_none()
        return module_row

    @log_exceptions
    async def get_modules_by_cycle(self, cycle_in_chapter_id: int, page: int, limit: int) -> list[Module]:
        if page == 0:
            query = select(Module).where(Module.cycle_in_chapter_id == cycle_in_chapter_id).order_by(Module.id.asc())
        else:
            query = select(Module).where(Module.cycle_in_chapter_id == cycle_in_chapter_id).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        modules = list(result.scalars().all())
        return modules

    @log_exceptions
    async def update_module(self, target_id: int, **kwargs) -> Module | None:
        query = update(Module).where(Module.id == target_id).values(**kwargs).returning(Module)
        res = await self.db_session.execute(query)
        updated_module = res.scalar_one_or_none()
        return updated_module
    