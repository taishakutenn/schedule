from api.subject_in_cycle_hours.subject_in_cycle_hours_pydantic import *
from api.services_helpers import ensure_subject_in_cycle_exists, ensure_subject_in_cycle_hours_exists
from api.subject_in_cycle_hours.subject_in_cycle_hours_DAL import SubjectsInCycleHoursDAL
from api.subject_in_cycle.subject_in_cycle_DAL import SubjectsInCycleDAL
from fastapi import HTTPException, Request

from config.logging_config import configure_logging

# Create logger object
logger = configure_logging()


class SubjectInCycleHoursService:
    async def _create_new_subject_in_cycle_hours(self, body: CreateSubjectsInCycleHours, request: Request, db) -> ShowSubjectsInCycleHoursWithHATEOAS:
        async with db as session:
            async with session.begin():
                subject_in_cycle_dal = SubjectsInCycleDAL(session)
                subject_in_cycle_hours_dal = SubjectsInCycleHoursDAL(session)
                try:
                    if not await ensure_subject_in_cycle_exists(subject_in_cycle_dal, body.subject_in_cycle_id):
                        raise HTTPException(status_code=404, detail=f"Предмет с id {body.subject_in_cycle_id} не найден")

                    subject_in_cycle_hours = await subject_in_cycle_hours_dal.create_subject_in_cycle_hours(
                        semester=body.semester,
                        self_study_hours=body.self_study_hours,
                        lectures_hours=body.lectures_hours,
                        laboratory_hours=body.laboratory_hours,
                        practical_hours=body.practical_hours,
                        course_project_hours=body.course_project_hours,
                        consultation_hours=body.consultation_hours,
                        intermediate_assessment_hours=body.intermediate_assessment_hours,
                        subject_in_cycle_id=body.subject_in_cycle_id
                    )
                    hours_id = subject_in_cycle_hours.id 
                    subject_in_cycle_hours_pydantic = ShowSubjectsInCycleHours.model_validate(subject_in_cycle_hours, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/subjects_in_cycles_hours/search/by_id/{hours_id}',
                        "update": f'{api_base_url}/subjects_in_cycles_hours/update',
                        "delete": f'{api_base_url}/subjects_in_cycles_hours/delete/{hours_id}',
                        "subjects_in_cycles_hours": f'{api_base_url}/subjects_in_cycles_hours',
                        "subject_in_cycle": f'{api_base_url}/subjects_in_cycles/search/by_id/{body.subject_in_cycle_id}',
                        "teachers_in_plans": f'{api_base_url}/teachers_in_plans/search/by_subject_hours/{hours_id}',
                        "certifications": f'{api_base_url}/certifications/search/by_subject_hours/{hours_id}'
                    }

                    return ShowSubjectsInCycleHoursWithHATEOAS(subject_in_cycle_hours=subject_in_cycle_hours_pydantic, links=hateoas_links)

                except HTTPException:
                    await session.rollback()
                    raise
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Неожиданная ошибка при создании записи о часах для предмета {body.subject_in_cycle_id}: {e}", exc_info=True)
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_subject_in_cycle_hours_by_id(self, hours_id: int, request: Request, db) -> ShowSubjectsInCycleHoursWithHATEOAS:
        async with db as session:
            async with session.begin():
                subject_in_cycle_hours_dal = SubjectsInCycleHoursDAL(session)
                try:
                    subject_in_cycle_hours = await subject_in_cycle_hours_dal.get_subject_in_cycle_hours_by_id(hours_id)
                    if not subject_in_cycle_hours:
                        raise HTTPException(status_code=404, detail=f"Запись о часах для предмета с id {hours_id} не найдена")
                    subject_in_cycle_hours_pydantic = ShowSubjectsInCycleHours.model_validate(subject_in_cycle_hours, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/subjects_in_cycles_hours/search/by_id/{hours_id}',
                        "update": f'{api_base_url}/subjects_in_cycles_hours/update',
                        "delete": f'{api_base_url}/subjects_in_cycles_hours/delete/{hours_id}',
                        "subjects_in_cycles_hours": f'{api_base_url}/subjects_in_cycles_hours',
                        "subject_in_cycle": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_in_cycle_hours.subject_in_cycle_id}',
                        "teachers_in_plans": f'{api_base_url}/teachers_in_plans/search/by_subject_hours/{hours_id}',
                        "certifications": f'{api_base_url}/certifications/search/by_subject_hours/{hours_id}'
                    }

                    return ShowSubjectsInCycleHoursWithHATEOAS(subject_in_cycle_hours=subject_in_cycle_hours_pydantic, links=hateoas_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение записи о часах для предмета {hours_id} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_subjects_in_cycle_hours_by_subject_in_cycle(self, subject_in_cycle_id: int, page: int, limit: int, request: Request, db) -> ShowSubjectsInCycleHoursListWithHATEOAS:
        async with db as session:
            async with session.begin():
                subject_in_cycle_dal = SubjectsInCycleDAL(session)
                subject_in_cycle_hours_dal = SubjectsInCycleHoursDAL(session)
                try:
                    if not await ensure_subject_in_cycle_exists(subject_in_cycle_dal, subject_in_cycle_id):
                        raise HTTPException(status_code=404, detail=f"Предмет в цикле с id {subject_in_cycle_id} не найден")

                    subjects_in_cycle_hours = await subject_in_cycle_hours_dal.get_subjects_in_cycle_hours_by_subject_in_cycle(subject_in_cycle_id, page, limit)
                    
                    if subjects_in_cycle_hours is None:
                        subjects_in_cycle_hours = []

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    subjects_in_cycles_hours_with_hateoas = []
                    for subject_in_cycle_hours in subjects_in_cycle_hours:
                        subject_in_cycle_hours_pydantic = ShowSubjectsInCycleHours.model_validate(subject_in_cycle_hours, from_attributes=True)
                        hours_id = subject_in_cycle_hours.id
                        subject_in_cycle_hours_links = {
                            "self": f'{api_base_url}/subjects_in_cycles_hours/search/by_id/{hours_id}',
                            "update": f'{api_base_url}/subjects_in_cycles_hours/update',
                            "delete": f'{api_base_url}/subjects_in_cycles_hours/delete/{hours_id}',
                            "subjects_in_cycles_hours": f'{api_base_url}/subjects_in_cycles_hours',
                            "subject_in_cycle": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_in_cycle_id}',
                            "teachers_in_plans": f'{api_base_url}/teachers_in_plans/search/by_subject_hours/{hours_id}',
                            "certifications": f'{api_base_url}/certifications/search/by_subject_hours/{hours_id}'
                        }
                        subject_in_cycle_hours_with_links = ShowSubjectsInCycleHoursWithHATEOAS(subject_in_cycle_hours=subject_in_cycle_hours_pydantic, links=subject_in_cycle_hours_links)
                        subjects_in_cycles_hours_with_hateoas.append(subject_in_cycle_hours_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/subjects_in_cycles_hours/search/by_subject_in_cycle/{subject_in_cycle_id}?page={page}&limit={limit}',
                        "create": f'{api_base_url}/subjects_in_cycles_hours/create',
                        "subject_in_cycle": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_in_cycle_id}'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowSubjectsInCycleHoursListWithHATEOAS(subjects_in_cycle_hours=subjects_in_cycles_hours_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение записей о часах для предмета в цикле {subject_in_cycle_id} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")
                

    async def _get_subjects_in_cycle_hours_by_subject_and_semester(self, subject_in_cycle_id: int, semester: int, request: Request, db) -> ShowSubjectsInCycleHoursListWithHATEOAS:
        async with db as session:
            async with session.begin():
                subject_in_cycle_dal = SubjectsInCycleDAL(session)
                subject_in_cycle_hours_dal = SubjectsInCycleHoursDAL(session)
                try:
                    if not await ensure_subject_in_cycle_exists(subject_in_cycle_dal, subject_in_cycle_id):
                        raise HTTPException(status_code=404, detail=f"Предмет в цикле с id {subject_in_cycle_id} не найден")

                    subjects_in_cycle_hours = await subject_in_cycle_hours_dal.get_subjects_in_cycle_hours_by_subject_and_semester(subject_in_cycle_id, semester)
                    
                    if subjects_in_cycle_hours is None:
                        subjects_in_cycle_hours = []

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    subjects_in_cycles_hours_with_hateoas = []
                    for subject_in_cycle_hours in subjects_in_cycle_hours:
                        subject_in_cycle_hours_pydantic = ShowSubjectsInCycleHours.model_validate(subject_in_cycle_hours, from_attributes=True)
                        hours_id = subject_in_cycle_hours.id
                        subject_in_cycle_hours_links = {
                            "self": f'{api_base_url}/subjects_in_cycles_hours/search/by_id/{hours_id}',
                            "update": f'{api_base_url}/subjects_in_cycles_hours/update',
                            "delete": f'{api_base_url}/subjects_in_cycles_hours/delete/{hours_id}',
                            "subjects_in_cycles_hours": f'{api_base_url}/subjects_in_cycles_hours',
                            "subject_in_cycle": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_in_cycle_id}',
                            "teachers_in_plans": f'{api_base_url}/teachers_in_plans/search/by_subject_hours/{hours_id}',
                            "certifications": f'{api_base_url}/certifications/search/by_subject_hours/{hours_id}'
                        }
                        subject_in_cycle_hours_with_links = ShowSubjectsInCycleHoursWithHATEOAS(subject_in_cycle_hours=subject_in_cycle_hours_pydantic, links=subject_in_cycle_hours_links)
                        subjects_in_cycles_hours_with_hateoas.append(subject_in_cycle_hours_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/subjects_in_cycles_hours/search/by_subject_and_semester/{subject_in_cycle_id}/{semester}',
                        "create": f'{api_base_url}/subjects_in_cycles_hours/create',
                        "subject_in_cycle": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_in_cycle_id}',
                        "subjects_in_cycles_by_semester": f'{api_base_url}/subjects_in_cycles_hours/search/by_semester/{semester}'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}
                    
                    return ShowSubjectsInCycleHoursListWithHATEOAS(subjects_in_cycle_hours=subjects_in_cycles_hours_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение записей о часах для предмета в цикле {subject_in_cycle_id} по семестру {semester} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_subjects_in_cycle_hours_by_semester(self, semester: int, page: int, limit: int, request: Request, db) -> ShowSubjectsInCycleHoursListWithHATEOAS:
        async with db as session:
            async with session.begin():
                subject_in_cycle_hours_dal = SubjectsInCycleHoursDAL(session)
                try:
                    subjects_in_cycle_hours = await subject_in_cycle_hours_dal.get_subjects_in_cycle_hours_by_semester(semester, page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    subjects_in_cycles_hours_with_hateoas = []
                    for subject_in_cycle_hours in subjects_in_cycle_hours:
                        subject_in_cycle_hours_pydantic = ShowSubjectsInCycleHours.model_validate(subject_in_cycle_hours, from_attributes=True)
                        hours_id = subject_in_cycle_hours.id
                        subject_in_cycle_hours_links = {
                            "self": f'{api_base_url}/subjects_in_cycles_hours/search/by_id/{hours_id}',
                            "update": f'{api_base_url}/subjects_in_cycles_hours/update',
                            "delete": f'{api_base_url}/subjects_in_cycles_hours/delete/{hours_id}',
                            "subjects_in_cycles_hours": f'{api_base_url}/subjects_in_cycles_hours',
                            "subject_in_cycle": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_in_cycle_hours.subject_in_cycle_id}',
                            "teachers_in_plans": f'{api_base_url}/teachers_in_plans/search/by_subject_hours/{hours_id}',
                            "certifications": f'{api_base_url}/certifications/search/by_subject_hours/{hours_id}'
                        }
                        subject_in_cycle_hours_with_links = ShowSubjectsInCycleHoursWithHATEOAS(subject_in_cycle_hours=subject_in_cycle_hours_pydantic, links=subject_in_cycle_hours_links)
                        subjects_in_cycles_hours_with_hateoas.append(subject_in_cycle_hours_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/subjects_in_cycles_hours/search/by_semester/{semester}?page={page}&limit={limit}',
                        "create": f'{api_base_url}/subjects_in_cycles_hours/create'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowSubjectsInCycleHoursListWithHATEOAS(subjects_in_cycle_hours=subjects_in_cycles_hours_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение записей о часах для семестра {semester} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_all_subjects_in_cycle_hours(self, page: int, limit: int, request: Request, db) -> ShowSubjectsInCycleHoursListWithHATEOAS:
        async with db as session:
            async with session.begin():
                subject_in_cycle_hours_dal = SubjectsInCycleHoursDAL(session)
                try:
                    subjects_in_cycle_hours = await subject_in_cycle_hours_dal.get_all_subjects_in_cycle_hours(page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    subjects_in_cycles_hours_with_hateoas = []
                    for subject_in_cycle_hours in subjects_in_cycle_hours:
                        subject_in_cycle_hours_pydantic = ShowSubjectsInCycleHours.model_validate(subject_in_cycle_hours, from_attributes=True)
                        hours_id = subject_in_cycle_hours.id
                        subject_in_cycle_hours_links = {
                            "self": f'{api_base_url}/subjects_in_cycles_hours/search/by_id/{hours_id}',
                            "update": f'{api_base_url}/subjects_in_cycles_hours/update',
                            "delete": f'{api_base_url}/subjects_in_cycles_hours/delete/{hours_id}',
                            "subjects_in_cycles_hours": f'{api_base_url}/subjects_in_cycles_hours',
                            "subject_in_cycle": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_in_cycle_hours.subject_in_cycle_id}',
                            "teachers_in_plans": f'{api_base_url}/teachers_in_plans/search/by_subject_hours/{hours_id}',
                            "certifications": f'{api_base_url}/certifications/search/by_subject_hours/{hours_id}'
                        }
                        subject_in_cycle_hours_with_links = ShowSubjectsInCycleHoursWithHATEOAS(subject_in_cycle_hours=subject_in_cycle_hours_pydantic, links=subject_in_cycle_hours_links)
                        subjects_in_cycles_hours_with_hateoas.append(subject_in_cycle_hours_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/subjects_in_cycles_hours/search?page={page}&limit={limit}',
                        "create": f'{api_base_url}/subjects_in_cycles_hours/create'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowSubjectsInCycleHoursListWithHATEOAS(subjects_in_cycle_hours=subjects_in_cycles_hours_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение записей о часах для предметов  отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")
                
                
    async def _get_subjects_hours_by_ids(self, ids: list[int], page: int, limit: int, request: Request, db) -> ShowSubjectsInCycleHoursListWithHATEOAS:
        async with db as session:
            async with session.begin():
                subjects_in_cycle_hours_dal = SubjectsInCycleHoursDAL(session)
                try:
                    subjects_in_cycle_hours_list = await subjects_in_cycle_hours_dal.get_subjects_hours_by_ids(ids, page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    subjects_in_cycles_hours_with_hateoas = []
                    for subject_hours in subjects_in_cycle_hours_list:
                        subject_hours_pydantic = ShowSubjectsInCycleHours.model_validate(subject_hours, from_attributes=True)
                        subject_hours_id = subject_hours.id
                        subject_hours_links = {
                            "self": f'{api_base_url}/subjects_in_cycles_hours/search/by_id/{subject_hours_id}',
                            "subjects_in_cycle": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_hours.subject_in_cycle_id}',
                        }
                        subject_hours_with_links = ShowSubjectsInCycleHoursWithHATEOAS(subject_in_cycle_hours=subject_hours_pydantic, links=subject_hours_links)
                        subjects_in_cycles_hours_with_hateoas.append(subject_hours_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/subjects_in_cycles_hours/search/by_ids?page={page}&limit={limit}&ids={",".join(map(str, ids))}',
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowSubjectsInCycleHoursListWithHATEOAS(subjects_in_cycle_hours=subjects_in_cycles_hours_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение записей о часах по списку id отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _delete_subject_in_cycle_hours(self, hours_id: int, request: Request, db) -> ShowSubjectsInCycleHoursWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    subject_in_cycle_hours_dal = SubjectsInCycleHoursDAL(session)

                    if not await ensure_subject_in_cycle_hours_exists(subject_in_cycle_hours_dal, hours_id):
                        raise HTTPException(status_code=404, detail=f"Запись о часах для предмета с id {hours_id} не найдена")

                    subject_in_cycle_hours = await subject_in_cycle_hours_dal.delete_subject_in_cycle_hours(hours_id)
                    
                    if not subject_in_cycle_hours:
                        raise HTTPException(status_code=404, detail=f"Запись о часах для предмета с id {hours_id} не найдена")

                    subject_in_cycle_hours_pydantic = ShowSubjectsInCycleHours.model_validate(subject_in_cycle_hours, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "subjects_in_cycles_hours": f'{api_base_url}/subjects_in_cycles_hours',
                        "create": f'{api_base_url}/subjects_in_cycles_hours/create',
                        "subject_in_cycle": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_in_cycle_hours.subject_in_cycle_id}'
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowSubjectsInCycleHoursWithHATEOAS(subject_in_cycle_hours=subject_in_cycle_hours_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при удалении записи о часах для предмета {hours_id}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении записи о часах для предмета .")


    async def _update_subject_in_cycle_hours(self, body: UpdateSubjectsInCycleHours, request: Request, db) -> ShowSubjectsInCycleHoursWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["hours_id"]}
                    
                    if "subject_in_cycle_id" in update_data:
                        subject_in_cycle_id_to_check = update_data["subject_in_cycle_id"]
                        subject_in_cycle_dal = SubjectsInCycleDAL(session)
                        if not await ensure_subject_in_cycle_exists(subject_in_cycle_dal, subject_in_cycle_id_to_check):
                            raise HTTPException(status_code=404, detail=f"Предмет с id {subject_in_cycle_id_to_check} не найден")

                    subject_in_cycle_hours_dal = SubjectsInCycleHoursDAL(session)

                    if not await ensure_subject_in_cycle_hours_exists(subject_in_cycle_hours_dal, body.hours_id):
                        raise HTTPException(status_code=404, detail=f"Запись о часах для предмета с id {body.hours_id} не найдена")

                    subject_in_cycle_hours = await subject_in_cycle_hours_dal.update_subject_in_cycle_hours(target_id=body.hours_id, **update_data)
                    if not subject_in_cycle_hours:
                        raise HTTPException(status_code=404, detail=f"Запись о часах для предмета с id {body.hours_id} не найдена")

                    hours_id = subject_in_cycle_hours.id 
                    subject_in_cycle_hours_pydantic = ShowSubjectsInCycleHours.model_validate(subject_in_cycle_hours, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/subjects_in_cycles_hours/search/by_id/{hours_id}',
                        "update": f'{api_base_url}/subjects_in_cycles_hours/update',
                        "delete": f'{api_base_url}/subjects_in_cycles_hours/delete/{hours_id}',
                        "subjects_in_cycles_hours": f'{api_base_url}/subjects_in_cycles_hours',
                        "subject_in_cycle": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_in_cycle_hours.subject_in_cycle_id}',
                        "teachers_in_plans": f'{api_base_url}/teachers_in_plans/search/by_subject_hours/{hours_id}',
                        "certifications": f'{api_base_url}/certifications/search/by_subject_hours/{hours_id}'
                    }

                    return ShowSubjectsInCycleHoursWithHATEOAS(subject_in_cycle_hours=subject_in_cycle_hours_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.warning(f"Изменение данных о часах для предмета отменено (Ошибка: {e})")
                raise e
            