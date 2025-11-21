from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import SubjectsInCycle
from config.decorators import log_exceptions


class SubjectsInCycleDAL:
    """Data Access Layer for operating subjects in cycle info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_subject_in_cycle(self, code: str, title: str, cycle_in_chapter_id: int, module_in_cycle_id: int | None = None) -> SubjectsInCycle:
        new_subject_in_cycle = SubjectsInCycle(
            code=code,
            title=title,
            cycle_in_chapter_id=cycle_in_chapter_id,
            module_in_cycle_id=module_in_cycle_id
        )
        self.db_session.add(new_subject_in_cycle)
        await self.db_session.flush()
        return new_subject_in_cycle

    @log_exceptions
    async def delete_subject_in_cycle(self, id: int) -> SubjectsInCycle | None:
        query = delete(SubjectsInCycle).where(SubjectsInCycle.id == id).returning(SubjectsInCycle)
        res = await self.db_session.execute(query)
        deleted_subject_in_cycle = res.scalar_one_or_none()
        return deleted_subject_in_cycle

    @log_exceptions
    async def get_all_subjects_in_cycles(self, page: int, limit: int) -> list[SubjectsInCycle]:
        if page == 0:
            query = select(SubjectsInCycle).order_by(SubjectsInCycle.id.asc())
        else:
            query = select(SubjectsInCycle).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        subjects_in_cycles = list(result.scalars().all())
        return subjects_in_cycles

    @log_exceptions
    async def get_subject_in_cycle_by_id(self, id: int) -> SubjectsInCycle | None:
        query = select(SubjectsInCycle).where(SubjectsInCycle.id == id)
        res = await self.db_session.execute(query)
        subject_in_cycle_row = res.scalar_one_or_none()
        return subject_in_cycle_row

    @log_exceptions
    async def get_subjects_in_cycle_by_cycle(self, cycle_in_chapter_id: int, page: int, limit: int) -> list[SubjectsInCycle]:
        if page == 0:
            query = select(SubjectsInCycle).where(SubjectsInCycle.cycle_in_chapter_id == cycle_in_chapter_id).order_by(SubjectsInCycle.id.asc())
        else:
            query = select(SubjectsInCycle).where(SubjectsInCycle.cycle_in_chapter_id == cycle_in_chapter_id).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        subjects_in_cycles = list(result.scalars().all())
        return subjects_in_cycles

    @log_exceptions
    async def get_subjects_in_cycle_by_module(self, module_in_cycle_id: int, page: int, limit: int) -> list[SubjectsInCycle]:
        if page == 0:
            query = select(SubjectsInCycle).where(SubjectsInCycle.module_in_cycle_id == module_in_cycle_id).order_by(SubjectsInCycle.id.asc())
        else:
            query = select(SubjectsInCycle).where(SubjectsInCycle.module_in_cycle_id == module_in_cycle_id).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        subjects_in_cycles = list(result.scalars().all())
        return subjects_in_cycles
    
    @log_exceptions
    async def get_subjects_in_cycle_by_ids(self, ids: list[int], page: int, limit: int) -> list[SubjectsInCycle]:
        query = select(SubjectsInCycle).where(SubjectsInCycle.id.in_(ids))

        if page > 0:
            offset_value = (page - 1) * limit
            query = query.offset(offset_value).limit(limit)

        result = await self.db_session.execute(query)
        subjects_in_cycle = list(result.scalars().all())
        return subjects_in_cycle if subjects_in_cycle is not None else []

    @log_exceptions
    async def update_subject_in_cycle(self, target_id: int, **kwargs) -> SubjectsInCycle | None:
        query = update(SubjectsInCycle).where(SubjectsInCycle.id == target_id).values(**kwargs).returning(SubjectsInCycle)
        res = await self.db_session.execute(query)
        updated_subject_in_cycle = res.scalar_one_or_none()
        return updated_subject_in_cycle