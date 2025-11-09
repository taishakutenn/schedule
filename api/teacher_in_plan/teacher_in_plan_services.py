from api.teacher.teacher_DAL import TeacherDAL
from api.group.group_DAL import GroupDAL
from api.session_type.session_type_DAL import SessionTypeDAL
from api.teacher_in_plan.teacher_in_plan_pydantic import *
from api.services_helpers import ensure_group_exists, ensure_session_type_exists, ensure_subject_in_cycle_hours_exists, ensure_teacher_exists, ensure_teacher_in_plan_exists
from api.teacher_in_plan.teacher_in_plan_DAL import TeacherInPlanDAL 
<<<<<<< HEAD
from api.subject_in_cycle_hours.subject_in_cycle_DAL import SubjectsInCycleHoursDAL
=======
# from api.subject_in_cycle_hours.subject_in_cycle_hours_DAL import SubjectsInCycleHoursDAL <--- DEBUG THIS
>>>>>>> 5bfc84b3b8ec1937e76a65a68834163a4fc9aee4
from fastapi import HTTPException, Request

from config.logging_config import configure_logging

# Create logger object
logger = configure_logging()


class TeacherInPlanService:
    async def _create_new_teacher_in_plan(self, body: CreateTeacherInPlan, request: Request, db) -> ShowTeacherInPlanWithHATEOAS:
        async with db as session:
            async with session.begin():
                subjects_in_cycle_hours_dal = SubjectsInCycleHoursDAL(session) # <--- AND DEBUG THIS
                teacher_dal = TeacherDAL(session)
                group_dal = GroupDAL(session)
                session_type_dal = SessionTypeDAL(session)
                teacher_in_plan_dal = TeacherInPlanDAL(session)
                try:
                    if not await ensure_subject_in_cycle_hours_exists(subjects_in_cycle_hours_dal, body.subject_in_cycle_hours_id):
                        raise HTTPException(status_code=404, detail=f"Запись о часах для предмета в цикле с id {body.subject_in_cycle_hours_id} не найдена")
                    if not await ensure_teacher_exists(teacher_dal, body.teacher_id):
                        raise HTTPException(status_code=404, detail=f"Преподаватель с id {body.teacher_id} не найден")
                    if not await ensure_group_exists(group_dal, body.group_name):
                        raise HTTPException(status_code=404, detail=f"Группа с названием {body.group_name} не найдена")
                    if not await ensure_session_type_exists(session_type_dal, body.session_type):
                        raise HTTPException(status_code=404, detail=f"Тип занятия {body.session_type} не найден")

                    teacher_in_plan = await teacher_in_plan_dal.create_teacher_in_plan(
                        subject_in_cycle_hours_id=body.subject_in_cycle_hours_id,
                        teacher_id=body.teacher_id,
                        group_name=body.group_name,
                        session_type=body.session_type
                    )
                    teacher_in_plan_id = teacher_in_plan.id
                    teacher_in_plan_pydantic = ShowTeacherInPlan.model_validate(teacher_in_plan, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/teachers_in_plans/search/by_id/{teacher_in_plan_id}',
                        "update": f'{api_base_url}/teachers_in_plans/update',
                        "delete": f'{api_base_url}/teachers_in_plans/delete/{teacher_in_plan_id}',
                        "teachers_in_plans": f'{api_base_url}/teachers_in_plans',
                        "subjects_in_cycle_hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_id/{body.subject_in_cycle_hours_id}',
                        "teacher": f'{api_base_url}/teachers/search/by_id/{body.teacher_id}',
                        "group": f'{api_base_url}/groups/search/by_group_name/{body.group_name}',
                        "session_type": f'{api_base_url}/session-types/search/by_name/{body.session_type}',
                        "sessions": f'{api_base_url}/sessions/search/by_plan/{teacher_in_plan_id}'
                    }

                    return ShowTeacherInPlanWithHATEOAS(teacher_in_plan=teacher_in_plan_pydantic, links=hateoas_links)

                except HTTPException:
                    await session.rollback()
                    raise
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Неожиданная ошибка при создании записи в расписании преподавателя: {e}", exc_info=True)
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_teacher_in_plan_by_id(self, teacher_in_plan_id: int, request: Request, db) -> ShowTeacherInPlanWithHATEOAS:
        async with db as session:
            async with session.begin():
                teacher_in_plan_dal = TeacherInPlanDAL(session)
                try:
                    if not await ensure_teacher_in_plan_exists(teacher_in_plan_dal, teacher_in_plan_id):
                        raise HTTPException(status_code=404, detail=f"Запись в расписании преподавателя с id {teacher_in_plan_id} не найдена")

                    teacher_in_plan = await teacher_in_plan_dal.get_teacher_in_plan_by_id(teacher_in_plan_id)
                    teacher_in_plan_pydantic = ShowTeacherInPlan.model_validate(teacher_in_plan, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/teachers_in_plans/search/by_id/{teacher_in_plan_id}',
                        "update": f'{api_base_url}/teachers_in_plans/update',
                        "delete": f'{api_base_url}/teachers_in_plans/delete/{teacher_in_plan_id}',
                        "teachers_in_plans": f'{api_base_url}/teachers_in_plans',
                        "subjects_in_cycle_hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_id/{teacher_in_plan.subject_in_cycle_hours_id}',
                        "teacher": f'{api_base_url}/teachers/search/by_id/{teacher_in_plan.teacher_id}',
                        "group": f'{api_base_url}/groups/search/by_group_name/{teacher_in_plan.group_name}',
                        "session_type": f'{api_base_url}/session-types/search/by_name/{teacher_in_plan.session_type}',
                        "sessions": f'{api_base_url}/sessions/search/by_plan/{teacher_in_plan_id}'
                    }

                    return ShowTeacherInPlanWithHATEOAS(teacher_in_plan=teacher_in_plan_pydantic, links=hateoas_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение записи в расписании преподавателя {teacher_in_plan_id} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_teachers_in_plans_by_teacher(self, teacher_id: int, page: int, limit: int, request: Request, db) -> ShowTeacherInPlanListWithHATEOAS:
        async with db as session:
            async with session.begin():
                teacher_dal = TeacherDAL(session)
                teacher_in_plan_dal = TeacherInPlanDAL(session)
                try:
                    if not await ensure_teacher_exists(teacher_dal, teacher_id):
                        raise HTTPException(status_code=404, detail=f"Преподаватель с id {teacher_id} не найден")

                    teachers_in_plans = await teacher_in_plan_dal.get_teachers_in_plans_by_teacher(teacher_id, page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    teachers_in_plans_with_hateoas = []
                    for teacher_in_plan in teachers_in_plans:
                        teacher_in_plan_pydantic = ShowTeacherInPlan.model_validate(teacher_in_plan, from_attributes=True)
                        teacher_in_plan_id = teacher_in_plan.id
                        teacher_in_plan_links = {
                            "self": f'{api_base_url}/teachers_in_plans/search/by_id/{teacher_in_plan_id}',
                            "update": f'{api_base_url}/teachers_in_plans/update',
                            "delete": f'{api_base_url}/teachers_in_plans/delete/{teacher_in_plan_id}',
                            "teachers_in_plans": f'{api_base_url}/teachers_in_plans',
                            "subjects_in_cycle_hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_id/{teacher_in_plan.subject_in_cycle_hours_id}',
                            "teacher": f'{api_base_url}/teachers/search/by_id/{teacher_id}',
                            "group": f'{api_base_url}/groups/search/by_group_name/{teacher_in_plan.group_name}',
                            "session_type": f'{api_base_url}/session-types/search/by_name/{teacher_in_plan.session_type}',
                            "sessions": f'{api_base_url}/sessions/search/by_plan/{teacher_in_plan_id}'
                        }
                        teacher_in_plan_with_links = ShowTeacherInPlanWithHATEOAS(teacher_in_plan=teacher_in_plan_pydantic, links=teacher_in_plan_links)
                        teachers_in_plans_with_hateoas.append(teacher_in_plan_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/teachers_in_plans/search/by_teacher/{teacher_id}?page={page}&limit={limit}',
                        "create": f'{api_base_url}/teachers_in_plans/create',
                        "teacher": f'{api_base_url}/teachers/search/by_id/{teacher_id}'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowTeacherInPlanListWithHATEOAS(teachers_in_plans=teachers_in_plans_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение записей в расписании преподавателя для преподавателя {teacher_id} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_teachers_in_plans_by_group(self, group_name: str, page: int, limit: int, request: Request, db) -> ShowTeacherInPlanListWithHATEOAS:
        async with db as session:
            async with session.begin():
                group_dal = GroupDAL(session)
                teacher_in_plan_dal = TeacherInPlanDAL(session)
                try:
                    if not await ensure_group_exists(group_dal, group_name):
                        raise HTTPException(status_code=404, detail=f"Группа с названием {group_name} не найдена")

                    teachers_in_plans = await teacher_in_plan_dal.get_teachers_in_plans_by_group(group_name, page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    teachers_in_plans_with_hateoas = []
                    for teacher_in_plan in teachers_in_plans:
                        teacher_in_plan_pydantic = ShowTeacherInPlan.model_validate(teacher_in_plan, from_attributes=True)
                        teacher_in_plan_id = teacher_in_plan.id
                        teacher_in_plan_links = {
                            "self": f'{api_base_url}/teachers_in_plans/search/by_id/{teacher_in_plan_id}',
                            "update": f'{api_base_url}/teachers_in_plans/update',
                            "delete": f'{api_base_url}/teachers_in_plans/delete/{teacher_in_plan_id}',
                            "teachers_in_plans": f'{api_base_url}/teachers_in_plans',
                            "subjects_in_cycle_hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_id/{teacher_in_plan.subject_in_cycle_hours_id}',
                            "teacher": f'{api_base_url}/teachers/search/by_id/{teacher_in_plan.teacher_id}',
                            "group": f'{api_base_url}/groups/search/by_group_name/{group_name}',
                            "session_type": f'{api_base_url}/session-types/search/by_name/{teacher_in_plan.session_type}',
                            "sessions": f'{api_base_url}/sessions/search/by_plan/{teacher_in_plan_id}'
                        }
                        teacher_in_plan_with_links = ShowTeacherInPlanWithHATEOAS(teacher_in_plan=teacher_in_plan_pydantic, links=teacher_in_plan_links)
                        teachers_in_plans_with_hateoas.append(teacher_in_plan_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/teachers_in_plans/search/by_group/{group_name}?page={page}&limit={limit}',
                        "create": f'{api_base_url}/teachers_in_plans/create',
                        "group": f'{api_base_url}/groups/search/by_group_name/{group_name}'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowTeacherInPlanListWithHATEOAS(teachers_in_plans=teachers_in_plans_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение записей в расписании преподавателя для группы {group_name} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_teachers_in_plans_by_subject_hours(self, subject_hours_id: int, page: int, limit: int, request: Request, db) -> ShowTeacherInPlanListWithHATEOAS:
        async with db as session:
            async with session.begin():
                subjects_in_cycle_hours_dal = SubjectsInCycleHoursDAL(session)
                teacher_in_plan_dal = TeacherInPlanDAL(session)
                try:
                    if not await ensure_subject_in_cycle_hours_exists(subjects_in_cycle_hours_dal, subject_hours_id):
                        raise HTTPException(status_code=404, detail=f"Запись о часах для предмета в цикле с id {subject_hours_id} не найдена")

                    teachers_in_plans = await teacher_in_plan_dal.get_teachers_in_plans_by_subject_hours(subject_hours_id, page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    teachers_in_plans_with_hateoas = []
                    for teacher_in_plan in teachers_in_plans:
                        teacher_in_plan_pydantic = ShowTeacherInPlan.model_validate(teacher_in_plan, from_attributes=True)
                        teacher_in_plan_id = teacher_in_plan.id
                        teacher_in_plan_links = {
                            "self": f'{api_base_url}/teachers_in_plans/search/by_id/{teacher_in_plan_id}',
                            "update": f'{api_base_url}/teachers_in_plans/update',
                            "delete": f'{api_base_url}/teachers_in_plans/delete/{teacher_in_plan_id}',
                            "teachers_in_plans": f'{api_base_url}/teachers_in_plans',
                            "subjects_in_cycle_hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_id/{subject_hours_id}',
                            "teacher": f'{api_base_url}/teachers/search/by_id/{teacher_in_plan.teacher_id}',
                            "group": f'{api_base_url}/groups/search/by_group_name/{teacher_in_plan.group_name}',
                            "session_type": f'{api_base_url}/session-types/search/by_name/{teacher_in_plan.session_type}',
                            "sessions": f'{api_base_url}/sessions/search/by_plan/{teacher_in_plan_id}'
                        }
                        teacher_in_plan_with_links = ShowTeacherInPlanWithHATEOAS(teacher_in_plan=teacher_in_plan_pydantic, links=teacher_in_plan_links)
                        teachers_in_plans_with_hateoas.append(teacher_in_plan_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/teachers_in_plans/search/by_subject_hours/{subject_hours_id}?page={page}&limit={limit}',
                        "create": f'{api_base_url}/teachers_in_plans/create',
                        "subjects_in_cycle_hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_id/{subject_hours_id}'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowTeacherInPlanListWithHATEOAS(teachers_in_plans=teachers_in_plans_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение записей в расписании преподавателя для часов предмета {subject_hours_id} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_teachers_in_plans_by_session_type(self, session_type: str, page: int, limit: int, request: Request, db) -> ShowTeacherInPlanListWithHATEOAS:
        async with db as session:
            async with session.begin():
                session_type_dal = SessionTypeDAL(session)
                teacher_in_plan_dal = TeacherInPlanDAL(session)
                try:
                    if not await ensure_session_type_exists(session_type_dal, session_type):
                        raise HTTPException(status_code=404, detail=f"Тип занятия {session_type} не найден")

                    teachers_in_plans = await teacher_in_plan_dal.get_teachers_in_plans_by_session_type(session_type, page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    teachers_in_plans_with_hateoas = []
                    for teacher_in_plan in teachers_in_plans:
                        teacher_in_plan_pydantic = ShowTeacherInPlan.model_validate(teacher_in_plan, from_attributes=True)
                        teacher_in_plan_id = teacher_in_plan.id
                        teacher_in_plan_links = {
                            "self": f'{api_base_url}/teachers_in_plans/search/by_id/{teacher_in_plan_id}',
                            "update": f'{api_base_url}/teachers_in_plans/update',
                            "delete": f'{api_base_url}/teachers_in_plans/delete/{teacher_in_plan_id}',
                            "teachers_in_plans": f'{api_base_url}/teachers_in_plans',
                            "subjects_in_cycle_hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_id/{teacher_in_plan.subject_in_cycle_hours_id}',
                            "teacher": f'{api_base_url}/teachers/search/by_id/{teacher_in_plan.teacher_id}',
                            "group": f'{api_base_url}/groups/search/by_group_name/{teacher_in_plan.group_name}',
                            "session_type": f'{api_base_url}/session-types/search/by_name/{teacher_in_plan.session_type}',
                            "sessions": f'{api_base_url}/sessions/search/by_plan/{teacher_in_plan_id}'
                        }
                        teacher_in_plan_with_links = ShowTeacherInPlanWithHATEOAS(teacher_in_plan=teacher_in_plan_pydantic, links=teacher_in_plan_links)
                        teachers_in_plans_with_hateoas.append(teacher_in_plan_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/teachers_in_plans/search/by_session_type/{session_type}?page={page}&limit={limit}',
                        "create": f'{api_base_url}/teachers_in_plans/create',
                        "session_type": f'{api_base_url}/session-types/search/by_name/{session_type}'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowTeacherInPlanListWithHATEOAS(teachers_in_plans=teachers_in_plans_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение записей в расписании преподавателя для типа занятия {session_type} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_all_teachers_in_plans(self, page: int, limit: int, request: Request, db) -> ShowTeacherInPlanListWithHATEOAS:
        async with db as session:
            async with session.begin():
                teacher_in_plan_dal = TeacherInPlanDAL(session)
                try:
                    teachers_in_plans = await teacher_in_plan_dal.get_all_teachers_in_plans(page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    teachers_in_plans_with_hateoas = []
                    for teacher_in_plan in teachers_in_plans:
                        teacher_in_plan_pydantic = ShowTeacherInPlan.model_validate(teacher_in_plan, from_attributes=True)
                        teacher_in_plan_id = teacher_in_plan.id
                        teacher_in_plan_links = {
                            "self": f'{api_base_url}/teachers_in_plans/search/by_id/{teacher_in_plan_id}',
                            "update": f'{api_base_url}/teachers_in_plans/update',
                            "delete": f'{api_base_url}/teachers_in_plans/delete/{teacher_in_plan_id}',
                            "teachers_in_plans": f'{api_base_url}/teachers_in_plans',
                            "subjects_in_cycle_hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_id/{teacher_in_plan.subject_in_cycle_hours_id}',
                            "teacher": f'{api_base_url}/teachers/search/by_id/{teacher_in_plan.teacher_id}',
                            "group": f'{api_base_url}/groups/search/by_group_name/{teacher_in_plan.group_name}',
                            "session_type": f'{api_base_url}/session-types/search/by_name/{teacher_in_plan.session_type}',
                            "sessions": f'{api_base_url}/sessions/search/by_plan/{teacher_in_plan_id}'
                        }
                        teacher_in_plan_with_links = ShowTeacherInPlanWithHATEOAS(teacher_in_plan=teacher_in_plan_pydantic, links=teacher_in_plan_links)
                        teachers_in_plans_with_hateoas.append(teacher_in_plan_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/teachers_in_plans/search?page={page}&limit={limit}',
                        "create": f'{api_base_url}/teachers_in_plans/create'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowTeacherInPlanListWithHATEOAS(teachers_in_plans=teachers_in_plans_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение записей в расписании преподавателя отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _delete_teacher_in_plan(self, teacher_in_plan_id: int, request: Request, db) -> ShowTeacherInPlanWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    teacher_in_plan_dal = TeacherInPlanDAL(session)
                    
                    if not await ensure_teacher_in_plan_exists(teacher_in_plan_dal, teacher_in_plan_id):
                        raise HTTPException(status_code=404, detail=f"Запись в расписании преподавателя с id {teacher_in_plan_id} не найдена")

                    teacher_in_plan = await teacher_in_plan_dal.delete_teacher_in_plan(teacher_in_plan_id)
                    
                    if not teacher_in_plan:
                        raise HTTPException(status_code=404, detail=f"Запись в расписании преподавателя с id {teacher_in_plan_id} не найдена")

                    teacher_in_plan_pydantic = ShowTeacherInPlan.model_validate(teacher_in_plan, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "teachers_in_plans": f'{api_base_url}/teachers_in_plans',
                        "create": f'{api_base_url}/teachers_in_plans/create'
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowTeacherInPlanWithHATEOAS(teacher_in_plan=teacher_in_plan_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при удалении записи в расписании преподавателя {teacher_in_plan_id}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении записи в расписании преподавателя.")


    async def _update_teacher_in_plan(self, body: UpdateTeacherInPlan, request: Request, db) -> ShowTeacherInPlanWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["teacher_in_plan_id"]}
                    
                    if "subject_in_cycle_hours_id" in update_data:
                        subjects_in_cycle_hours_dal = SubjectsInCycleHoursDAL(session)
                        if not await ensure_subject_in_cycle_hours_exists(subjects_in_cycle_hours_dal, update_data["subject_in_cycle_hours_id"]):
                            raise HTTPException(status_code=404, detail=f"Запись о часах для предмета в цикле с id {update_data['subject_in_cycle_hours_id']} не найдена")
                    if "teacher_id" in update_data:
                        teacher_dal = TeacherDAL(session)
                        if not await ensure_teacher_exists(teacher_dal, update_data["teacher_id"]):
                            raise HTTPException(status_code=404, detail=f"Преподаватель с id {update_data['teacher_id']} не найден")
                    if "group_name" in update_data:
                        group_dal = GroupDAL(session)
                        if not await ensure_group_exists(group_dal, update_data["group_name"]):
                            raise HTTPException(status_code=404, detail=f"Группа с названием {update_data['group_name']} не найдена")
                    if "session_type" in update_data:
                        session_type_dal = SessionTypeDAL(session)
                        if not await ensure_session_type_exists(session_type_dal, update_data["session_type"]):
                            raise HTTPException(status_code=404, detail=f"Тип занятия {update_data['session_type']} не найден")

                    teacher_in_plan_dal = TeacherInPlanDAL(session)

                    if not await ensure_teacher_in_plan_exists(teacher_in_plan_dal, body.teacher_in_plan_id):
                        raise HTTPException(status_code=404, detail=f"Запись в расписании преподавателя с id {body.teacher_in_plan_id} не найдена")

                    teacher_in_plan = await teacher_in_plan_dal.update_teacher_in_plan(target_id=body.teacher_in_plan_id, **update_data)
                    if not teacher_in_plan:
                        raise HTTPException(status_code=404, detail=f"Запись в расписании преподавателя с id {body.teacher_in_plan_id} не найдена")

                    teacher_in_plan_id = teacher_in_plan.id
                    teacher_in_plan_pydantic = ShowTeacherInPlan.model_validate(teacher_in_plan, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/teachers_in_plans/search/by_id/{teacher_in_plan_id}',
                        "update": f'{api_base_url}/teachers_in_plans/update',
                        "delete": f'{api_base_url}/teachers_in_plans/delete/{teacher_in_plan_id}',
                        "teachers_in_plans": f'{api_base_url}/teachers_in_plans',
                        "subjects_in_cycle_hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_id/{teacher_in_plan.subject_in_cycle_hours_id}',
                        "teacher": f'{api_base_url}/teachers/search/by_id/{teacher_in_plan.teacher_id}',
                        "group": f'{api_base_url}/groups/search/by_group_name/{teacher_in_plan.group_name}',
                        "session_type": f'{api_base_url}/session-types/search/by_name/{teacher_in_plan.session_type}',
                        "sessions": f'{api_base_url}/sessions/search/by_plan/{teacher_in_plan_id}'
                    }

                    return ShowTeacherInPlanWithHATEOAS(teacher_in_plan=teacher_in_plan_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.warning(f"Изменение данных о записи в расписании преподавателя отменено (Ошибка: {e})")
                raise e
            