"""
file for handlers
"""

from fastapi import APIRouter, Depends, Query
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from api.models import ShowTeacher, CreateTeacher, QueryParams
from db.dals import TeacherDAL
from db.session import get_db

teacher_router = APIRouter()  # Create router for teachers


async def _create_new_teacher(body: CreateTeacher, db) -> ShowTeacher:
    async with db as session:
        async with session.begin():
            teacher_dal = TeacherDAL(session)
            teacher = await teacher_dal.create_teacher(
                name=body.name,
                surname=body.surname,
                phone_number=body.phone_number,
                email=str(body.email),
                fathername=body.fathername
            )
            return ShowTeacher(
                name=teacher.name,
                surname=teacher.surname,
                phone_number=teacher.phone_number,
                email=teacher.email,
                fathername=teacher.fathername
            )


async def _get_teacher_by_id(id, db) -> ShowTeacher | list:
    async with db as session:
        async with session.begin():
            teacher_dal = TeacherDAL(session)
            teacher = await teacher_dal.get_teacher_by_id(id)

            # if teacher exist
            if teacher is not None:
                return ShowTeacher(
                    name=teacher.name,
                    surname=teacher.surname,
                    phone_number=teacher.phone_number,
                    email=teacher.email,
                    fathername=teacher.fathername
                )
            return []


async def _get_teacher_by_name_and_surname(name, surname, db) -> ShowTeacher | list:
    async with db as session:
        async with session.begin():
            teacher_dal = TeacherDAL(session)
            teacher = await teacher_dal.get_teacher_by_name_surname(name, surname)

            # if teacher exist
            if teacher is not None:
                return ShowTeacher(
                    name=teacher.name,
                    surname=teacher.surname,
                    phone_number=teacher.phone_number,
                    email=teacher.email,
                    fathername=teacher.fathername
                )

            return []


async def _get_all_teachers(page: int, limit: int, db) -> list[ShowTeacher]:
    async with db as session:
        async with session.begin():
            teacher_dal = TeacherDAL(session)
            teachers = await teacher_dal.get_all_teachers(page, limit)
            if teachers:
                return teachers
            return []

async def _delete_teacher(teacher_id: int, db) -> ShowTeacher | list:
    async with db as session:
        async with await session.begin():
            teacher_dal = TeacherDAL(session)
            teacher = await teacher_dal.delete_teacher(teacher_id)
            if teacher:
                return teacher
            return []


@teacher_router.post("/create", response_model=ShowTeacher)
async def create_teacher(body: CreateTeacher, db: AsyncSession = Depends(get_db)):
    return await _create_new_teacher(body, db)


@teacher_router.get("/search/by_id/{teacher_id}", response_model=ShowTeacher)
async def get_teacher_by_id(teacher_id: int, db: AsyncSession = Depends(get_db)):
    return await _get_teacher_by_id(teacher_id, db)


@teacher_router.get("/search/by_humanity", response_model=ShowTeacher)
async def get_teacher_by_name_and_surname(name: str, surname: str, db: AsyncSession = Depends(get_db)):
    return await _get_teacher_by_name_and_surname(name, surname, db)


@teacher_router.get("/search", response_model=list[ShowTeacher])
async def get_all_teachers(query_param: Annotated[QueryParams, Depends()], db: AsyncSession = Depends(get_db)):
    """
    query_param set via Annotated so that fastapi understands
    that the pydantic model QueryParam refers to the query parameters,
    we specify this as the second argument for Annotated.
    Wherever there will be pagination and the number of elements on the page,
    it is better to use this pydantic model, so as not to manually enter these parameters each time.
    Link to documentation: https://fastapi.tiangolo.com/ru/tutorial/query-param-models/
    """
    return await _get_all_teachers(query_param.page, query_param.limit, db)


@teacher_router.put("/delete/{teacher_id}", response_model=ShowTeacher)
async def delete_teacher(teacher_id: int, db: AsyncSession = Depends(get_db)):
    return await _delete_teacher(teacher_id, db)


@teacher_router.put("/update/{teacher_id}", response_model=ShowTeacher)
async def update_teacher():
    pass