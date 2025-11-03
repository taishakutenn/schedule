from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Cabinet
from config.decorators import log_exceptions


class CabinetDAL:
    """Data Access Layer for operating cabinet info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_cabinet(self, cabinet_number: int, building_number: int, capacity: int = None, cabinet_state: str = None) -> Cabinet:
        new_cabinet = Cabinet(
            cabinet_number=cabinet_number,
            building_number=building_number,
            capacity=capacity,
            cabinet_state=cabinet_state
        )
        self.db_session.add(new_cabinet)
        await self.db_session.flush()
        return new_cabinet

    @log_exceptions
    async def delete_cabinet(self, building_number: int, cabinet_number: int) -> Cabinet | None:
        query = delete(Cabinet).where((Cabinet.cabinet_number == cabinet_number) & (Cabinet.building_number == building_number)).returning(Cabinet)
        res = await self.db_session.execute(query)
        deleted_cabinet = res.scalar_one_or_none()
        return deleted_cabinet

    @log_exceptions
    async def get_all_cabinets(self, page: int, limit: int) -> list[Cabinet]:
        if page == 0:
            query = select(Cabinet).order_by(Cabinet.cabinet_number.asc())
        else:
            query = select(Cabinet).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        cabinets = list(result.scalars().all())
        return cabinets

    @log_exceptions
    async def get_cabinets_by_building(self, building_number: int, page: int, limit: int) -> list[Cabinet]:
        if page == 0:
            query = select(Cabinet).where(Cabinet.building_number == building_number).order_by(
                Cabinet.cabinet_number.asc())
        else:
            query = select(Cabinet).where(Cabinet.building_number == building_number).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        cabinets = list(result.scalars().all())
        return cabinets

    @log_exceptions
    async def get_cabinet_by_number_and_building(self, building_number: int, cabinet_number: int) -> Cabinet | None:
        query = select(Cabinet).where((Cabinet.cabinet_number == cabinet_number) &
                                      (Cabinet.building_number == building_number))
        res = await self.db_session.execute(query)
        cabinet_row = res.scalar_one_or_none()
        return cabinet_row

    @log_exceptions
    async def update_cabinet(self, search_building_number: int, search_cabinet_number: int, **kwargs) -> Cabinet | None:
        """
        We use that names for the variables we are searching for because
        in **kwargs there are already variables with names: building_number and cabinet_number
        """
        query = update(Cabinet).where(
            (Cabinet.cabinet_number == search_cabinet_number) & (Cabinet.building_number == search_building_number)).values(**kwargs).returning(Cabinet)
        res = await self.db_session.execute(query)
        return res.scalar_one_or_none()
