from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from api.stream.stream_pydantic  import *
from api.models import QueryParams
from db.session import get_db
from api.stream.stream_services import StreamService

stream_router = APIRouter()

stream_service = StreamService()


@stream_router.post("/create", response_model=ShowStreamWithHATEOAS, status_code=201)
async def create_stream(body: CreateStream, request: Request, db: AsyncSession = Depends(get_db)):
    return await stream_service._create_new_stream(body, request, db)


@stream_router.get("/search/by_composite_key/{stream_id}/{group_name}/{subject_id}", response_model=ShowStreamWithHATEOAS, responses={404: {"description": "Поток не найден"}})
async def get_stream_by_composite_key(stream_id: int, group_name: str, subject_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await stream_service._get_stream_by_composite_key(stream_id, group_name, subject_id, request, db)


@stream_router.get("/search/by_group/{group_name}", response_model=ShowStreamListWithHATEOAS, responses={404: {"description": "Потоки не найдены"}})
async def get_streams_by_group(group_name: str, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await stream_service._get_streams_by_group(group_name, query_param.page, query_param.limit, request, db)


@stream_router.get("/search/by_subject/{subject_id}", response_model=ShowStreamListWithHATEOAS, responses={404: {"description": "Потоки не найдены"}})
async def get_streams_by_subject(subject_id: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await stream_service._get_streams_by_subject(subject_id, query_param.page, query_param.limit, request, db)


@stream_router.get("/search", response_model=ShowStreamListWithHATEOAS)
async def get_all_streams(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await stream_service._get_all_streams(query_param.page, query_param.limit, request, db)


@stream_router.delete("/delete/{stream_id}/{group_name}/{subject_id}", response_model=ShowStreamWithHATEOAS, responses={404: {"description": "Поток не найден"}})
async def delete_stream(stream_id: int, group_name: str, subject_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await stream_service._delete_stream(stream_id, group_name, subject_id, request, db)


@stream_router.put("/update", response_model=ShowStreamWithHATEOAS, responses={404: {"description": "Поток не найден"}})
async def update_stream(body: UpdateStream, request: Request, db: AsyncSession = Depends(get_db)):
    return await stream_service._update_stream(body, request, db)
