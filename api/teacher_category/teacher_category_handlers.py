from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from api.teacher_category.teacher_category_pydantic import *
from api.models import QueryParams
from db.session import get_db
from api.teacher_category.teacher_category_services import TeacherCategoryService

category_router = APIRouter()

#
teacher_category_service = TeacherCategoryService()


@category_router.post("/create", response_model=ShowTeacherCategoryWithHATEOAS, status_code=status.HTTP_201_CREATED)
async def create_category(body: CreateTeacherCategory, request: Request, db: AsyncSession = Depends(get_db)):
    return await teacher_category_service._create_new_category(body, request, db)


@category_router.get("/search/{teacher_category}", response_model=ShowTeacherCategoryWithHATEOAS,
                     responses={404: {"description": "Категория преподавателя не найдена"}})
async def get_category(teacher_category: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await teacher_category_service._get_category(teacher_category, request, db)


@category_router.get("/search", response_model=ShowTeacherCategoryListWithHATEOAS,
                     responses={404: {"description": "Категории преподавателей не найдены"}})
async def get_all_categories(query_param: Annotated[QueryParams, Depends()], request: Request,
                             db: AsyncSession = Depends(get_db)):
    return await teacher_category_service._get_all_categories(query_param.page, query_param.limit, request, db)


@category_router.delete("/delete/{teacher_category}", response_model=ShowTeacherCategoryWithHATEOAS,
                        responses={404: {"description": "Категория преподавателя не найдена"}})
async def delete_category(teacher_category: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await teacher_category_service._delete_category(teacher_category, request, db)


@category_router.put("/update", response_model=ShowTeacherCategoryWithHATEOAS,
                     responses={404: {"description": "Категория преподавателя не найдена"}})
async def update_category(body: UpdateTeacherCategory, request: Request, db: AsyncSession = Depends(get_db)):
    return await teacher_category_service._update_category(body, request, db)
