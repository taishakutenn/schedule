from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from api.session.session_pydantic import *
from api.models import QueryParams
from db.session import get_db
from api.session.session_services import SessionService

session_router = APIRouter()

session_service = SessionService()


@session_router.post("/create", response_model=ShowSessionWithHATEOAS, status_code=201)
async def create_session(body: CreateSession, request: Request, db: AsyncSession = Depends(get_db)):
    return await session_service._create_new_session(body, request, db)


@session_router.get("/search/by_composite_key/{session_number}/{session_date}/{teacher_in_plan}", response_model=ShowSessionWithHATEOAS, responses={404: {"description": "Занятие не найдено"}})
async def get_session_by_composite_key(session_number: int, session_date: date, teacher_in_plan: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await session_service._get_session_by_composite_key(session_number, session_date, teacher_in_plan, request, db)


@session_router.get("/search/by_plan/{teacher_in_plan_id}", response_model=ShowSessionListWithHATEOAS, responses={404: {"description": "Занятия не найдены"}})
async def get_sessions_by_plan(teacher_in_plan_id: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await session_service._get_sessions_by_plan(teacher_in_plan_id, query_param.page, query_param.limit, request, db)


@session_router.get("/search/by_date/{session_date}", response_model=ShowSessionListWithHATEOAS, responses={404: {"description": "Занятия не найдены"}})
async def get_sessions_by_date(session_date: date, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await session_service._get_sessions_by_date(session_date, query_param.page, query_param.limit, request, db)


@session_router.get("/search/by_type/{session_type}", response_model=ShowSessionListWithHATEOAS, responses={404: {"description": "Занятия не найдены"}})
async def get_sessions_by_type(session_type: str, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await session_service._get_sessions_by_type(session_type, query_param.page, query_param.limit, request, db)


@session_router.get("/search/by_cabinet/{building_number}/{cabinet_number}", response_model=ShowSessionListWithHATEOAS, responses={404: {"description": "Занятия не найдены"}})
async def get_sessions_by_cabinet(building_number: int, cabinet_number: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await session_service._get_sessions_by_cabinet(cabinet_number, building_number, query_param.page, query_param.limit, request, db)


@session_router.get("/search", response_model=ShowSessionListWithHATEOAS)
async def get_all_sessions(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await session_service._get_all_sessions(query_param.page, query_param.limit, request, db)


@session_router.delete("/delete/{session_number}/{session_date}/{teacher_in_plan}", response_model=ShowSessionWithHATEOAS, responses={404: {"description": "Занятие не найдено"}})
async def delete_session(session_number: int, session_date: date, teacher_in_plan: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await session_service._delete_session(session_number, session_date, teacher_in_plan, request, db)


@session_router.put("/update", response_model=ShowSessionWithHATEOAS, responses={404: {"description": "Занятие не найдено"}})
async def update_session(body: UpdateSession, request: Request, db: AsyncSession = Depends(get_db)):
    return await session_service._update_session(body, request, db)
