from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from api.session_type.session_type_pydantic import *
from api.models import QueryParams
from db.session import get_db
from api.session_type.session_type_services import SessionTypeService

session_type_router = APIRouter()

session_type_service = SessionTypeService()


@session_type_router.post("/create", response_model=ShowSessionTypeWithHATEOAS, status_code=201)
async def create_session_type(body: CreateSessionType, request: Request, db: AsyncSession = Depends(get_db)):
    return await session_type_service._create_new_session_type(body, request, db)


@session_type_router.get("/search/by_name/{name}", response_model=ShowSessionTypeWithHATEOAS, responses={404: {"description": "Тип сессии не найден"}})
async def get_session_type_by_name(name: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await session_type_service._get_session_type_by_name(name, request, db)


@session_type_router.get("/search", response_model=ShowSessionTypeListWithHATEOAS)
async def get_all_session_types(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await session_type_service._get_all_session_types(query_param.page, query_param.limit, request, db)


@session_type_router.delete("/delete/{name}", response_model=ShowSessionTypeWithHATEOAS, responses={404: {"description": "Тип сессии не найден"}})
async def delete_session_type(name: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await session_type_service._delete_session_type(name, request, db)


@session_type_router.put("/update", response_model=ShowSessionTypeWithHATEOAS, responses={404: {"description": "Тип сессии не найден"}})
async def update_session_type(body: UpdateSessionType, request: Request, db: AsyncSession = Depends(get_db)):
    return await session_type_service._update_session_type(body, request, db)
