"""
File for encapsulating business logic,
here classes are written for implementing crud operations for each table.
There is no need to do checks in the data,
because it is assumed that the data submitted here is already validated.
"""

from typing import Union, Tuple, Optional

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from models import Teacher
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

    async def delete_teacher(self, id) -> bool:
        query = delete(Teacher).where(Teacher.id == id).returning(Teacher.id)
        res = await self.db_session.execute(query)
        deleted_teacher = res.fetchone()
        if not deleted_teacher:  # if there aren't deleted records
            logger.warning(f"Не было найдено ни одного учителя с таким id: {id}")
            return False
        logger.info(f"Учитель с id {id} был успешно удалён из бд")
        return True

    async def get_teacher_by_id(self, id) -> Union[int, None]:
        query = select(Teacher).where(Teacher.id == id)
        res = await self.db_session.execute(query)  # Make an asynchronous query to the database to search for a teacher
        teacher_row = res.scalar()  # return object Teacher or None
        if teacher_row is not None:
            logger.info(f"Учитель с id: {id} был успешно найден")
            return teacher_row.id
        logger.warning(f"Не было найдено ни одного учителя с таким id: {id}")
        return None

    async def get_teacher_by_name_surname(self, name: str, surname: str) -> Union[int, None]:
        query = select(Teacher).where(
            (Teacher.name == name) & (Teacher.surname == surname)
        )
        res = await self.db_session.execute(query)
        teacher_row = res.scalar()  # return object Teacher or None
        if teacher_row is not None:
            logger.info(f"Учитель с ФИ: {name} - {surname} был успешно найден")
            return teacher_row.id
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
