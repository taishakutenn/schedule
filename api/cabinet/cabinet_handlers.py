from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from api.cabinet.cabinet_pydantic import *
from api.models import QueryParams
from db.session import get_db
from api.cabinet.cabinet_services import CabinetService

cabinet_router = APIRouter()

cabinet_service = CabinetService()


@cabinet_router.post("/create", response_model=ShowCabinetWithHATEOAS, status_code=201)
async def create_cabinet(body: CreateCabinet, request: Request, db: AsyncSession = Depends(get_db)):
    return await cabinet_service._create_new_cabinet(body, request, db)


@cabinet_router.get("/search/by_building_and_number/{building_number}/{cabinet_number}", response_model=ShowCabinetWithHATEOAS, responses={404: {"description": "Кабинет не найден"}})
async def get_cabinet_by_number_and_building(building_number: int, cabinet_number: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await cabinet_service._get_cabinet_by_number_and_building(building_number, cabinet_number, request, db)


@cabinet_router.get("/search", response_model=ShowCabinetListWithHATEOAS)
async def get_all_cabinets(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await cabinet_service._get_all_cabinets(query_param.page, query_param.limit, request, db)


@cabinet_router.get("/search/by_building/{building_number}", response_model=ShowCabinetListWithHATEOAS, responses={404: {"description": "Кабинеты не найдены"}})
async def get_cabinets_by_building(building_number: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await cabinet_service._get_cabinets_by_building(building_number, query_param.page, query_param.limit, request, db)


@cabinet_router.delete("/delete/{building_number}/{cabinet_number}", response_model=ShowCabinetWithHATEOAS, responses={404: {"description": "Кабинет не найден"}})
async def delete_cabinet(building_number: int, cabinet_number: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await cabinet_service._delete_cabinet(building_number, cabinet_number, request, db)


@cabinet_router.put("/update", response_model=ShowCabinetWithHATEOAS, responses={404: {"description": "Кабинет не найден"}})
async def update_cabinet(body: UpdateCabinet, request: Request, db: AsyncSession = Depends(get_db)):
    return await cabinet_service._update_cabinet(body, request, db)
