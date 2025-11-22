from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import TeacherInPlan
from config.decorators import log_exceptions


class TeacherInPlanDAL:
    """Data Access Layer for operating teacher in plan info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_teacher_in_plan(self, subject_in_cycle_hours_id: int, teacher_id: int, group_name: str, session_type: str = None) -> TeacherInPlan:
        new_teacher_in_plan = TeacherInPlan(
            subject_in_cycle_hours_id=subject_in_cycle_hours_id,
            teacher_id=teacher_id,
            group_name=group_name,
            session_type=session_type
        )
        self.db_session.add(new_teacher_in_plan)
        await self.db_session.flush()
        return new_teacher_in_plan

    @log_exceptions
    async def delete_teacher_in_plan(self, id: int) -> TeacherInPlan | None:
        query = delete(TeacherInPlan).where(TeacherInPlan.id == id).returning(TeacherInPlan)
        res = await self.db_session.execute(query)
        deleted_teacher_in_plan = res.scalar_one_or_none()
        return deleted_teacher_in_plan

    @log_exceptions
    async def get_all_teachers_in_plans(self, page: int, limit: int) -> list[TeacherInPlan]:
        if page == 0:
            query = select(TeacherInPlan).order_by(TeacherInPlan.id.asc())
        else:
            query = select(TeacherInPlan).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        teachers_in_plans = list(result.scalars().all())
        return teachers_in_plans

    @log_exceptions
    async def get_teacher_in_plan_by_id(self, id: int) -> TeacherInPlan | None:
        query = select(TeacherInPlan).where(TeacherInPlan.id == id)
        res = await self.db_session.execute(query)
        teacher_in_plan_row = res.scalar_one_or_none()
        return teacher_in_plan_row

    @log_exceptions
    async def get_teacher_in_plan_by_group_and_subject_in_cycle_hours(
            self, group_name: str, subject_in_cycle_hours_id: int) -> TeacherInPlan | None:

        query = select(TeacherInPlan).where(
            (TeacherInPlan.group_name == group_name)
            & (TeacherInPlan.subject_in_cycle_hours_id == subject_in_cycle_hours_id)
        )
        res = await self.db_session.execute(query)
        teacher_in_plan_row = res.scalar_one_or_none()
        return teacher_in_plan_row

    @log_exceptions
    async def get_teachers_in_plans_by_teacher(self, teacher_id: int, page: int, limit: int) -> list[TeacherInPlan]:
        if page == 0:
            query = select(TeacherInPlan).where(TeacherInPlan.teacher_id == teacher_id).order_by(TeacherInPlan.id.asc())
        else:
            query = select(TeacherInPlan).where(TeacherInPlan.teacher_id == teacher_id).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        teachers_in_plans = list(result.scalars().all())
        return teachers_in_plans if teachers_in_plans is not None else []

    @log_exceptions
    async def get_teachers_in_plans_by_group(self, group_name: str, page: int, limit: int) -> list[TeacherInPlan]:
        if page == 0:
            query = select(TeacherInPlan).where(TeacherInPlan.group_name == group_name).order_by(TeacherInPlan.id.asc())
        else:
            query = select(TeacherInPlan).where(TeacherInPlan.group_name == group_name).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        teachers_in_plans = list(result.scalars().all())
        return teachers_in_plans if teachers_in_plans is not None else []

    @log_exceptions
    async def get_teachers_in_plans_by_subject_hours(self, subject_in_cycle_hours_id: int, page: int, limit: int) -> list[TeacherInPlan]:
        if page == 0:
            query = select(TeacherInPlan).where(TeacherInPlan.subject_in_cycle_hours_id == subject_in_cycle_hours_id).order_by(TeacherInPlan.id.asc())
        else:
            query = select(TeacherInPlan).where(TeacherInPlan.subject_in_cycle_hours_id == subject_in_cycle_hours_id).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        teachers_in_plans = list(result.scalars().all())
        return teachers_in_plans if teachers_in_plans is not None else []

    @log_exceptions
    async def get_teachers_in_plans_by_session_type(self, session_type: str, page: int, limit: int) -> list[TeacherInPlan]:
        if page == 0:
            query = select(TeacherInPlan).where(TeacherInPlan.session_type == session_type).order_by(TeacherInPlan.id.asc())
        else:
            query = select(TeacherInPlan).where(TeacherInPlan.session_type == session_type).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        teachers_in_plans = list(result.scalars().all())
        return teachers_in_plans if teachers_in_plans is not None else []

    @log_exceptions
    async def update_teacher_in_plan(self, target_id: int, **kwargs) -> TeacherInPlan | None:
        query = update(TeacherInPlan).where(TeacherInPlan.id == target_id).values(**kwargs).returning(TeacherInPlan)
        res = await self.db_session.execute(query)
        updated_teacher_in_plan = res.scalar_one_or_none()
        return updated_teacher_in_plan
    
