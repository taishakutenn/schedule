from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Group
from config.decorators import log_exceptions


class GroupDAL:
    """Data Access Layer for operating group info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_group(self, group_name: str, speciality_code: str = None, quantity_students: int = None, group_advisor_id: int = None) -> Group:
        new_group = Group(
            group_name=group_name,
            speciality_code=speciality_code,
            quantity_students=quantity_students,
            group_advisor_id=group_advisor_id
        )
        self.db_session.add(new_group)
        await self.db_session.flush()
        return new_group

    @log_exceptions
    async def delete_group(self, group_name: str) -> Group | None:
        query = delete(Group).where(Group.group_name == group_name).returning(Group)
        res = await self.db_session.execute(query)
        deleted_group = res.scalar_one_or_none()
        return deleted_group

    @log_exceptions
    async def get_all_groups(self, page: int, limit: int) -> list[Group]:
        if page == 0:
            query = select(Group).order_by(Group.group_name.asc())
        else:
            query = select(Group).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        groups = list(result.scalars().all())
        return groups

    @log_exceptions
    async def get_group_by_name(self, group_name: str) -> Group | None:
        query = select(Group).where(Group.group_name == group_name)
        res = await self.db_session.execute(query)
        group_row = res.scalar_one_or_none()
        return group_row

    @log_exceptions
    async def get_group_by_advisor_id(self, group_advisor_id: int) -> Group | None:
        query = select(Group).where(Group.group_advisor_id == group_advisor_id)
        res = await self.db_session.execute(query)
        group_row = res.scalar_one_or_none()
        return group_row
    
    @log_exceptions
    async def get_groups_by_speciality(self, speciality_code: str, page: int, limit: int) -> list[Group]:
        if page == 0:
            query = select(Group).where(Group.speciality_code == speciality_code).order_by(Group.group_name.asc())
        else:
            query = select(Group).where(Group.speciality_code == speciality_code).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        groups = list(result.scalars().all())
        return groups if groups is not None else []

    @log_exceptions
    async def update_group(self, target_group_name: str, **kwargs) -> Group | None:
        query = update(Group).where(Group.group_name == target_group_name).values(**kwargs).returning(Group)
        res = await self.db_session.execute(query)
        updated_group = res.scalar_one_or_none()
        return updated_group
    