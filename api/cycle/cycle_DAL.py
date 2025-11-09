from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Cycle
from config.decorators import log_exceptions


class CycleDAL:
    """Data Access Layer for operating cycle info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_cycle(self, contains_modules: bool, code: str, name: str, chapter_in_plan_id: int) -> Cycle:
        new_cycle = Cycle(
            contains_modules=contains_modules,
            code=code,
            name=name,
            chapter_in_plan_id=chapter_in_plan_id
        )
        self.db_session.add(new_cycle)
        await self.db_session.flush()
        return new_cycle

    @log_exceptions
    async def delete_cycle(self, id: int) -> Cycle | None:
        query = delete(Cycle).where(Cycle.id == id).returning(Cycle)
        res = await self.db_session.execute(query)
        deleted_cycle = res.scalar_one_or_none()
        return deleted_cycle

    @log_exceptions
    async def get_all_cycles(self, page: int, limit: int) -> list[Cycle]:
        if page == 0:
            query = select(Cycle).order_by(Cycle.id.asc())
        else:
            query = select(Cycle).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        cycles = list(result.scalars().all())
        return cycles

    @log_exceptions
    async def get_cycle_by_id(self, id: int) -> Cycle | None:
        query = select(Cycle).where(Cycle.id == id)
        res = await self.db_session.execute(query)
        cycle_row = res.scalar_one_or_none()
        return cycle_row

    @log_exceptions
    async def get_cycles_by_chapter(self, chapter_in_plan_id: int, page: int, limit: int) -> list[Cycle]:
        if page == 0:
            query = select(Cycle).where(Cycle.chapter_in_plan_id == chapter_in_plan_id).order_by(Cycle.id.asc())
        else:
            query = select(Cycle).where(Cycle.chapter_in_plan_id == chapter_in_plan_id).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        cycles = list(result.scalars().all())
        return cycles

    @log_exceptions
    async def update_cycle(self, target_id: int, **kwargs) -> Cycle | None:
        query = update(Cycle).where(Cycle.id == target_id).values(**kwargs).returning(Cycle)
        res = await self.db_session.execute(query)
        updated_cycle = res.scalar_one_or_none()
        return updated_cycle
    