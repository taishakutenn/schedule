"""
file for handlers
"""

from fastapi import APIRouter, Depends
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import ShowTeacher, CreateTeacher
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
                email=EmailStr(teacher.email),
                fathername=teacher.fathername
            )


@teacher_router.post("/", response_model=ShowTeacher)
async def create_teacher(body: CreateTeacher, db: AsyncSession = Depends(get_db)):
    return await _create_new_teacher(body, db)


# @teacher_router.get("/")
# async def get_teacher_by_id():
