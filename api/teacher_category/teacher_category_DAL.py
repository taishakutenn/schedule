from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import TeacherCategory
from config.decorators import log_exceptions


class TeacherCategoryDAL:
    """Data Access Layer for operating teacher category info"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_teacher_category(
            self, teacher_category: str
    ) -> TeacherCategory:
        new_category = TeacherCategory(
            teacher_category=teacher_category
        )
        self.db_session.add(new_category)
        await self.db_session.flush()
        return new_category

    @log_exceptions
    async def delete_teacher_category(self, teacher_category: str) -> TeacherCategory | None:
        query = delete(TeacherCategory).where(TeacherCategory.teacher_category == teacher_category).returning(
            TeacherCategory)
        res = await self.db_session.execute(query)
        deleted_category = res.scalar_one_or_none()
        return deleted_category

    @log_exceptions
    async def get_all_teacher_categories(self, page: int, limit: int) -> list[TeacherCategory]:
        if page == 0:
            query = select(TeacherCategory).order_by(TeacherCategory.teacher_category.asc())
        else:
            query = select(TeacherCategory).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        categories = list(result.scalars().all())
        return categories

    @log_exceptions
    async def get_teacher_category(self, teacher_category: str) -> TeacherCategory | None:
        query = select(TeacherCategory).where(TeacherCategory.teacher_category == teacher_category)
        res = await self.db_session.execute(query)
        return res.scalar_one_or_none()

    @log_exceptions
    async def update_teacher_category(self, target_category: str, **kwargs) -> TeacherCategory | None:
        query = (
            update(TeacherCategory)
            .where(TeacherCategory.teacher_category == target_category)
            .values(**kwargs)
            .returning(TeacherCategory)
        )
        res = await self.db_session.execute(query)
        return res.scalar_one_or_none()
