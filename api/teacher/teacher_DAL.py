from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Teacher
from config.decorators import log_exceptions


class TeacherDAL:
    """Data Access Layer for operating teacher info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_teacher(
            self, name: str, surname: str, phone_number: str, email: str = None, fathername: str = None, salary_rate: float = None, teacher_category: str = None
    ) -> Teacher:
        new_teacher = Teacher(
            name=name,
            surname=surname,
            phone_number=phone_number,
            email=email,
            fathername=fathername,
            salary_rate=salary_rate,
            teacher_category=teacher_category
        )
        self.db_session.add(new_teacher)
        await self.db_session.flush()
        return new_teacher

    @log_exceptions
    async def delete_teacher(self, id: int) -> Teacher | None:
        query_select = select(Teacher).where(Teacher.id == id)
        res = await self.db_session.execute(query_select)
        teacher = res.scalar_one_or_none()
        if teacher:
            await self.db_session.execute(delete(Teacher).where(Teacher.id == id))
            await self.db_session.flush()
        return teacher

    @log_exceptions
    async def get_all_teachers(self, page: int, limit: int) -> list[Teacher]:
        query = select(Teacher).order_by(Teacher.id.asc())
        if page > 0:
            query = query.offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    @log_exceptions
    async def get_teacher_by_id(self, id: int) -> Teacher | None:
        query = select(Teacher).where(Teacher.id == id)
        res = await self.db_session.execute(query)
        return res.scalar_one_or_none()

    @log_exceptions
    async def get_teacher_by_name_surname(self, name: str, surname: str) -> Teacher | None:
        result = await self.db_session.execute(select(Teacher).where((Teacher.name == name) & (Teacher.surname == surname)))
        return result.scalar_one_or_none()

    @log_exceptions
    async def update_teacher(self, id: int, **kwargs) -> Teacher | None:
        result = await self.db_session.execute(update(Teacher).where(Teacher.id == id).values(**kwargs).returning(Teacher))
        updated_teacher = result.scalar_one_or_none()
        if updated_teacher:
            await self.db_session.flush()
        return updated_teacher

    @log_exceptions
    async def get_teacher_by_email(self, email: str) -> Teacher | None:
        query = select(Teacher).where(Teacher.email == email)
        res = await self.db_session.execute(query)
        return res.scalar_one_or_none()

    @log_exceptions
    async def get_teacher_by_phone_number(self, phone_number: str) -> Teacher | None:
        query = select(Teacher).where(Teacher.phone_number == phone_number)
        res = await self.db_session.execute(query)
        return res.scalar_one_or_none()

    @log_exceptions
    async def get_all_teachers_by_category(self, category: str, page: int, limit: int) -> list[Teacher]:
        query = select(Teacher).where(Teacher.teacher_category == category).order_by(Teacher.id.asc())
        if page > 0:
            query = query.offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        return list(result.scalars().all())
