from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from api.group.group_pydantic import *
from api.models import QueryParams
from db.session import get_db
from api.group.group_services import GroupService

group_router = APIRouter()

group_service = GroupService()


@group_router.post("/create", response_model=ShowGroupWithHATEOAS, status_code=201)
async def create_group(body: CreateGroup, request: Request, db: AsyncSession = Depends(get_db)):
    return await group_service._create_new_group(body, request, db)


@group_router.get("/search/by_group_name/{group_name}", response_model=ShowGroupWithHATEOAS, responses={404: {"description": "Группа не найдена"}})
async def get_group_by_name(group_name: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await group_service._get_group_by_name(group_name, request, db)


@group_router.get("/search/by_advisor/{advisor_id}", response_model=ShowGroupWithHATEOAS, responses={404: {"description": "Группа не найдена"}})
async def get_group_by_advisor(advisor_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await group_service._get_group_by_advisor(advisor_id, request, db)


@group_router.get("/search/by_speciality/{speciality_code}", response_model=ShowGroupListWithHATEOAS, responses={404: {"description": "Группы не найдены"}})
async def get_groups_by_speciality(speciality_code: str, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await group_service._get_groups_by_speciality(speciality_code, query_param.page, query_param.limit, request, db)


@group_router.get("/search/by_names", response_model=ShowGroupListWithHATEOAS, responses={404: {"description": "Группы не найдены"}})
async def get_groups_by_names(query_param: Annotated[QueryParams, Depends()], request: Request, names: list[str] = Query(...), db: AsyncSession = Depends(get_db)):
    return await group_service._get_groups_by_names(names, query_param.page, query_param.limit, request, db)


@group_router.get("/search", response_model=ShowGroupListWithHATEOAS)
async def get_all_groups(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await group_service._get_all_groups(query_param.page, query_param.limit, request, db)


@group_router.delete("/delete/{group_name}", response_model=ShowGroupWithHATEOAS, responses={404: {"description": "Группа не найдена"}})
async def delete_group(group_name: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await group_service._delete_group(group_name, request, db)


@group_router.put("/update", response_model=ShowGroupWithHATEOAS, responses={404: {"description": "Группа не найдена"}})
async def update_group(body: UpdateGroup, request: Request, db: AsyncSession = Depends(get_db)):
    return await group_service._update_group(body, request, db)
