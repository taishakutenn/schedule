from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Plan
from config.decorators import log_exceptions


class PlanDAL:
    """Data Access Layer for operating plan info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_plan(self, year: int, speciality_code: str) -> Plan:
        new_plan = Plan(
            year=year,
            speciality_code=speciality_code
        )
        self.db_session.add(new_plan)
        await self.db_session.flush()
        return new_plan

    @log_exceptions
    async def delete_plan(self, id: int) -> Plan | None:
        query = delete(Plan).where(Plan.id == id).returning(Plan)
        res = await self.db_session.execute(query)
        deleted_plan = res.scalar_one_or_none()
        return deleted_plan

    @log_exceptions
    async def get_all_plans(self, page: int, limit: int) -> list[Plan]:
        if page == 0:
            query = select(Plan).order_by(Plan.id.asc())
        else:
            query = select(Plan).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        plans = list(result.scalars().all())
        return plans

    @log_exceptions
    async def get_plan_by_year_and_speciality(self, year: int, speciality_code: str) -> Plan | None:
        query = select(Plan).where((Plan.year == year) & (Plan.speciality_code == speciality_code))
        res = await self.db_session.execute(query)
        plan_row = res.scalar_one_or_none()
        return plan_row

    @log_exceptions
    async def get_plan_by_id(self, id: int) -> Plan | None:
        query = select(Plan).where(Plan.id == id)
        res = await self.db_session.execute(query)
        plan_row = res.scalar_one_or_none()
        return plan_row

    @log_exceptions
    async def update_plan(self, target_id: int, **kwargs) -> Plan | None:
        query = update(Plan).where(Plan.id == target_id).values(**kwargs).returning(Plan)
        res = await self.db_session.execute(query)
        updated_plan = res.scalar_one_or_none()
        return updated_plan
    