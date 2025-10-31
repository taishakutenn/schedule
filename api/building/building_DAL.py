from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Building
from config.decorators import log_exceptions


class BuildingDAL:
    """Data Access Layer for operating building info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_building(
            self, building_number: int, city: str, building_address: str
    ) -> Building:
        new_building = Building(
            building_number=building_number,
            city=city,
            building_address=building_address
        )
        self.db_session.add(new_building)
        await self.db_session.flush()
        return new_building

    @log_exceptions
    async def delete_building(self, building_number: int) -> Building | None:
        query = delete(Building).where(Building.building_number == building_number).returning(Building)
        res = await self.db_session.execute(query)
        deleted_building = res.scalar_one_or_none()
        return deleted_building

    @log_exceptions
    async def get_all_buildings(self, page: int, limit: int) -> list[Building]:
        if page == 0:
            query = select(Building).order_by(Building.building_number.asc())
        else:
            query = select(Building).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    @log_exceptions
    async def get_building_by_number(self, building_number: int) -> Building | None:
        query = select(Building).where(Building.building_number == building_number)
        res = await self.db_session.execute(query)
        building_row = res.scalar_one_or_none()
        return building_row

    @log_exceptions
    async def get_building_by_address(self, building_address: str) -> Building | None:
        query = select(Building).where(Building.building_address == building_address)
        res = await self.db_session.execute(query)
        building_row = res.first()
        return building_row[0] if building_row is not None else None

    @log_exceptions
    async def update_building(self, target_number, **kwargs) -> Building | None:
        query = update(Building).where(Building.building_number == target_number).values(**kwargs).returning(Building)
        res = await self.db_session.execute(query)
        return res.scalar_one_or_none()
