from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from api.subject_in_cycle.subject_in_cycle_pydantic  import *
from api.models import QueryParams
from db.session import get_db
from api.subject_in_cycle.subject_in_cycle_services import SubjectInCycleService

subject_in_cycle_router = APIRouter()

subject_in_cycle_service = SubjectInCycleService()


@subject_in_cycle_router.post("/create", response_model=ShowSubjectsInCycleWithHATEOAS, status_code=201)
async def create_subject_in_cycle(body: CreateSubjectsInCycle, request: Request, db: AsyncSession = Depends(get_db)):
    return await subject_in_cycle_service._create_new_subject_in_cycle(body, request, db)


@subject_in_cycle_router.get("/search/by_id/{subject_in_cycle_id}", response_model=ShowSubjectsInCycleWithHATEOAS, responses={404: {"description": "Предмет в цикле не найден"}})
async def get_subject_in_cycle_by_id(subject_in_cycle_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await subject_in_cycle_service._get_subject_in_cycle_by_id(subject_in_cycle_id, request, db)


@subject_in_cycle_router.get("/search/by_cycle/{cycle_in_chapter_id}", response_model=ShowSubjectsInCycleListWithHATEOAS, responses={404: {"description": "Предметы в цикле не найдены"}})
async def get_subjects_in_cycle_by_cycle(cycle_in_chapter_id: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await subject_in_cycle_service._get_subjects_in_cycle_by_cycle(cycle_in_chapter_id, query_param.page, query_param.limit, request, db)


@subject_in_cycle_router.get("/search/by_module/{module_in_cycle_id}", response_model=ShowSubjectsInCycleListWithHATEOAS, responses={404: {"description": "Предметы в цикле не найдены"}})
async def get_subjects_in_cycle_by_module(module_in_cycle_id: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await subject_in_cycle_service._get_subjects_in_cycle_by_module(module_in_cycle_id, query_param.page, query_param.limit, request, db)


@subject_in_cycle_router.get("/search", response_model=ShowSubjectsInCycleListWithHATEOAS)
async def get_all_subjects_in_cycles(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await subject_in_cycle_service._get_all_subjects_in_cycles(query_param.page, query_param.limit, request, db)


@subject_in_cycle_router.get("/search/info_for_create/{group_name}/{semester}")
async def get_info_to_create_schedule(group_name: str, semester: int, db: AsyncSession = Depends(get_db)):
    return await subject_in_cycle_service._get_info_to_create_schedule(group_name, semester, db)


@subject_in_cycle_router.delete("/delete/{subject_in_cycle_id}", response_model=ShowSubjectsInCycleWithHATEOAS, responses={404: {"description": "Предмет в цикле не найден"}})
async def delete_subject_in_cycle(subject_in_cycle_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await subject_in_cycle_service._delete_subject_in_cycle(subject_in_cycle_id, request, db)


@subject_in_cycle_router.put("/update", response_model=ShowSubjectsInCycleWithHATEOAS, responses={404: {"description": "Предмет в цикле не найден"}})
async def update_subject_in_cycle(body: UpdateSubjectsInCycle, request: Request, db: AsyncSession = Depends(get_db)):
    return await subject_in_cycle_service._update_subject_in_cycle(body, request, db)
