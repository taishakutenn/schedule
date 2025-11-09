from api.module.module_pydantic import *
from api.services_helpers import ensure_cycle_contains_modules, ensure_cycle_exists, ensure_module_exists
from api.module.module_DAL import ModuleDAL
from api.cycle.cycle_DAL import CycleDAL
from fastapi import HTTPException, Request

from config.logging_config import configure_logging

# Create logger object
logger = configure_logging()


class ModuleService:
    async def _create_new_module(self, body: CreateModule, request: Request, db) -> ShowModuleWithHATEOAS:
        async with db as session:
            async with session.begin():
                cycle_dal = CycleDAL(session)
                module_dal = ModuleDAL(session)
                try:
                    if not await ensure_cycle_exists(cycle_dal, body.cycle_in_chapter_id):
                        raise HTTPException(status_code=404, detail=f"Цикл с id {body.cycle_in_chapter_id} не найден")

                    if not await ensure_cycle_contains_modules(cycle_dal, body.cycle_in_chapter_id):
                        raise HTTPException(status_code=400, detail=f"Цикл с id {body.cycle_in_chapter_id} не может содержать модули, так как contains_modules = False")

                    module = await module_dal.create_module(
                        name=body.name,
                        code=body.code,
                        cycle_in_chapter_id=body.cycle_in_chapter_id
                    )
                    module_id = module.id
                    module_pydantic = ShowModule.model_validate(module, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/modules/search/by_id/{module_id}',
                        "update": f'{api_base_url}/modules/update',
                        "delete": f'{api_base_url}/modules/delete/{module_id}',
                        "modules": f'{api_base_url}/modules',
                        "cycle": f'{api_base_url}/cycles/search/by_id/{body.cycle_in_chapter_id}',
                        "subjects_in_cycle": f'{api_base_url}/subjects_in_cycles/search/by_module/{module_id}'
                    }

                    return ShowModuleWithHATEOAS(module=module_pydantic, links=hateoas_links)

                except HTTPException:
                    await session.rollback()
                    raise
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Неожиданная ошибка при создании модуля '{body.name}' в цикле {body.cycle_in_chapter_id}: {e}", exc_info=True)
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_module_by_id(self, module_id: int, request: Request, db) -> ShowModuleWithHATEOAS:
        async with db as session:
            async with session.begin():
                module_dal = ModuleDAL(session)
                try:
                    module = await module_dal.get_module_by_id(module_id)
                    if not module:
                        raise HTTPException(status_code=404, detail=f"Модуль с id {module_id} не найден")
                    module_pydantic = ShowModule.model_validate(module, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/modules/search/by_id/{module_id}',
                        "update": f'{api_base_url}/modules/update',
                        "delete": f'{api_base_url}/modules/delete/{module_id}',
                        "modules": f'{api_base_url}/modules',
                        "cycle": f'{api_base_url}/cycles/search/by_id/{module.cycle_in_chapter_id}',
                        "subjects_in_cycle": f'{api_base_url}/subjects_in_cycles/search/by_module/{module_id}'
                    }

                    return ShowModuleWithHATEOAS(module=module_pydantic, links=hateoas_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение модуля {module_id} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_modules_by_cycle(self, cycle_in_chapter_id: int, page: int, limit: int, request: Request, db) -> ShowModuleListWithHATEOAS:
        async with db as session:
            async with session.begin():
                cycle_dal = CycleDAL(session)
                module_dal = ModuleDAL(session)
                try:
                    if not await ensure_cycle_exists(cycle_dal, cycle_in_chapter_id):
                        raise HTTPException(status_code=404, detail=f"Цикл с id {cycle_in_chapter_id} не найден")

                    modules = await module_dal.get_modules_by_cycle(cycle_in_chapter_id, page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    modules_with_hateoas = []
                    for module in modules:
                        module_pydantic = ShowModule.model_validate(module, from_attributes=True)
                        module_id = module.id
                        module_links = {
                            "self": f'{api_base_url}/modules/search/by_id/{module_id}',
                            "update": f'{api_base_url}/modules/update',
                            "delete": f'{api_base_url}/modules/delete/{module_id}',
                            "modules": f'{api_base_url}/modules',
                            "cycle": f'{api_base_url}/cycles/search/by_id/{cycle_in_chapter_id}',
                            "subjects_in_cycle": f'{api_base_url}/subjects_in_cycles/search/by_module/{module_id}'
                        }
                        module_with_links = ShowModuleWithHATEOAS(module=module_pydantic, links=module_links)
                        modules_with_hateoas.append(module_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/modules/search/by_cycle/{cycle_in_chapter_id}?page={page}&limit={limit}',
                        "create": f'{api_base_url}/modules/create',
                        "cycle": f'{api_base_url}/cycles/search/by_id/{cycle_in_chapter_id}'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowModuleListWithHATEOAS(modules=modules_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение модулей для цикла {cycle_in_chapter_id} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_all_modules(self, page: int, limit: int, request: Request, db) -> ShowModuleListWithHATEOAS:
        async with db as session:
            async with session.begin():
                module_dal = ModuleDAL(session)
                try:
                    modules = await module_dal.get_all_modules(page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    modules_with_hateoas = []
                    for module in modules:
                        module_pydantic = ShowModule.model_validate(module, from_attributes=True)
                        module_id = module.id
                        module_links = {
                            "self": f'{api_base_url}/modules/search/by_id/{module_id}',
                            "update": f'{api_base_url}/modules/update',
                            "delete": f'{api_base_url}/modules/delete/{module_id}',
                            "modules": f'{api_base_url}/modules',
                            "cycle": f'{api_base_url}/cycles/search/by_id/{module.cycle_in_chapter_id}',
                            "subjects_in_cycle": f'{api_base_url}/subjects_in_cycles/search/by_module/{module_id}'
                        }
                        module_with_links = ShowModuleWithHATEOAS(module=module_pydantic, links=module_links)
                        modules_with_hateoas.append(module_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/modules/search?page={page}&limit={limit}',
                        "create": f'{api_base_url}/modules/create'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowModuleListWithHATEOAS(modules=modules_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение модулей отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _delete_module(self, module_id: int, request: Request, db) -> ShowModuleWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    module_dal = ModuleDAL(session)
                    if not await ensure_module_exists(module_dal, module_id):
                        raise HTTPException(status_code=404, detail=f"Модуль с id {module_id} не найден")

                    module = await module_dal.delete_module(module_id)
                    if not module:
                        raise HTTPException(status_code=404, detail=f"Модуль с id {module_id} не найден")

                    module_pydantic = ShowModule.model_validate(module, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "modules": f'{api_base_url}/modules',
                        "create": f'{api_base_url}/modules/create',
                        "cycle": f'{api_base_url}/cycles/search/by_id/{module.cycle_in_chapter_id}'
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowModuleWithHATEOAS(module=module_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при удалении модуля {module_id}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении модуля.")


    async def _update_module(self, body: UpdateModule, request: Request, db) -> ShowModuleWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["module_id"]}

                    if "cycle_in_chapter_id" in update_data:
                        cycle_id_to_check = update_data["cycle_in_chapter_id"]
                        cycle_dal = CycleDAL(session)
                        if not await ensure_cycle_exists(cycle_dal, cycle_id_to_check):
                            raise HTTPException(status_code=404, detail=f"Цикл с id {cycle_id_to_check} не найден")

                    module_dal = ModuleDAL(session)

                    if not await ensure_module_exists(module_dal, body.module_id):
                        raise HTTPException(status_code=404, detail=f"Модуль с id {body.module_id} не найден")

                    module = await module_dal.update_module(target_id=body.module_id, **update_data)
                    if not module:
                        raise HTTPException(status_code=404, detail=f"Модуль с id {body.module_id} не найден")

                    module_id = module.id 
                    module_pydantic = ShowModule.model_validate(module, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/modules/search/by_id/{module_id}',
                        "update": f'{api_base_url}/modules/update',
                        "delete": f'{api_base_url}/modules/delete/{module_id}',
                        "modules": f'{api_base_url}/modules',
                        "cycle": f'{api_base_url}/cycles/search/by_id/{module.cycle_in_chapter_id}',
                        "subjects_in_cycle": f'{api_base_url}/subjects_in_cycles/search/by_module/{module_id}'
                    }

                    return ShowModuleWithHATEOAS(module=module_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.warning(f"Изменение данных о модуле отменено (Ошибка: {e})")
                raise e
