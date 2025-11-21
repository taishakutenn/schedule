from api.subject_in_cycle.subject_in_cycle_pydantic import *
from api.services_helpers import ensure_cycle_exists, ensure_module_exists, ensure_subject_in_cycle_exists
from api.subject_in_cycle.subject_in_cycle_DAL import SubjectsInCycleDAL
from api.module.module_DAL import ModuleDAL
from api.cycle.cycle_DAL import CycleDAL
from fastapi import HTTPException, Request

from config.logging_config import configure_logging

# Create logger object
logger = configure_logging()


class SubjectInCycleService:
    async def _create_new_subject_in_cycle(self, body: CreateSubjectsInCycle, request: Request, db) -> ShowSubjectsInCycleWithHATEOAS:
        async with db as session:
            async with session.begin():
                cycle_dal = CycleDAL(session)
                module_dal = ModuleDAL(session)
                subject_in_cycle_dal = SubjectsInCycleDAL(session)
                try:
                    if body.cycle_in_chapter_id is not None:
                        if not await ensure_cycle_exists(cycle_dal, body.cycle_in_chapter_id):
                            raise HTTPException(status_code=404, detail=f"Цикл с id {body.cycle_in_chapter_id} не найден")

                    if body.module_in_cycle_id is not None:
                        if not await ensure_module_exists(module_dal, body.module_in_cycle_id):
                            raise HTTPException(status_code=404, detail=f"Модуль с id {body.module_in_cycle_id} не найден")
                        if body.cycle_in_chapter_id is not None:
                            module_obj = await module_dal.get_module_by_id(body.module_in_cycle_id)
                            if module_obj.cycle_in_chapter_id != body.cycle_in_chapter_id:
                                raise HTTPException(status_code=400, detail=f"Модуль с id {body.module_in_cycle_id} не принадлежит циклу с id {body.cycle_in_chapter_id}")
                    
                    subject_in_cycle = await subject_in_cycle_dal.create_subject_in_cycle(
                        code=body.code,
                        title=body.title,
                        cycle_in_chapter_id=body.cycle_in_chapter_id,
                        module_in_cycle_id=body.module_in_cycle_id
                    )
                    subject_in_cycle_id = subject_in_cycle.id 
                    subject_in_cycle_pydantic = ShowSubjectsInCycle.model_validate(subject_in_cycle, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_in_cycle_id}',
                        "update": f'{api_base_url}/subjects_in_cycles/update',
                        "delete": f'{api_base_url}/subjects_in_cycles/delete/{subject_in_cycle_id}',
                        "subjects_in_cycles": f'{api_base_url}/subjects_in_cycles',
                        "cycle": f'{api_base_url}/cycles/search/by_id/{body.cycle_in_chapter_id}',
                        "module": f'{api_base_url}/modules/search/by_id/{body.module_in_cycle_id}' if body.module_in_cycle_id else None,
                        "hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_subject_in_cycle/{subject_in_cycle_id}',
                        "streams": f'{api_base_url}/streams/search/by_subject_in_cycle/{subject_in_cycle_id}'
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowSubjectsInCycleWithHATEOAS(subject_in_cycle=subject_in_cycle_pydantic, links=hateoas_links)

                except HTTPException:
                    await session.rollback()
                    raise
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Неожиданная ошибка при создании предмета '{body.title}' в цикле {body.cycle_in_chapter_id}: {e}", exc_info=True)
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_subject_in_cycle_by_id(self, subject_in_cycle_id: int, request: Request, db) -> ShowSubjectsInCycleWithHATEOAS:
        async with db as session:
            async with session.begin():
                subject_in_cycle_dal = SubjectsInCycleDAL(session)
                try:
                    subject_in_cycle = await subject_in_cycle_dal.get_subject_in_cycle_by_id(subject_in_cycle_id)
                    if not subject_in_cycle:
                        raise HTTPException(status_code=404, detail=f"Предмет в цикле с id {subject_in_cycle_id} не найден")
                    subject_in_cycle_pydantic = ShowSubjectsInCycle.model_validate(subject_in_cycle, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_in_cycle_id}',
                        "update": f'{api_base_url}/subjects_in_cycles/update',
                        "delete": f'{api_base_url}/subjects_in_cycles/delete/{subject_in_cycle_id}',
                        "subjects_in_cycles": f'{api_base_url}/subjects_in_cycles',
                        "cycle": f'{api_base_url}/cycles/search/by_id/{subject_in_cycle.cycle_in_chapter_id}',
                        "module": f'{api_base_url}/modules/search/by_id/{subject_in_cycle.module_in_cycle_id}' if subject_in_cycle.module_in_cycle_id else None,
                        "hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_subject_in_cycle/{subject_in_cycle_id}',
                        "streams": f'{api_base_url}/streams/search/by_subject_in_cycle/{subject_in_cycle_id}'
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowSubjectsInCycleWithHATEOAS(subject_in_cycle=subject_in_cycle_pydantic, links=hateoas_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение предмета в цикле {subject_in_cycle_id} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_subjects_in_cycle_by_cycle(self, cycle_in_chapter_id: int, page: int, limit: int, request: Request, db) -> ShowSubjectsInCycleListWithHATEOAS:
        async with db as session:
            async with session.begin():
                cycle_dal = CycleDAL(session)
                subject_in_cycle_dal = SubjectsInCycleDAL(session)
                try:
                    if not await ensure_cycle_exists(cycle_dal, cycle_in_chapter_id):
                        raise HTTPException(status_code=404, detail=f"Цикл с id {cycle_in_chapter_id} не найден")

                    subjects_in_cycles = await subject_in_cycle_dal.get_subjects_in_cycle_by_cycle(cycle_in_chapter_id, page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    subjects_in_cycles_with_hateoas = []
                    for subject_in_cycle in subjects_in_cycles:
                        subject_in_cycle_pydantic = ShowSubjectsInCycle.model_validate(subject_in_cycle, from_attributes=True)
                        subject_in_cycle_id = subject_in_cycle.id
                        subject_in_cycle_links = {
                            "self": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_in_cycle_id}',
                            "update": f'{api_base_url}/subjects_in_cycles/update',
                            "delete": f'{api_base_url}/subjects_in_cycles/delete/{subject_in_cycle_id}',
                            "subjects_in_cycles": f'{api_base_url}/subjects_in_cycles',
                            "cycle": f'{api_base_url}/cycles/search/by_id/{cycle_in_chapter_id}',
                            "module": f'{api_base_url}/modules/search/by_id/{subject_in_cycle.module_in_cycle_id}' if subject_in_cycle.module_in_cycle_id else None,
                            "hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_subject_in_cycle/{subject_in_cycle_id}',
                            "streams": f'{api_base_url}/streams/search/by_subject_in_cycle/{subject_in_cycle_id}'
                        }
                        subject_in_cycle_links = {k: v for k, v in subject_in_cycle_links.items() if v is not None}
                        subject_in_cycle_with_links = ShowSubjectsInCycleWithHATEOAS(subject_in_cycle=subject_in_cycle_pydantic, links=subject_in_cycle_links)
                        subjects_in_cycles_with_hateoas.append(subject_in_cycle_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/subjects_in_cycles/search/by_cycle/{cycle_in_chapter_id}?page={page}&limit={limit}',
                        "create": f'{api_base_url}/subjects_in_cycles/create',
                        "cycle": f'{api_base_url}/cycles/search/by_id/{cycle_in_chapter_id}'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowSubjectsInCycleListWithHATEOAS(subjects_in_cycles=subjects_in_cycles_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение предметов в цикле для цикла {cycle_in_chapter_id} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_subjects_in_cycle_by_module(self, module_in_cycle_id: int, page: int, limit: int, request: Request, db) -> ShowSubjectsInCycleListWithHATEOAS:
        async with db as session:
            async with session.begin():
                module_dal = ModuleDAL(session)
                subject_in_cycle_dal = SubjectsInCycleDAL(session)
                try:
                    if not await ensure_module_exists(module_dal, module_in_cycle_id):
                        raise HTTPException(status_code=404, detail=f"Модуль с id {module_in_cycle_id} не найден")

                    subjects_in_cycles = await subject_in_cycle_dal.get_subjects_in_cycle_by_module(module_in_cycle_id, page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    subjects_in_cycles_with_hateoas = []
                    for subject_in_cycle in subjects_in_cycles:
                        subject_in_cycle_pydantic = ShowSubjectsInCycle.model_validate(subject_in_cycle, from_attributes=True)
                        subject_in_cycle_id = subject_in_cycle.id
                        subject_in_cycle_links = {
                            "self": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_in_cycle_id}',
                            "update": f'{api_base_url}/subjects_in_cycles/update',
                            "delete": f'{api_base_url}/subjects_in_cycles/delete/{subject_in_cycle_id}',
                            "subjects_in_cycles": f'{api_base_url}/subjects_in_cycles',
                            "cycle": f'{api_base_url}/cycles/search/by_id/{subject_in_cycle.cycle_in_chapter_id}',
                            "module": f'{api_base_url}/modules/search/by_id/{module_in_cycle_id}',
                            "hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_subject_in_cycle/{subject_in_cycle_id}',
                            "streams": f'{api_base_url}/streams/search/by_subject_in_cycle/{subject_in_cycle_id}'
                        }
                        subject_in_cycle_links = {k: v for k, v in subject_in_cycle_links.items() if v is not None}
                        subject_in_cycle_with_links = ShowSubjectsInCycleWithHATEOAS(subject_in_cycle=subject_in_cycle_pydantic, links=subject_in_cycle_links)
                        subjects_in_cycles_with_hateoas.append(subject_in_cycle_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/subjects_in_cycles/search/by_module/{module_in_cycle_id}?page={page}&limit={limit}',
                        "create": f'{api_base_url}/subjects_in_cycles/create',
                        "module": f'{api_base_url}/modules/search/by_id/{module_in_cycle_id}'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowSubjectsInCycleListWithHATEOAS(subjects_in_cycles=subjects_in_cycles_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение предметов в цикле для модуля {module_in_cycle_id} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_all_subjects_in_cycles(self, page: int, limit: int, request: Request, db) -> ShowSubjectsInCycleListWithHATEOAS:
        async with db as session:
            async with session.begin():
                subject_in_cycle_dal = SubjectsInCycleDAL(session)
                try:
                    subjects_in_cycles = await subject_in_cycle_dal.get_all_subjects_in_cycles(page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    subjects_in_cycles_with_hateoas = []
                    for subject_in_cycle in subjects_in_cycles:
                        subject_in_cycle_pydantic = ShowSubjectsInCycle.model_validate(subject_in_cycle, from_attributes=True)
                        subject_in_cycle_id = subject_in_cycle.id
                        subject_in_cycle_links = {
                            "self": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_in_cycle_id}',
                            "update": f'{api_base_url}/subjects_in_cycles/update',
                            "delete": f'{api_base_url}/subjects_in_cycles/delete/{subject_in_cycle_id}',
                            "subjects_in_cycles": f'{api_base_url}/subjects_in_cycles',
                            "cycle": f'{api_base_url}/cycles/search/by_id/{subject_in_cycle.cycle_in_chapter_id}',
                            "module": f'{api_base_url}/modules/search/by_id/{subject_in_cycle.module_in_cycle_id}' if subject_in_cycle.module_in_cycle_id else None,
                            "hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_subject_in_cycle/{subject_in_cycle_id}',
                            "streams": f'{api_base_url}/streams/search/by_subject_in_cycle/{subject_in_cycle_id}'
                        }
                        subject_in_cycle_links = {k: v for k, v in subject_in_cycle_links.items() if v is not None}
                        subject_in_cycle_with_links = ShowSubjectsInCycleWithHATEOAS(subject_in_cycle=subject_in_cycle_pydantic, links=subject_in_cycle_links)
                        subjects_in_cycles_with_hateoas.append(subject_in_cycle_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/subjects_in_cycles/search?page={page}&limit={limit}',
                        "create": f'{api_base_url}/subjects_in_cycles/create'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowSubjectsInCycleListWithHATEOAS(subjects_in_cycles=subjects_in_cycles_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение предметов в цикле отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _delete_subject_in_cycle(self, subject_in_cycle_id: int, request: Request, db) -> ShowSubjectsInCycleWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    subject_in_cycle_dal = SubjectsInCycleDAL(session)

                    if not await ensure_subject_in_cycle_exists(subject_in_cycle_dal, subject_in_cycle_id):
                        raise HTTPException(status_code=404, detail=f"Предмет в цикле с id {subject_in_cycle_id} не найден")

                    subject_in_cycle = await subject_in_cycle_dal.delete_subject_in_cycle(subject_in_cycle_id)

                    if not subject_in_cycle:
                        raise HTTPException(status_code=404, detail=f"Предмет в цикле с id {subject_in_cycle_id} не найден")

                    subject_in_cycle_pydantic = ShowSubjectsInCycle.model_validate(subject_in_cycle, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "subjects_in_cycles": f'{api_base_url}/subjects_in_cycles',
                        "create": f'{api_base_url}/subjects_in_cycles/create',
                        "cycle": f'{api_base_url}/cycles/search/by_id/{subject_in_cycle.cycle_in_chapter_id}',
                        "module": f'{api_base_url}/modules/search/by_id/{subject_in_cycle.module_in_cycle_id}' if subject_in_cycle.module_in_cycle_id else None
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowSubjectsInCycleWithHATEOAS(subject_in_cycle=subject_in_cycle_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при удалении предмета в цикле {subject_in_cycle_id}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении предмета в цикле.")
            
            
    async def _get_subjects_in_cycle_by_ids(self, ids: list[int], page: int, limit: int, request: Request, db) -> ShowSubjectsInCycleListWithHATEOAS:
        async with db as session:
            async with session.begin():
                subject_in_cycle_dal = SubjectsInCycleDAL(session)
                try:
                    subjects_in_cycle_list = await subject_in_cycle_dal.get_subjects_in_cycle_by_ids(ids, page, limit)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    subjects_in_cycles_with_hateoas = []
                    for subject_in_cycle in subjects_in_cycle_list:
                        subject_in_cycle_pydantic = ShowSubjectsInCycle.model_validate(subject_in_cycle, from_attributes=True)
                        subject_in_cycle_id = subject_in_cycle.id
                        subject_in_cycle_links = {
                            "self": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_in_cycle_id}',
                            "cycle": f'{api_base_url}/cycles/search/by_id/{subject_in_cycle.cycle_in_chapter_id}',
                            "module": f'{api_base_url}/modules/search/by_id/{subject_in_cycle.module_in_cycle_id}' if subject_in_cycle.module_in_cycle_id else None, 
                        }
                        subject_in_cycle_links = {k: v for k, v in subject_in_cycle_links.items() if v is not None}
                        subject_in_cycle_with_links = ShowSubjectsInCycleWithHATEOAS(subject_in_cycle=subject_in_cycle_pydantic, links=subject_in_cycle_links)
                        subjects_in_cycles_with_hateoas.append(subject_in_cycle_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/subjects_in_cycles/search/by_ids?page={page}&limit={limit}&ids={",".join(map(str, ids))}',
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowSubjectsInCycleListWithHATEOAS(subjects_in_cycles=subjects_in_cycles_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение записей предметов в цикле по списку id отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _update_subject_in_cycle(self, body: UpdateSubjectsInCycle, request: Request, db) -> ShowSubjectsInCycleWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["subject_in_cycle_id"]}
                    if "module_in_cycle_id" in update_data:
                        module_id_to_check = update_data["module_in_cycle_id"]
                        if module_id_to_check is not None:
                            module_dal = ModuleDAL(session)
                            cycle_id_to_check = update_data.get("cycle_in_chapter_id", body.cycle_in_chapter_id)
                            module_obj = await module_dal.get_module_by_id(module_id_to_check)

                            if module_obj.cycle_in_chapter_id != cycle_id_to_check:
                                raise HTTPException(status_code=400, detail=f"Модуль с id {module_id_to_check} не принадлежит циклу с id {cycle_id_to_check}")
                        else:
                            cycle_id_to_check = update_data.get("cycle_in_chapter_id", body.cycle_in_chapter_id)

                    elif "cycle_in_chapter_id" in update_data:
                        if update_data.get("module_in_cycle_id") is None:
                            cycle_id_to_check = update_data["cycle_in_chapter_id"]
                            
                            
                    subject_in_cycle_dal = SubjectsInCycleDAL(session)

                    if not await ensure_subject_in_cycle_exists(subject_in_cycle_dal, body.subject_in_cycle_id):
                        raise HTTPException(status_code=404, detail=f"Предмет в цикле с id {body.subject_in_cycle_id} не найден")

                    subject_in_cycle = await subject_in_cycle_dal.update_subject_in_cycle(target_id=body.subject_in_cycle_id, **update_data)
                    if not subject_in_cycle:
                        raise HTTPException(status_code=404, detail=f"Предмет в цикле с id {body.subject_in_cycle_id} не найден")

                    subject_in_cycle_id = subject_in_cycle.id 
                    subject_in_cycle_pydantic = ShowSubjectsInCycle.model_validate(subject_in_cycle, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_in_cycle_id}',
                        "update": f'{api_base_url}/subjects_in_cycles/update',
                        "delete": f'{api_base_url}/subjects_in_cycles/delete/{subject_in_cycle_id}',
                        "subjects_in_cycles": f'{api_base_url}/subjects_in_cycles',
                        "cycle": f'{api_base_url}/cycles/search/by_id/{subject_in_cycle.cycle_in_chapter_id}',
                        "module": f'{api_base_url}/modules/search/by_id/{subject_in_cycle.module_in_cycle_id}' if subject_in_cycle.module_in_cycle_id else None,
                        "hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_subject_in_cycle/{subject_in_cycle_id}',
                        "streams": f'{api_base_url}/streams/search/by_subject_in_cycle/{subject_in_cycle_id}'
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowSubjectsInCycleWithHATEOAS(subject_in_cycle=subject_in_cycle_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.warning(f"Изменение данных о предмете в цикле отменено (Ошибка: {e})")
                raise e
            