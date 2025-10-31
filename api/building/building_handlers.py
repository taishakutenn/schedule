from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from api.building.building_pydantic import *
from api.models import QueryParams
from db.session import get_db
from api.building.building_services import BuildingService

building_router = APIRouter()

building_service = BuildingService()


@building_router.post("/create", response_model=ShowBuildingWithHATEOAS, status_code=201)
async def create_building(body: CreateBuilding, request: Request, db: AsyncSession = Depends(get_db)):
    return await building_service._create_new_building(body, request, db)


@building_router.get("/search/by_number/{building_number}", response_model=ShowBuildingWithHATEOAS, responses={404: {"description": "Здание не найдено"}})
async def get_building_by_number(building_number: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await building_service._get_building_by_number(building_number, request, db)


@building_router.get("/search/by_address/{building_address}", response_model=ShowBuildingWithHATEOAS, responses={404: {"description": "Здание не найдено"}})
async def get_building_by_address(address: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await building_service._get_building_by_address(address, request, db)


@building_router.get("/search", response_model=ShowBuildingListWithHATEOAS)
async def get_all_buildings(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await building_service._get_all_buildings(query_param.page, query_param.limit, request, db)


@building_router.delete("/delete/{building_number}", response_model=ShowBuildingWithHATEOAS, responses={404: {"description": "Здание не найдено"}})
async def delete_building(building_number: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await building_service._delete_building(building_number, request, db)


@building_router.put("/update", response_model=ShowBuildingWithHATEOAS, responses={404: {"description": "Здание не найдено"}})
async def update_building(body: UpdateBuilding, request: Request, db: AsyncSession = Depends(get_db)):
    return await building_service._update_building(body, request, db)
