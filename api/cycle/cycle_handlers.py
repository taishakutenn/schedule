from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from api.cycle.cycle_pydantic  import *
from api.models import QueryParams
from db.session import get_db
from api.cycle.cycle_services import CycleService

cycle_router = APIRouter()

cycle_service = CycleService()


@cycle_router.post("/create", response_model=ShowCycleWithHATEOAS, status_code=201)
async def create_cycle(body: CreateCycle, request: Request, db: AsyncSession = Depends(get_db)):
    return await cycle_service._create_new_cycle(body, request, db)


@cycle_router.get("/search/by_id/{cycle_id}", response_model=ShowCycleWithHATEOAS, responses={404: {"description": "Цикл не найден"}})
async def get_cycle_by_id(cycle_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await cycle_service._get_cycle_by_id(cycle_id, request, db)


@cycle_router.get("/search/by_chapter/{chapter_in_plan_id}", response_model=ShowCycleListWithHATEOAS, responses={404: {"description": "Циклы не найдены"}})
async def get_cycles_by_chapter(chapter_in_plan_id: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await cycle_service._get_cycles_by_chapter(chapter_in_plan_id, query_param.page, query_param.limit, request, db)


@cycle_router.get("/search", response_model=ShowCycleListWithHATEOAS)
async def get_all_cycles(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await cycle_service._get_all_cycles(query_param.page, query_param.limit, request, db)


@cycle_router.delete("/delete/{cycle_id}", response_model=ShowCycleWithHATEOAS, responses={404: {"description": "Цикл не найден"}})
async def delete_cycle(cycle_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await cycle_service._delete_cycle(cycle_id, request, db)


@cycle_router.put("/update", response_model=ShowCycleWithHATEOAS, responses={404: {"description": "Цикл не найден"}})
async def update_cycle(body: UpdateCycle, request: Request, db: AsyncSession = Depends(get_db)):
    return await cycle_service._update_cycle(body, request, db)
