from api.cycle.cycle_pydantic import *
from api.services_helpers import ensure_chapter_exists, ensure_cycle_exists
from api.cycle.cycle_DAL import CycleDAL
from api.chapter.chapter_DAL import ChapterDAL
from fastapi import HTTPException, Request

from config.logging_config import configure_logging

# Create logger object
logger = configure_logging()


class CycleService:
    async def _create_new_cycle(self, body: CreateCycle, request: Request, db) -> ShowCycleWithHATEOAS:
        async with db as session:
            async with session.begin():
                chapter_dal = ChapterDAL(session)
                cycle_dal = CycleDAL(session)
                try:
                    if not await ensure_chapter_exists(chapter_dal, body.chapter_in_plan_id):
                        raise HTTPException(status_code=404, detail=f"Раздел с id {body.chapter_in_plan_id} не найдена")

                    cycle = await cycle_dal.create_cycle(
                        contains_modules=body.contains_modules,
                        code=body.code,
                        name=body.name,
                        chapter_in_plan_id=body.chapter_in_plan_id
                    )
                    cycle_id = cycle.id 
                    cycle_pydantic = ShowCycle.model_validate(cycle, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/cycles/search/by_id/{cycle_id}',
                        "update": f'{api_base_url}/cycles/update',
                        "delete": f'{api_base_url}/cycles/delete/{cycle_id}',
                        "cycles": f'{api_base_url}/cycles',
                        "chapter": f'{api_base_url}/chapters/search/by_id/{body.chapter_in_plan_id}',
                        "modules": f'{api_base_url}/modules/search/by_cycle/{cycle_id}',
                        "subjects_in_cycle": f'{api_base_url}/subjects_in_cycles/search/by_cycle/{cycle_id}'
                    }

                    return ShowCycleWithHATEOAS(cycle=cycle_pydantic, links=hateoas_links)

                except HTTPException:
                    await session.rollback()
                    raise
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Неожиданная ошибка при создании цикла '{body.name}' в разделе {body.chapter_in_plan_id}: {e}", exc_info=True)
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_cycle_by_id(self, cycle_id: int, request: Request, db) -> ShowCycleWithHATEOAS:
        async with db as session:
            async with session.begin():
                cycle_dal = CycleDAL(session)
                try:
                    cycle = await cycle_dal.get_cycle_by_id(cycle_id)
                    if not cycle:
                        raise HTTPException(status_code=404, detail=f"Цикл с id {cycle_id} не найден")
                    cycle_pydantic = ShowCycle.model_validate(cycle, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/cycles/search/by_id/{cycle_id}',
                        "update": f'{api_base_url}/cycles/update',
                        "delete": f'{api_base_url}/cycles/delete/{cycle_id}',
                        "cycles": f'{api_base_url}/cycles',
                        "chapter": f'{api_base_url}/chapters/search/by_id/{cycle.chapter_in_plan_id}',
                        "modules": f'{api_base_url}/modules/search/by_cycle/{cycle_id}',
                        "subjects_in_cycle": f'{api_base_url}/subjects_in_cycles/search/by_cycle/{cycle_id}'
                    }

                    return ShowCycleWithHATEOAS(cycle=cycle_pydantic, links=hateoas_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение цикла {cycle_id} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_cycles_by_chapter(self, chapter_in_plan_id: int, page: int, limit: int, request: Request, db) -> ShowCycleListWithHATEOAS:
        async with db as session:
            async with session.begin():
                chapter_dal = ChapterDAL(session)
                cycle_dal = CycleDAL(session)
                try:
                    if not await ensure_chapter_exists(chapter_dal, chapter_in_plan_id):
                        raise HTTPException(status_code=404, detail=f"Глава с id {chapter_in_plan_id} не найдена")

                    cycles = await cycle_dal.get_cycles_by_chapter(chapter_in_plan_id, page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    cycles_with_hateoas = []
                    for cycle in cycles:
                        cycle_pydantic = ShowCycle.model_validate(cycle, from_attributes=True)
                        cycle_id = cycle.id
                        cycle_links = {
                            "self": f'{api_base_url}/cycles/search/by_id/{cycle_id}',
                            "update": f'{api_base_url}/cycles/update',
                            "delete": f'{api_base_url}/cycles/delete/{cycle_id}',
                            "cycles": f'{api_base_url}/cycles',
                            "chapter": f'{api_base_url}/chapters/search/by_id/{chapter_in_plan_id}',
                            "modules": f'{api_base_url}/modules/search/by_cycle/{cycle_id}',
                            "subjects_in_cycle": f'{api_base_url}/subjects_in_cycles/search/by_cycle/{cycle_id}'
                        }
                        cycle_with_links = ShowCycleWithHATEOAS(cycle=cycle_pydantic, links=cycle_links)
                        cycles_with_hateoas.append(cycle_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/cycles/search/by_chapter/{chapter_in_plan_id}?page={page}&limit={limit}',
                        "create": f'{api_base_url}/cycles/create',
                        "chapter": f'{api_base_url}/chapters/search/by_id/{chapter_in_plan_id}'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowCycleListWithHATEOAS(cycles=cycles_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение циклов для раздела {chapter_in_plan_id} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_all_cycles(self, page: int, limit: int, request: Request, db) -> ShowCycleListWithHATEOAS:
        async with db as session:
            async with session.begin():
                cycle_dal = CycleDAL(session)
                try:
                    cycles = await cycle_dal.get_all_cycles(page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    cycles_with_hateoas = []
                    for cycle in cycles:
                        cycle_pydantic = ShowCycle.model_validate(cycle, from_attributes=True)
                        cycle_id = cycle.id
                        cycle_links = {
                            "self": f'{api_base_url}/cycles/search/by_id/{cycle_id}',
                            "update": f'{api_base_url}/cycles/update',
                            "delete": f'{api_base_url}/cycles/delete/{cycle_id}',
                            "cycles": f'{api_base_url}/cycles',
                            "chapter": f'{api_base_url}/chapters/search/by_id/{cycle.chapter_in_plan_id}',
                            "modules": f'{api_base_url}/modules/search/by_cycle/{cycle_id}',
                            "subjects_in_cycle": f'{api_base_url}/subjects_in_cycles/search/by_cycle/{cycle_id}'
                        }
                        cycle_with_links = ShowCycleWithHATEOAS(cycle=cycle_pydantic, links=cycle_links)
                        cycles_with_hateoas.append(cycle_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/cycles/search?page={page}&limit={limit}',
                        "create": f'{api_base_url}/cycles/create'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowCycleListWithHATEOAS(cycles=cycles_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение циклов отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _delete_cycle(self, cycle_id: int, request: Request, db) -> ShowCycleWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    cycle_dal = CycleDAL(session)
                    if not await ensure_cycle_exists(cycle_dal, cycle_id):
                        raise HTTPException(status_code=404, detail=f"Цикл с id {cycle_id} не найден")

                    cycle = await cycle_dal.delete_cycle(cycle_id)

                    if not cycle:
                        raise HTTPException(status_code=404, detail=f"Цикл с id {cycle_id} не найден")

                    cycle_pydantic = ShowCycle.model_validate(cycle, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "cycles": f'{api_base_url}/cycles',
                        "create": f'{api_base_url}/cycles/create',
                        "chapter": f'{api_base_url}/chapters/search/by_id/{cycle.chapter_in_plan_id}'
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowCycleWithHATEOAS(cycle=cycle_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при удалении цикла {cycle_id}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении цикла.")


    async def _update_cycle(self, body: UpdateCycle, request: Request, db) -> ShowCycleWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["cycle_id"]}
                    
                    if "chapter_in_plan_id" in update_data:
                        chapter_id_to_check = update_data["chapter_in_plan_id"]
                        chapter_dal = ChapterDAL(session)
                        if not await ensure_chapter_exists(chapter_dal, chapter_id_to_check):
                            raise HTTPException(status_code=404, detail=f"Глава с id {chapter_id_to_check} не найдена")

                    cycle_dal = CycleDAL(session)

                    if not await ensure_cycle_exists(cycle_dal, body.cycle_id):
                        raise HTTPException(status_code=404, detail=f"Цикл с id {body.cycle_id} не найден")

                    cycle = await cycle_dal.update_cycle(target_id=body.cycle_id, **update_data)
                    if not cycle:
                        raise HTTPException(status_code=404, detail=f"Цикл с id {body.cycle_id} не найден")

                    cycle_id = cycle.id
                    cycle_pydantic = ShowCycle.model_validate(cycle, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/cycles/search/by_id/{cycle_id}',
                        "update": f'{api_base_url}/cycles/update',
                        "delete": f'{api_base_url}/cycles/delete/{cycle_id}',
                        "cycles": f'{api_base_url}/cycles',
                        "chapter": f'{api_base_url}/chapters/search/by_id/{cycle.chapter_in_plan_id}',
                        "modules": f'{api_base_url}/modules/search/by_cycle/{cycle_id}',
                        "subjects_in_cycle": f'{api_base_url}/subjects_in_cycles/search/by_cycle/{cycle_id}'
                    }

                    return ShowCycleWithHATEOAS(cycle=cycle_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.warning(f"Изменение данных о цикле отменено (Ошибка: {e})")
                raise e
