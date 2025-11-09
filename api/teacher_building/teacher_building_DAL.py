from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import TeacherBuilding
from config.decorators import log_exceptions


class TeacherBuildingDAL:
    """Data Access Layer for operating teacher-building relation info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_teacher_building(self, teacher_id: int, building_number: int) -> TeacherBuilding:
        new_teacher_building = TeacherBuilding(
            teacher_id=teacher_id,
            building_number=building_number
        )
        self.db_session.add(new_teacher_building)
        await self.db_session.flush()
        return new_teacher_building

    @log_exceptions
    async def delete_teacher_building(self, id: int) -> TeacherBuilding | None:
        query = delete(TeacherBuilding).where(TeacherBuilding.id == id).returning(TeacherBuilding)
        res = await self.db_session.execute(query)
        deleted_teacher_building = res.scalar_one_or_none()
        return deleted_teacher_building

    @log_exceptions
    async def get_all_teachers_buildings(self, page: int, limit: int) -> list[TeacherBuilding]:
        if page == 0:
            query = select(TeacherBuilding).order_by(TeacherBuilding.id.asc())
        else:
            query = select(TeacherBuilding).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        teachers_buildings = list(result.scalars().all())
        return teachers_buildings

    @log_exceptions
    async def get_teacher_building_by_id(self, id: int) -> TeacherBuilding | None:
        query = select(TeacherBuilding).where(TeacherBuilding.id == id)
        res = await self.db_session.execute(query)
        teacher_building_row = res.scalar_one_or_none()
        return teacher_building_row

    @log_exceptions
    async def get_teachers_buildings_by_teacher(self, teacher_id: int, page: int, limit: int) -> list[TeacherBuilding]:
        if page == 0:
            query = select(TeacherBuilding).where(TeacherBuilding.teacher_id == teacher_id).order_by(TeacherBuilding.id.asc())
        else:
            query = select(TeacherBuilding).where(TeacherBuilding.teacher_id == teacher_id).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        teachers_buildings = list(result.scalars().all())
        return teachers_buildings if teachers_buildings is not None else []

    @log_exceptions
    async def get_teachers_buildings_by_building(self, building_number: int, page: int, limit: int) -> list[TeacherBuilding]:
        if page == 0:
            query = select(TeacherBuilding).where(TeacherBuilding.building_number == building_number).order_by(TeacherBuilding.id.asc())
        else:
            query = select(TeacherBuilding).where(TeacherBuilding.building_number == building_number).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        teachers_buildings = list(result.scalars().all())
        return teachers_buildings if teachers_buildings is not None else []

    @log_exceptions
    async def update_teacher_building(self, target_id: int, **kwargs) -> TeacherBuilding | None:
        query = update(TeacherBuilding).where(TeacherBuilding.id == target_id).values(**kwargs).returning(TeacherBuilding)
        res = await self.db_session.execute(query)
        updated_teacher_building = res.scalar_one_or_none()
        return updated_teacher_building
