from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from api.chapter.chapter_pydantic  import *
from api.models import QueryParams
from db.session import get_db
from api.chapter.chapter_services import ChapterService

chapter_router = APIRouter()

chapter_service = ChapterService()


@chapter_router.post("/create", response_model=ShowChapterWithHATEOAS, status_code=201)
async def create_chapter(body: CreateChapter, request: Request, db: AsyncSession = Depends(get_db)):
    return await chapter_service._create_new_chapter(body, request, db)


@chapter_router.get("/search/by_id/{chapter_id}", response_model=ShowChapterWithHATEOAS, responses={404: {"description": "Раздел не найден"}})
async def get_chapter_by_id(chapter_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await chapter_service._get_chapter_by_id(chapter_id, request, db)


@chapter_router.get("/search/by_plan/{plan_id}", response_model=ShowChapterListWithHATEOAS, responses={404: {"description": "Главы не найдены"}})
async def get_chapters_by_plan(plan_id: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await chapter_service._get_chapters_by_plan(plan_id, query_param.page, query_param.limit, request, db)


@chapter_router.get("/search", response_model=ShowChapterListWithHATEOAS)
async def get_all_chapters(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await chapter_service._get_all_chapters(query_param.page, query_param.limit, request, db)


@chapter_router.delete("/delete/{chapter_id}", response_model=ShowChapterWithHATEOAS, responses={404: {"description": "Раздел не найден"}})
async def delete_chapter(chapter_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await chapter_service._delete_chapter(chapter_id, request, db)


@chapter_router.put("/update", response_model=ShowChapterWithHATEOAS, responses={404: {"description": "Раздел не найден"}})
async def update_chapter(body: UpdateChapter, request: Request, db: AsyncSession = Depends(get_db)):
    return await chapter_service._update_chapter(body, request, db)
