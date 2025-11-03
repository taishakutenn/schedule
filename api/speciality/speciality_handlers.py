from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from api.speciality.speciality_pydantic import *
from api.models import QueryParams
from db.session import get_db
from api.speciality.speciality_services import SpecialityService

speciality_router = APIRouter()

speciality_service = SpecialityService()


@speciality_router.post("/create", response_model=ShowSpecialityWithHATEOAS, status_code=201)
async def create_speciality(body: CreateSpeciality, request: Request, db: AsyncSession = Depends(get_db)):
    return await speciality_service._create_new_speciality(body, request, db)


@speciality_router.get("/search/by_speciality_code/{speciality_code}", response_model=ShowSpecialityWithHATEOAS, responses={404: {"description": "Специальность не найдена"}})
async def get_speciality_by_code(speciality_code: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await speciality_service._get_speciality_by_code(speciality_code, request, db)


@speciality_router.get("/search", response_model=ShowSpecialityListWithHATEOAS)
async def get_all_specialities(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await speciality_service._get_all_specialities(query_param.page, query_param.limit, request, db)


@speciality_router.delete("/delete/{speciality_code}", response_model=ShowSpecialityWithHATEOAS, responses={404: {"description": "Специальность не найдена"}})
async def delete_speciality(speciality_code: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await speciality_service._delete_speciality(speciality_code, request, db)


@speciality_router.put("/update", response_model=ShowSpecialityWithHATEOAS, responses={404: {"description": "Специальность не найдена"}})
async def update_speciality(body: UpdateSpeciality, request: Request, db: AsyncSession = Depends(get_db)):
    return await speciality_service._update_speciality(body, request, db)
