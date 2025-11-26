from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from api.plan.plan_pydantic  import *
from api.models import QueryParams
from db.session import get_db
from api.plan.plan_services import PlanService

plan_router = APIRouter()

plan_service = PlanService()


@plan_router.post("/create", response_model=ShowPlanWithHATEOAS, status_code=201)
async def create_plan(body: CreatePlan, request: Request, db: AsyncSession = Depends(get_db)):
    return await plan_service._create_new_plan(body, request, db)


@plan_router.get("/search/by_id/{plan_id}", response_model=ShowPlanWithHATEOAS, responses={404: {"description": "Учебный план не найден"}})
async def get_plan_by_id(plan_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await plan_service._get_plan_by_id(plan_id, request, db)


@plan_router.get("/search/by_year_and_speciality/{year}/{speciality}", response_model=ShowPlanWithHATEOAS, responses={404: {"description": "Учебный план не найден"}})
async def get_plan_by_year_and_speciality(year: int, speciality: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await plan_service._get_plan_by_year_and_speciality(year, speciality, request, db)


@plan_router.get("/search/by_subject_hours_id/{subject_hours_id}", response_model=ShowPlanWithHATEOAS, responses={404: {"description": "Учебный план не найден"}})
async def get_plan_by_subject_hours_id(subject_hours_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await plan_service._get_plan_by_subject_hours_id(subject_hours_id, request, db)


@plan_router.get("/search", response_model=ShowPlanListWithHATEOAS)
async def get_all_plans(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await plan_service._get_all_plans(query_param.page, query_param.limit, request, db)


@plan_router.delete("/delete/{plan_id}", response_model=ShowPlanWithHATEOAS, responses={404: {"description": "Учебный план не найден"}})
async def delete_plan(plan_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await plan_service._delete_plan(plan_id, request, db)


@plan_router.put("/update", response_model=ShowPlanWithHATEOAS, responses={404: {"description": "Учебный план не найден"}})
async def update_plan(body: UpdatePlan, request: Request, db: AsyncSession = Depends(get_db)):
    return await plan_service._update_plan(body, request, db)
