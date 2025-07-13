"""
File for encapsulating business logic,
here classes are written for implementing crud operations for each table.
There is no need to do checks in the data,
because it is assumed that the data submitted here is already validated.
"""

from typing import Optional

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import ShowTeacher
from db.models import Teacher
from config.logging_config import configure_logging

# Создаём объект логгера
logger = configure_logging()


class TeacherDAL:
    """Data Access Layer for operating teacher info"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_teacher(
            self, name: str, surname: str, phone_number: str, email: str = None, fathername: str = None
    ) -> Teacher:
        new_teacher = Teacher(
            name=name,
            surname=surname,
            phone_number=phone_number,
            email=email,
            fathername=fathername
        )

        # Add teacher in session
        self.db_session.add(new_teacher)

        # Add changes to the database, but do not commit them strictly
        await self.db_session.flush()
        logger.info("Новый учитель успешно добавлен в бд")
        return new_teacher

    async def delete_teacher(self, id: int) -> ShowTeacher | None:
        # Сначала находим учителя по id
        query_select = select(Teacher).where(Teacher.id == id)
        res = await self.db_session.execute(query_select)
        teacher = res.scalar_one_or_none()

        if teacher is None:
            logger.warning(f"Не было найдено ни одного учителя с таким id: {id}")
            return None

        # Удаляем учителя
        query_delete = delete(Teacher).where(Teacher.id == id)
        await self.db_session.execute(query_delete)

        logger.info(f"Учитель с id {id} был успешно удалён из бд")

        return ShowTeacher(
            name=teacher.name,
            surname=teacher.surname,
            phone_number=teacher.phone_number,
            email=teacher.email,
            fathername=teacher.fathername
        )

    async def get_all_teachers(self, page: int, limit: int) -> list[ShowTeacher] | None:
        # Calculate first and end selection element.
        # Based on the received page and elements on it
        # If the page is zero - then select all elements

        if page == 0:
            query = select(Teacher).order_by(Teacher.surname.asc())
        else:
            query = (
                select(Teacher)
                .offset((page - 1) * limit)
                .limit(limit)
            )

        result = await self.db_session.execute(query)
        teachers = result.scalars().all()

        if teachers:
            logger.info(f"Найдено учителей: {len(teachers)}")
            return [
                ShowTeacher(
                    name=t.name,
                    surname=t.surname,
                    email=t.email,
                    phone_number=t.phone_number,
                    fathername=t.fathername
                ) for t in teachers
            ]
        else:
            logger.warning("Не было найдено ни одного учителя")
            return None

    async def get_teacher_by_id(self, id) -> Teacher | None:
        query = select(Teacher).where(Teacher.id == id)
        res = await self.db_session.execute(query)  # Make an asynchronous query to the database to search for a teacher
        teacher_row = res.scalar()  # return object Teacher or None
        if teacher_row is not None:
            logger.info(f"Учитель с id: {id} был успешно найден")
            return Teacher(
                name=teacher_row.name,
                surname=teacher_row.surname,
                phone_number=teacher_row.phone_number,
                email=teacher_row.email,
                fathername=teacher_row.fathername
            )

        logger.warning(f"Не было найдено ни одного учителя с таким id: {id}")
        return None

    async def get_teacher_by_name_surname(self, name: str, surname: str) -> Teacher | None:
        query = select(Teacher).where(
            (Teacher.name == name) & (Teacher.surname == surname)
        )
        res = await self.db_session.execute(query)
        teacher_row = res.scalar()  # return object Teacher or None
        if teacher_row is not None:
            logger.info(f"Учитель с ФИ: {name} - {surname} был успешно найден")
            return Teacher(
                name=teacher_row.name,
                surname=teacher_row.surname,
                phone_number=teacher_row.phone_number,
                email=teacher_row.email,
                fathername=teacher_row.fathername
            )
        logger.warning(f"Не было найдено ни одного учителя с таким ФИ: {name} - {surname}")
        return None

    async def update(self, id, **kwargs) -> Optional[int]:
        # kwargs - it is the fields which we want to update
        query = (
            update(Teacher).
            where(Teacher.id == id).
            values(**kwargs).
            returning(Teacher.id)
        )
        res = await self.db_session.execute(query)
        updated_teacher = res.scalar()  # return Teacher id or None (because returning == Teacher.id)
        if updated_teacher is not None:
            logger.info(f"У учителя с id: {id} были успешно обновлены поля: {" - ".join(kwargs.keys())}")
            return updated_teacher.id
        logger.warning(f"Не было найдено ни одного учителя с таким id: {id}")
        return None
