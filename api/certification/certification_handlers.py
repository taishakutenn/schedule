from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from api.certification.certification_pydantic  import *
from api.models import QueryParams
from db.session import get_db
from api.certification.certification_services import CertificationService

certification_router = APIRouter()

certification_service = CertificationService()


@certification_router.post("/create", response_model=ShowCertificationWithHATEOAS, status_code=201)
async def create_certification(body: CreateCertification, request: Request, db: AsyncSession = Depends(get_db)):
    return await certification_service._create_new_certification(body, request, db)


@certification_router.get("/search/by_id/{certification_id}", response_model=ShowCertificationWithHATEOAS, responses={404: {"description": "Сертификация не найдена"}})
async def get_certification_by_id(certification_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await certification_service._get_certification_by_id(certification_id, request, db)


@certification_router.get("/search/by_ids", response_model=ShowCertificationListWithHATEOAS, responses={404: {"description": "Сертификации не найдены"}})
async def get_certifications_by_ids(query_param: Annotated[QueryParams, Depends()], request: Request, ids: list[int] = Query(...), db: AsyncSession = Depends(get_db)):
    return await certification_service._get_certifications_by_ids(ids, query_param.page, query_param.limit, request, db)


@certification_router.get("/search", response_model=ShowCertificationListWithHATEOAS)
async def get_all_certifications(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await certification_service._get_all_certifications(query_param.page, query_param.limit, request, db)


@certification_router.delete("/delete/{certification_id}", response_model=ShowCertificationWithHATEOAS, responses={404: {"description": "Сертификация не найдена"}})
async def delete_certification(certification_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await certification_service._delete_certification(certification_id, request, db)


@certification_router.put("/update", response_model=ShowCertificationWithHATEOAS, responses={404: {"description": "Сертификация не найдена"}})
async def update_certification(body: UpdateCertification, request: Request, db: AsyncSession = Depends(get_db)):
    return await certification_service._update_certification(body, request, db)
