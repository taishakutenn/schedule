from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from api.semester.semester_pydantic  import *
from api.models import QueryParams
from db.session import get_db
from api.semester.semester_services import SemesterService

semester_router = APIRouter()

semester_service = SemesterService()


@semester_router.post("/create", response_model=ShowSemesterWithHATEOAS, status_code=201)
async def create_semester(body: CreateSemester, request: Request, db: AsyncSession = Depends(get_db)):
    return await semester_service._create_new_semester(body, request, db)


@semester_router.get("/search/by_semester_and_plan/{semester}/{plan_id}", response_model=ShowSemesterWithHATEOAS, responses={404: {"description": "Семестр не найден"}})
async def get_semester_by_semester_and_plan(semester: int, plan_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await semester_service._get_semester_by_semester_and_plan(semester, plan_id, request, db)


@semester_router.get("/search", response_model=ShowSemesterListWithHATEOAS)
async def get_all_semesters(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await semester_service._get_all_semesters(query_param.page, query_param.limit, request, db)


@semester_router.delete("/delete/{semester}/{plan_id}", response_model=ShowSemesterWithHATEOAS, responses={404: {"description": "Семестр не найден"}})
async def delete_semester(semester: int, plan_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await semester_service._delete_semester(semester, plan_id, request, db)


@semester_router.put("/update", response_model=ShowSemesterWithHATEOAS, responses={404: {"description": "Семестр не найден"}})
async def update_semester(body: UpdateSemester, request: Request, db: AsyncSession = Depends(get_db)):
    return await semester_service._update_semester(body, request, db)
