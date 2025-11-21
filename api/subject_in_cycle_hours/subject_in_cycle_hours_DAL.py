from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import SubjectsInCycleHours
from config.decorators import log_exceptions


class SubjectsInCycleHoursDAL:
    """Data Access Layer for operating subjects in cycle hours info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_subject_in_cycle_hours(
        self,
        semester: int,
        self_study_hours: int,
        lectures_hours: int,
        laboratory_hours: int,
        practical_hours: int,
        course_project_hours: int,
        consultation_hours: int,
        intermediate_assessment_hours: int,
        subject_in_cycle_id: int
    ) -> SubjectsInCycleHours:
        new_subject_in_cycle_hours = SubjectsInCycleHours(
            semester=semester,
            self_study_hours=self_study_hours,
            lectures_hours=lectures_hours,
            laboratory_hours=laboratory_hours,
            practical_hours=practical_hours,
            course_project_hours=course_project_hours,
            consultation_hours=consultation_hours,
            intermediate_assessment_hours=intermediate_assessment_hours,
            subject_in_cycle_id=subject_in_cycle_id
        )
        self.db_session.add(new_subject_in_cycle_hours)
        await self.db_session.flush()
        return new_subject_in_cycle_hours

    @log_exceptions
    async def delete_subject_in_cycle_hours(self, id: int) -> SubjectsInCycleHours | None:
        query = delete(SubjectsInCycleHours).where(SubjectsInCycleHours.id == id).returning(SubjectsInCycleHours)
        res = await self.db_session.execute(query)
        deleted_subject_in_cycle_hours = res.scalar_one_or_none()
        return deleted_subject_in_cycle_hours

    @log_exceptions
    async def get_all_subjects_in_cycle_hours(self, page: int, limit: int) -> list[SubjectsInCycleHours]:
        if page == 0:
            query = select(SubjectsInCycleHours).order_by(SubjectsInCycleHours.id.asc())
        else:
            query = select(SubjectsInCycleHours).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        subjects_in_cycle_hours = list(result.scalars().all())
        return subjects_in_cycle_hours

    @log_exceptions
    async def get_subject_in_cycle_hours_by_id(self, id: int) -> SubjectsInCycleHours | None:
        query = select(SubjectsInCycleHours).where(SubjectsInCycleHours.id == id)
        res = await self.db_session.execute(query)
        subject_in_cycle_hours_row = res.scalar_one_or_none()
        return subject_in_cycle_hours_row

    @log_exceptions
    async def get_subjects_in_cycle_hours_by_subject_in_cycle(self, subject_in_cycle_id: int, page: int, limit: int) -> list[SubjectsInCycleHours]:
        if page == 0:
            query = select(SubjectsInCycleHours).where(SubjectsInCycleHours.subject_in_cycle_id == subject_in_cycle_id).order_by(SubjectsInCycleHours.semester.asc(), SubjectsInCycleHours.id.asc())
        else:
            query = select(SubjectsInCycleHours).where(SubjectsInCycleHours.subject_in_cycle_id == subject_in_cycle_id).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        subjects_in_cycle_hours = list(result.scalars().all())
        return subjects_in_cycle_hours if subjects_in_cycle_hours is not None else []
    
    @log_exceptions
    async def get_subjects_in_cycle_hours_by_subject_and_semester(self, subject_in_cycle_id: int, semester: int) -> list[SubjectsInCycleHours]:
        query = select(SubjectsInCycleHours).where(
            (SubjectsInCycleHours.subject_in_cycle_id == subject_in_cycle_id) &
            (SubjectsInCycleHours.semester == semester)
        ).order_by(SubjectsInCycleHours.id.asc())
        result = await self.db_session.execute(query)
        subjects_in_cycle_hours = list(result.scalars().all())
        return subjects_in_cycle_hours if subjects_in_cycle_hours is not None else []

    @log_exceptions
    async def get_subjects_in_cycle_hours_by_semester(self, semester: int, page: int, limit: int) -> list[SubjectsInCycleHours]:
        if page == 0:
            query = select(SubjectsInCycleHours).where(SubjectsInCycleHours.semester == semester).order_by(SubjectsInCycleHours.id.asc())
        else:
            query = select(SubjectsInCycleHours).where(SubjectsInCycleHours.semester == semester).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        subjects_in_cycle_hours = list(result.scalars().all())
        return subjects_in_cycle_hours
    
    @log_exceptions
    async def get_subjects_hours_by_ids(self, ids: list[int], page: int, limit: int) -> list[SubjectsInCycleHours]:
        query = select(SubjectsInCycleHours).where(SubjectsInCycleHours.id.in_(ids))

        if page > 0:
            offset_value = (page - 1) * limit
            query = query.offset(offset_value).limit(limit)

        result = await self.db_session.execute(query)
        subjects_in_cycle_hours = list(result.scalars().all())
        return subjects_in_cycle_hours if subjects_in_cycle_hours is not None else []
# ...

    @log_exceptions
    async def update_subject_in_cycle_hours(self, target_id: int, **kwargs) -> SubjectsInCycleHours | None:
        query = update(SubjectsInCycleHours).where(SubjectsInCycleHours.id == target_id).values(**kwargs).returning(SubjectsInCycleHours)
        res = await self.db_session.execute(query)
        updated_subject_in_cycle_hours = res.scalar_one_or_none()
        return updated_subject_in_cycle_hours