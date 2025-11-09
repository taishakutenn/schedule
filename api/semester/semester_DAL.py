from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Semester
from config.decorators import log_exceptions


class SemesterDAL:
    """Data Access Layer for operating semester info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_semester(self, semester: int, weeks: float, practice_weeks: int, plan_id: int) -> Semester:
        new_semester = Semester(
            semester=semester,
            weeks=weeks,
            practice_weeks=practice_weeks,
            plan_id=plan_id
        )
        self.db_session.add(new_semester)
        await self.db_session.flush()
        return new_semester

    @log_exceptions
    async def delete_semester(self, semester: int, plan_id: int) -> Semester | None:
        query = delete(Semester).where((Semester.semester == semester) & (Semester.plan_id == plan_id)).returning(Semester)
        res = await self.db_session.execute(query)
        deleted_semester = res.scalar_one_or_none()
        return deleted_semester

    @log_exceptions
    async def get_all_semesters(self, page: int, limit: int) -> list[Semester]:
        if page == 0:
            query = select(Semester).order_by(Semester.semester.asc())
        else:
            query = select(Semester).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        semesters = list(result.scalars().all())
        return semesters

    @log_exceptions
    async def get_semester_by_semester_and_plan(self, semester: int, plan_id: int) -> Semester | None:
        query = select(Semester).where((Semester.semester == semester) & (Semester.plan_id == plan_id))
        res = await self.db_session.execute(query)
        semester_row = res.scalar_one_or_none()
        return semester_row

    @log_exceptions
    async def update_semester(self, target_semester: int, target_plan_id: int, **kwargs) -> Semester | None:
        query = update(Semester).where(
            (Semester.semester == target_semester) & (Semester.plan_id == target_plan_id)
        ).values(**kwargs).returning(Semester)
        res = await self.db_session.execute(query)
        updated_semester = res.scalar_one_or_none()
        return updated_semester
    