from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Chapter
from config.decorators import log_exceptions


class ChapterDAL:
    """Data Access Layer for operating chapter info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_chapter(self, code: str, name: str, plan_id: int) -> Chapter:
        new_chapter = Chapter(
            code=code,
            name=name,
            plan_id=plan_id
        )
        self.db_session.add(new_chapter)
        await self.db_session.flush()
        return new_chapter

    @log_exceptions
    async def delete_chapter(self, id: int) -> Chapter | None:
        query = delete(Chapter).where(Chapter.id == id).returning(Chapter)
        res = await self.db_session.execute(query)
        deleted_chapter = res.scalar_one_or_none()
        return deleted_chapter

    @log_exceptions
    async def get_all_chapters(self, page: int, limit: int) -> list[Chapter]:
        if page == 0:
            query = select(Chapter).order_by(Chapter.id.asc())
        else:
            query = select(Chapter).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        chapters = list(result.scalars().all())
        return chapters

    @log_exceptions
    async def get_chapter_by_id(self, id: int) -> Chapter | None:
        query = select(Chapter).where(Chapter.id == id)
        res = await self.db_session.execute(query)
        chapter_row = res.scalar_one_or_none()
        return chapter_row

    @log_exceptions
    async def get_chapters_by_plan(self, plan_id: int, page: int, limit: int) -> list[Chapter]:
        if page == 0:
            query = select(Chapter).where(Chapter.plan_id == plan_id).order_by(Chapter.id.asc())
        else:
            query = select(Chapter).where(Chapter.plan_id == plan_id).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        chapters = list(result.scalars().all())
        return chapters

    @log_exceptions
    async def update_chapter(self, target_id: int, **kwargs) -> Chapter | None:
        query = update(Chapter).where(Chapter.id == target_id).values(**kwargs).returning(Chapter)
        res = await self.db_session.execute(query)
        updated_chapter = res.scalar_one_or_none()
        return updated_chapter
    