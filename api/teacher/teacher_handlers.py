from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from api.teacher.teacher_pydantic import *
from api.models import QueryParams
from db.session import get_db
from api.teacher.teacher_services import TeacherService

teacher_router = APIRouter()

teacher_service = TeacherService()


@teacher_router.post("/create", response_model=ShowTeacherWithHATEOAS, status_code=status.HTTP_201_CREATED)
async def create_teacher(body: CreateTeacher, request: Request, db: AsyncSession = Depends(get_db)):
    return await teacher_service._create_new_teacher(body, request, db)


@teacher_router.get("/search/by_id/{teacher_id}", response_model=ShowTeacherWithHATEOAS, responses={404: {"description": "Преподаватель не найден"}})
async def get_teacher_by_id(teacher_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await teacher_service._get_teacher_by_id(teacher_id, request, db)


@teacher_router.get("/search", response_model=ShowTeacherListWithHATEOAS, responses={404: {"description": "Преподаватели не найдены"}})
async def get_all_teachers(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await teacher_service._get_all_teachers(query_param.page, query_param.limit, request, db)


@teacher_router.delete("/delete/{teacher_id}", response_model=ShowTeacherWithHATEOAS, responses={404: {"description": "Преподаватель не найден"}})
async def delete_teacher(teacher_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await teacher_service._delete_teacher(teacher_id, request, db)


@teacher_router.put("/update", response_model=ShowTeacherWithHATEOAS, responses={404: {"description": "Преподаватель не найден"}})
async def update_teacher(body: UpdateTeacher, request: Request, db: AsyncSession = Depends(get_db)):
    return await teacher_service._update_teacher(body, request, db)
