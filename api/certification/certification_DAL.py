from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Certification
from config.decorators import log_exceptions


class CertificationDAL:
    """Data Access Layer for operating certification info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_certification(
        self,
        id: int,
        credit: bool = False,
        differentiated_credit: bool = False,
        course_project: bool = False,
        course_work: bool = False,
        control_work: bool = False,
        other_form: bool = False
    ) -> Certification:
        new_certification = Certification(
            id=id,
            credit=credit,
            differentiated_credit=differentiated_credit,
            course_project=course_project,
            course_work=course_work,
            control_work=control_work,
            other_form=other_form
        )
        self.db_session.add(new_certification)
        await self.db_session.flush()
        return new_certification

    @log_exceptions
    async def delete_certification(self, id: int) -> Certification | None:
        query = delete(Certification).where(Certification.id == id).returning(Certification)
        res = await self.db_session.execute(query)
        deleted_certification = res.scalar_one_or_none()
        return deleted_certification

    @log_exceptions
    async def get_all_certifications(self, page: int, limit: int) -> list[Certification]:
        if page == 0:
            query = select(Certification).order_by(Certification.id.asc())
        else:
            query = select(Certification).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        certifications = list(result.scalars().all())
        return certifications

    @log_exceptions
    async def get_certification_by_id(self, id: int) -> Certification | None:
        query = select(Certification).where(Certification.id == id)
        res = await self.db_session.execute(query)
        certification_row = res.scalar_one_or_none()
        return certification_row
    
    @log_exceptions
    async def get_certifications_by_ids(self, ids: list[int], page: int, limit: int) -> list[Certification]:
        query = select(Certification).where(Certification.id.in_(ids))
        if page > 0:
            offset_value = (page - 1) * limit
            query = query.offset(offset_value).limit(limit)
        result = await self.db_session.execute(query)
        certifications = list(result.scalars().all())
        return certifications if certifications is not None else []

    @log_exceptions
    async def update_certification(self, target_id: int, **kwargs) -> Certification | None:
        query = update(Certification).where(Certification.id == target_id).values(**kwargs).returning(Certification)
        res = await self.db_session.execute(query)
        updated_certification = res.scalar_one_or_none()
        return updated_certification
