from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from api.teacher_in_plan.teacher_in_plan_pydantic import *
from api.models import QueryParams
from db.session import get_db
from api.teacher_in_plan.teacher_in_plan_services import TeacherInPlanService

teacher_in_plan_router = APIRouter()

teacher_in_plan_service = TeacherInPlanService()


@teacher_in_plan_router.post("/create", response_model=ShowTeacherInPlanWithHATEOAS, status_code=201)
async def create_teacher_in_plan(body: CreateTeacherInPlan, request: Request, db: AsyncSession = Depends(get_db)):
    return await teacher_in_plan_service._create_new_teacher_in_plan(body, request, db)


@teacher_in_plan_router.get("/search/by_id/{teacher_in_plan_id}", response_model=ShowTeacherInPlanWithHATEOAS, responses={404: {"description": "Запись в расписании преподавателя не найдена"}})
async def get_teacher_in_plan_by_id(teacher_in_plan_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await teacher_in_plan_service._get_teacher_in_plan_by_id(teacher_in_plan_id, request, db)


@teacher_in_plan_router.get("/search/by_group_and_subject_hours/{group_name}/{subject_hours_id}",
                            response_model=ShowTeacherInPlanWithHATEOAS,
                            responses={404: {"description": "Запись в расписании преподавателя не найдена"}})
async def _get_teacher_in_plan_by_group_and_subject_hours(group_name: str, subject_hours_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await teacher_in_plan_service._get_teacher_in_plan_by_group_and_subject_hours(group_name,
                                                                                         subject_hours_id,
                                                                                         request,
                                                                                         db)


@teacher_in_plan_router.get("/search/by_teacher/{teacher_id}", response_model=ShowTeacherInPlanListWithHATEOAS, responses={404: {"description": "Записи в расписании преподавателя не найдены"}})
async def get_teachers_in_plans_by_teacher(teacher_id: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await teacher_in_plan_service._get_teachers_in_plans_by_teacher(teacher_id, query_param.page, query_param.limit, request, db)


@teacher_in_plan_router.get("/search/by_group/{group_name}", response_model=ShowTeacherInPlanListWithHATEOAS, responses={404: {"description": "Записи в расписании преподавателя не найдены"}})
async def get_teachers_in_plans_by_group(group_name: str, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await teacher_in_plan_service._get_teachers_in_plans_by_group(group_name, query_param.page, query_param.limit, request, db)


@teacher_in_plan_router.get("/search/by_subject_hours/{subject_hours_id}", response_model=ShowTeacherInPlanListWithHATEOAS, responses={404: {"description": "Записи в расписании преподавателя не найдены"}})
async def get_teachers_in_plans_by_subject_hours(subject_hours_id: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await teacher_in_plan_service._get_teachers_in_plans_by_subject_hours(subject_hours_id, query_param.page, query_param.limit, request, db)


@teacher_in_plan_router.get("/search/by_session_type/{session_type}", response_model=ShowTeacherInPlanListWithHATEOAS, responses={404: {"description": "Записи в расписании преподавателя не найдены"}})
async def get_teachers_in_plans_by_session_type(session_type: str, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await teacher_in_plan_service._get_teachers_in_plans_by_session_type(session_type, query_param.page, query_param.limit, request, db)


@teacher_in_plan_router.get("/search", response_model=ShowTeacherInPlanListWithHATEOAS)
async def get_all_teachers_in_plans(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await teacher_in_plan_service._get_all_teachers_in_plans(query_param.page, query_param.limit, request, db)


@teacher_in_plan_router.delete("/delete/{teacher_in_plan_id}", response_model=ShowTeacherInPlanWithHATEOAS, responses={404: {"description": "Запись в расписании преподавателя не найдена"}})
async def delete_teacher_in_plan(teacher_in_plan_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await teacher_in_plan_service._delete_teacher_in_plan(teacher_in_plan_id, request, db)


@teacher_in_plan_router.put("/update", response_model=ShowTeacherInPlanWithHATEOAS, responses={404: {"description": "Запись в расписании преподавателя не найдена"}})
async def update_teacher_in_plan(body: UpdateTeacherInPlan, request: Request, db: AsyncSession = Depends(get_db)):
    return await teacher_in_plan_service._update_teacher_in_plan(body, request, db)
