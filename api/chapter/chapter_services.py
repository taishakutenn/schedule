from api.chapter.chapter_pydantic import *
from api.services_helpers import ensure_chapter_exists, ensure_plan_exists
from api.chapter.chapter_DAL import ChapterDAL
from api.plan.plan_DAL import PlanDAL
from fastapi import HTTPException, Request

from config.logging_config import configure_logging

# Create logger object
logger = configure_logging()


class ChapterService:
    async def _create_new_chapter(self, body: CreateChapter, request: Request, db) -> ShowChapterWithHATEOAS:
        async with db as session:
            async with session.begin():
                plan_dal = PlanDAL(session)
                chapter_dal = ChapterDAL(session)
                try:
                    if not await ensure_plan_exists(plan_dal, body.plan_id):
                        raise HTTPException(status_code=404, detail=f"Учебный план с id {body.plan_id} не найден")

                    chapter = await chapter_dal.create_chapter(
                        code=body.code,
                        name=body.name,
                        plan_id=body.plan_id
                    )
                    chapter_id = chapter.id
                    chapter_pydantic = ShowChapter.model_validate(chapter, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/chapters/search/by_id/{chapter_id}',
                        "update": f'{api_base_url}/chapters/update',
                        "delete": f'{api_base_url}/chapters/delete/{chapter_id}',
                        "chapters": f'{api_base_url}/chapters',
                        "plan": f'{api_base_url}/plans/search/by_id/{body.plan_id}',
                        "cycles": f'{api_base_url}/cycles/search/by_chapter/{chapter_id}'
                    }

                    return ShowChapterWithHATEOAS(chapter=chapter_pydantic, links=hateoas_links)

                except HTTPException:
                    await session.rollback()
                    raise
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Неожиданная ошибка при создании главы '{body.name}' в плане {body.plan_id}: {e}", exc_info=True)
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_chapter_by_id(self, chapter_id: int, request: Request, db) -> ShowChapterWithHATEOAS:
        async with db as session:
            async with session.begin():
                chapter_dal = ChapterDAL(session)
                try:
                    chapter = await chapter_dal.get_chapter_by_id(chapter_id)
                    if not chapter:
                        raise HTTPException(status_code=404, detail=f"Раздел с id {chapter_id} не найден")
                    chapter_pydantic = ShowChapter.model_validate(chapter, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/chapters/search/by_id/{chapter_id}',
                        "update": f'{api_base_url}/chapters/update',
                        "delete": f'{api_base_url}/chapters/delete/{chapter_id}',
                        "chapters": f'{api_base_url}/chapters',
                        "plan": f'{api_base_url}/plans/search/by_id/{chapter.plan_id}',
                        "cycles": f'{api_base_url}/cycles/search/by_chapter/{chapter_id}'
                    }

                    return ShowChapterWithHATEOAS(chapter=chapter_pydantic, links=hateoas_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение главы {chapter_id} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_chapters_by_plan(self, plan_id: int, page: int, limit: int, request: Request, db) -> ShowChapterListWithHATEOAS:
        async with db as session:
            async with session.begin():
                plan_dal = PlanDAL(session)
                chapter_dal = ChapterDAL(session)
                try:
                    if not await ensure_plan_exists(plan_dal, plan_id):
                        raise HTTPException(status_code=404, detail=f"Учебный план с id {plan_id} не найден")

                    chapters = await chapter_dal.get_chapters_by_plan(plan_id, page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    chapters_with_hateoas = []
                    for chapter in chapters:
                        chapter_pydantic = ShowChapter.model_validate(chapter, from_attributes=True)
                        chapter_id = chapter.id
                        chapter_links = {
                            "self": f'{api_base_url}/chapters/search/by_id/{chapter_id}',
                            "update": f'{api_base_url}/chapters/update',
                            "delete": f'{api_base_url}/chapters/delete/{chapter_id}',
                            "chapters": f'{api_base_url}/chapters',
                            "plan": f'{api_base_url}/plans/search/by_id/{plan_id}',
                            "cycles": f'{api_base_url}/cycles/search/by_chapter/{chapter_id}'
                        }
                        chapter_with_links = ShowChapterWithHATEOAS(chapter=chapter_pydantic, links=chapter_links)
                        chapters_with_hateoas.append(chapter_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/chapters/search/by_plan/{plan_id}?page={page}&limit={limit}',
                        "create": f'{api_base_url}/chapters/create',
                        "plan": f'{api_base_url}/plans/search/by_id/{plan_id}'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowChapterListWithHATEOAS(chapters=chapters_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение глав для плана {plan_id} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_all_chapters(self, page: int, limit: int, request: Request, db) -> ShowChapterListWithHATEOAS:
        async with db as session:
            async with session.begin():
                chapter_dal = ChapterDAL(session)
                try:
                    chapters = await chapter_dal.get_all_chapters(page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    chapters_with_hateoas = []
                    for chapter in chapters:
                        chapter_pydantic = ShowChapter.model_validate(chapter, from_attributes=True)
                        chapter_id = chapter.id
                        chapter_links = {
                            "self": f'{api_base_url}/chapters/search/by_id/{chapter_id}',
                            "update": f'{api_base_url}/chapters/update',
                            "delete": f'{api_base_url}/chapters/delete/{chapter_id}',
                            "chapters": f'{api_base_url}/chapters',
                            "plan": f'{api_base_url}/plans/search/by_id/{chapter.plan_id}',
                            "cycles": f'{api_base_url}/cycles/search/by_chapter/{chapter_id}'
                        }
                        chapter_with_links = ShowChapterWithHATEOAS(chapter=chapter_pydantic, links=chapter_links)
                        chapters_with_hateoas.append(chapter_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/chapters/search?page={page}&limit={limit}',
                        "create": f'{api_base_url}/chapters/create'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowChapterListWithHATEOAS(chapters=chapters_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение глав отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _delete_chapter(self, chapter_id: int, request: Request, db) -> ShowChapterWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    chapter_dal = ChapterDAL(session)
                    if not await ensure_chapter_exists(chapter_dal, chapter_id):
                        raise HTTPException(status_code=404, detail=f"Раздел с id {chapter_id} не найден")

                    chapter = await chapter_dal.delete_chapter(chapter_id)
                    if not chapter:
                        raise HTTPException(status_code=404, detail=f"Раздел с id {chapter_id} не найден")

                    chapter_pydantic = ShowChapter.model_validate(chapter, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "chapters": f'{api_base_url}/chapters',
                        "create": f'{api_base_url}/chapters/create',
                        "plan": f'{api_base_url}/plans/search/by_id/{chapter.plan_id}'
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowChapterWithHATEOAS(chapter=chapter_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при удалении главы {chapter_id}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении главы.")


    async def _update_chapter(self, body: UpdateChapter, request: Request, db) -> ShowChapterWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["chapter_id"]}
                    if "plan_id" in update_data:
                        plan_id_to_check = update_data["plan_id"]
                        plan_dal = PlanDAL(session)
                        if not await ensure_plan_exists(plan_dal, plan_id_to_check):
                            raise HTTPException(status_code=404, detail=f"Учебный план с id {plan_id_to_check} не найден")

                    chapter_dal = ChapterDAL(session)

                    if not await ensure_chapter_exists(chapter_dal, body.chapter_id):
                        raise HTTPException(status_code=404, detail=f"Раздел с id {body.chapter_id} не найден")

                    chapter = await chapter_dal.update_chapter(target_id=body.chapter_id, **update_data)
                    if not chapter:
                        raise HTTPException(status_code=404, detail=f"Раздел с id {body.chapter_id} не найден")

                    chapter_id = chapter.id
                    chapter_pydantic = ShowChapter.model_validate(chapter, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/chapters/search/by_id/{chapter_id}',
                        "update": f'{api_base_url}/chapters/update',
                        "delete": f'{api_base_url}/chapters/delete/{chapter_id}',
                        "chapters": f'{api_base_url}/chapters',
                        "plan": f'{api_base_url}/plans/search/by_id/{chapter.plan_id}',
                        "cycles": f'{api_base_url}/cycles/search/by_chapter/{chapter_id}'
                    }

                    return ShowChapterWithHATEOAS(chapter=chapter_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.warning(f"Изменение данных о главе отменено (Ошибка: {e})")
                raise e
