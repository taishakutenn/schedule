from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from api.teacher_building.teacher_building_pydantic  import *
from api.models import QueryParams
from db.session import get_db
from api.teacher_building.teacher_building_services import TeacherBuildingService

teacher_building_router = APIRouter()

teacher_building_service = TeacherBuildingService()


@teacher_building_router.post("/create", response_model=ShowTeacherBuildingWithHATEOAS, status_code=201)
async def create_teacher_building(body: CreateTeacherBuilding, request: Request, db: AsyncSession = Depends(get_db)):
    return await teacher_building_service._create_new_teacher_building(body, request, db)


@teacher_building_router.get("/search/by_id/{teacher_building_id}", response_model=ShowTeacherBuildingWithHATEOAS, responses={404: {"description": "Связь преподавателя и здания не найдена"}})
async def get_teacher_building_by_id(teacher_building_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await teacher_building_service._get_teacher_building_by_id(teacher_building_id, request, db)


@teacher_building_router.get("/search/by_teacher/{teacher_id}", response_model=ShowTeacherBuildingListWithHATEOAS, responses={404: {"description": "Связи преподавателя и зданий не найдены"}})
async def get_teachers_buildings_by_teacher(teacher_id: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await teacher_building_service._get_teachers_buildings_by_teacher(teacher_id, query_param.page, query_param.limit, request, db)


@teacher_building_router.get("/search/by_building/{building_number}", response_model=ShowTeacherBuildingListWithHATEOAS, responses={404: {"description": "Связи преподавателей и здания не найдены"}})
async def get_teachers_buildings_by_building(building_number: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await teacher_building_service._get_teachers_buildings_by_building(building_number, query_param.page, query_param.limit, request, db)


@teacher_building_router.get("/search", response_model=ShowTeacherBuildingListWithHATEOAS)
async def get_all_teachers_buildings(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await teacher_building_service._get_all_teachers_buildings(query_param.page, query_param.limit, request, db)


@teacher_building_router.delete("/delete/{teacher_building_id}", response_model=ShowTeacherBuildingWithHATEOAS, responses={404: {"description": "Связь преподавателя и здания не найдена"}})
async def delete_teacher_building(teacher_building_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await teacher_building_service._delete_teacher_building(teacher_building_id, request, db)


@teacher_building_router.put("/update", response_model=ShowTeacherBuildingWithHATEOAS, responses={404: {"description": "Связь преподавателя и здания не найдена"}})
async def update_teacher_building(body: UpdateTeacherBuilding, request: Request, db: AsyncSession = Depends(get_db)):
    return await teacher_building_service._update_teacher_building(body, request, db)
