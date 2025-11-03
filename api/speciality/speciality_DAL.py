from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Speciality
from config.decorators import log_exceptions


class SpecialityDAL:
    """Data Access Layer for operating speciality info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_speciality(self, speciality_code: str) -> Speciality:
        new_speciality = Speciality(
            speciality_code=speciality_code
        )
        self.db_session.add(new_speciality)
        await self.db_session.flush()
        return new_speciality

    @log_exceptions
    async def delete_speciality(self, speciality_code: str) -> Speciality | None:
        query = delete(Speciality).where(Speciality.speciality_code == speciality_code).returning(Speciality)
        res = await self.db_session.execute(query)
        deleted_speciality = res.scalar_one_or_none()
        return deleted_speciality

    @log_exceptions
    async def get_all_specialities(self, page: int, limit: int) -> list[Speciality]:
        if page == 0:
            query = select(Speciality).order_by(Speciality.speciality_code.asc())
        else:
            query = select(Speciality).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        specialities = list(result.scalars().all())
        return specialities

    @log_exceptions
    async def get_speciality(self, speciality_code: str) -> Speciality | None:
        query = select(Speciality).where(Speciality.speciality_code == speciality_code)
        res = await self.db_session.execute(query)
        speciality_row = res.scalar_one_or_none()
        return speciality_row

    @log_exceptions
    async def update_speciality(self, target_code: str, **kwargs) -> Speciality | None:
        query = update(Speciality).where(Speciality.speciality_code == target_code).values(**kwargs).returning(Speciality)
        res = await self.db_session.execute(query)
        updated_speciality = res.scalar_one_or_none()
        return updated_speciality
    