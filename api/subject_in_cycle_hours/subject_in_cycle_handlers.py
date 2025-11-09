from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from api.subject_in_cycle_hours.subject_in_cycle_pydantic  import *
from api.models import QueryParams
from db.session import get_db
from api.subject_in_cycle_hours.subject_in_cycle_services import SubjectInCycleService

subject_in_cycle_hours_router = APIRouter()

subject_in_cycle_service = SubjectInCycleService()


@subject_in_cycle_hours_router.post("/create", response_model=ShowSubjectsInCycleHoursWithHATEOAS, status_code=201)
async def create_subject_in_cycle_hours(body: CreateSubjectsInCycleHours, request: Request, db: AsyncSession = Depends(get_db)):
    return await subject_in_cycle_service._create_new_subject_in_cycle_hours(body, request, db)


@subject_in_cycle_hours_router.get("/search/by_id/{hours_id}", response_model=ShowSubjectsInCycleHoursWithHATEOAS, responses={404: {"description": "Запись о часах для предмета не найдена"}})
async def get_subject_in_cycle_hours_by_id(hours_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await subject_in_cycle_service._get_subject_in_cycle_hours_by_id(hours_id, request, db)


@subject_in_cycle_hours_router.get("/search/by_subject_in_cycle/{subject_in_cycle_id}", response_model=ShowSubjectsInCycleHoursListWithHATEOAS, responses={404: {"description": "Записи о часах для предмета не найдены"}})
async def get_subjects_in_cycle_hours_by_subject_in_cycle(subject_in_cycle_id: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await subject_in_cycle_service._get_subjects_in_cycle_hours_by_subject_in_cycle(subject_in_cycle_id, query_param.page, query_param.limit, request, db)


@subject_in_cycle_hours_router.get("/search/by_subject_and_semester/{subject_in_cycle_id}/{semester}", response_model=ShowSubjectsInCycleHoursListWithHATEOAS, responses={404: {"description": "Записи о часах для предмета в цикле по семестру не найдены"}})
async def get_subjects_in_cycle_hours_by_subject_and_semester(subject_in_cycle_id: int, semester: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await subject_in_cycle_service._get_subjects_in_cycle_hours_by_subject_and_semester(subject_in_cycle_id, semester, request, db)


@subject_in_cycle_hours_router.get("/search/by_semester/{semester}", response_model=ShowSubjectsInCycleHoursListWithHATEOAS, responses={404: {"description": "Записи о часах для семестра не найдены"}})
async def get_subjects_in_cycle_hours_by_semester(semester: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await subject_in_cycle_service._get_subjects_in_cycle_hours_by_semester(semester, query_param.page, query_param.limit, request, db)


@subject_in_cycle_hours_router.get("/search", response_model=ShowSubjectsInCycleHoursListWithHATEOAS)
async def get_all_subjects_in_cycle_hours(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await subject_in_cycle_service._get_all_subjects_in_cycle_hours(query_param.page, query_param.limit, request, db)


@subject_in_cycle_hours_router.delete("/delete/{hours_id}", response_model=ShowSubjectsInCycleHoursWithHATEOAS, responses={404: {"description": "Запись о часах для предмета не найдена"}})
async def delete_subject_in_cycle_hours(hours_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await subject_in_cycle_service._delete_subject_in_cycle_hours(hours_id, request, db)


@subject_in_cycle_hours_router.put("/update", response_model=ShowSubjectsInCycleHoursWithHATEOAS, responses={404: {"description": "Запись о часах для предмета не найдена"}})
async def update_subject_in_cycle_hours(body: UpdateSubjectsInCycleHours, request: Request, db: AsyncSession = Depends(get_db)):
    return await subject_in_cycle_service._update_subject_in_cycle_hours(body, request, db)