from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from api.module.module_pydantic  import *
from api.models import QueryParams
from db.session import get_db
from api.module.module_services import ModuleService

module_router = APIRouter()

module_service = ModuleService()


@module_router.post("/create", response_model=ShowModuleWithHATEOAS, status_code=201)
async def create_module(body: CreateModule, request: Request, db: AsyncSession = Depends(get_db)):
    return await module_service._create_new_module(body, request, db)


@module_router.get("/search/by_id/{module_id}", response_model=ShowModuleWithHATEOAS, responses={404: {"description": "Модуль не найден"}})
async def get_module_by_id(module_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await module_service._get_module_by_id(module_id, request, db)


@module_router.get("/search/by_cycle/{cycle_in_chapter_id}", response_model=ShowModuleListWithHATEOAS, responses={404: {"description": "Модули не найдены"}})
async def get_modules_by_cycle(cycle_in_chapter_id: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await module_service._get_modules_by_cycle(cycle_in_chapter_id, query_param.page, query_param.limit, request, db)


@module_router.get("/search", response_model=ShowModuleListWithHATEOAS)
async def get_all_modules(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await module_service._get_all_modules(query_param.page, query_param.limit, request, db)


@module_router.delete("/delete/{module_id}", response_model=ShowModuleWithHATEOAS, responses={404: {"description": "Модуль не найден"}})
async def delete_module(module_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await module_service._delete_module(module_id, request, db)


@module_router.put("/update", response_model=ShowModuleWithHATEOAS, responses={404: {"description": "Модуль не найден"}})
async def update_module(body: UpdateModule, request: Request, db: AsyncSession = Depends(get_db)):
    return await module_service._update_module(body, request, db)
