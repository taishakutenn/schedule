from api.group.group_pydantic import *
from api.payment.payment_DAL import PaymentFormDAL
from api.services_helpers import ensure_group_exists, ensure_group_unique, ensure_speciality_exists, ensure_teacher_exists, ensure_payment_form_exists
from api.group.group_DAL import GroupDAL
from api.speciality.speciality_DAL import SpecialityDAL
from api.teacher.teacher_DAL import TeacherDAL
from fastapi import HTTPException, Request

from config.logging_config import configure_logging

# Create logger object
logger = configure_logging()


class GroupService:
    async def _create_new_group(self, body: CreateGroup, request: Request, db) -> ShowGroupWithHATEOAS:
        async with db as session:
            async with session.begin():
                group_dal = GroupDAL(session)
                teacher_dal = TeacherDAL(session)
                speciality_dal = SpecialityDAL(session)
                payment_dal = PaymentFormDAL(session)
                
                try:
                    if body.speciality_code is not None and not await ensure_speciality_exists(speciality_dal, body.speciality_code):
                        raise HTTPException(status_code=404, detail=f"Специальность с кодом {body.speciality_code} не найдена")
                    
                    if body.group_advisor_id is not None and not await ensure_teacher_exists(teacher_dal, body.group_advisor_id):
                        raise HTTPException(status_code=404, detail=f"Преподаватель с id {body.group_advisor_id} не найден")
                    
                    if body.payment_form is not None and not await ensure_payment_form_exists(payment_dal, body.payment_form):
                        raise HTTPException(status_code=404, detail=f"Форма оплаты {body.payment_form} не найдена")
                    
                    if not await ensure_group_unique(group_dal, body.group_name):
                        raise HTTPException(status_code=400, detail=f"Группа {body.group_name} уже существует")

                    group = await group_dal.create_group(
                        group_name=body.group_name,
                        speciality_code=body.speciality_code,
                        quantity_students=body.quantity_students,
                        group_advisor_id=body.group_advisor_id
                    )
                    group_name = group.group_name
                    group_pydantic = ShowGroup.model_validate(group, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/groups/search/by_group_name/{group_name}',
                        "update": f'{api_base_url}/groups/update',
                        "delete": f'{api_base_url}/groups/delete/{group_name}',
                        "groups": f'{api_base_url}/groups',
                        "advisor": f'{api_base_url}/teachers/search/by_id/{group.group_advisor_id}' if group.group_advisor_id else None,
                        "speciality": f'{api_base_url}/specialities/search/by_speciality_code/{group.speciality_code}' if group.speciality_code else None,
                        "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}',
                        "streams": f'{api_base_url}/streams/search/by_group/{group_name}',
                        "teachers_in_plans": f'{api_base_url}/teachers_in_plans/search/by_group/{group_name}'
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowGroupWithHATEOAS(group=group_pydantic, links=hateoas_links)

                except HTTPException:
                    await session.rollback()
                    raise
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Неожиданная ошибка при создании группы: {e}", exc_info=True)
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_group_by_name(self, group_name: str, request: Request, db) -> ShowGroupWithHATEOAS:
        async with db as session:
            async with session.begin():
                group_dal = GroupDAL(session)
                try:
                    group = await group_dal.get_group_by_name(group_name)
                    if not group:
                        raise HTTPException(status_code=404, detail=f"Группа с названием: {group_name} не найдена")
                    group_pydantic = ShowGroup.model_validate(group, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/groups/search/by_group_name/{group_name}',
                        "update": f'{api_base_url}/groups/update',
                        "delete": f'{api_base_url}/groups/delete/{group_name}',
                        "groups": f'{api_base_url}/groups',
                        "advisor": f'{api_base_url}/teachers/search/by_id/{group.group_advisor_id}' if group.group_advisor_id else None,
                        "speciality": f'{api_base_url}/specialities/search/by_speciality_code/{group.speciality_code}' if group.speciality_code else None,
                        "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}',
                        "streams": f'{api_base_url}/streams/search/by_group/{group_name}',
                        "teachers_in_plans": f'{api_base_url}/teachers_in_plans/search/by_group/{group_name}'
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowGroupWithHATEOAS(group=group_pydantic, links=hateoas_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"Неожиданная ошибка при получении группы {group_name}: {e}", exc_info=True)
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при получении группы.")


    async def _get_group_by_advisor(self, advisor_id: int, request: Request, db) -> ShowGroupWithHATEOAS:
        async with db as session:
            async with session.begin():
                group_dal = GroupDAL(session)
                teacher_dal = TeacherDAL(session)
                try:
                    if not await ensure_teacher_exists(teacher_dal, advisor_id):
                        raise HTTPException(status_code=404, detail=f"Преподаватель с id {advisor_id} не найден")

                    group = await group_dal.get_group_by_advisor_id(advisor_id)
                    if not group:
                        raise HTTPException(status_code=404, detail=f"Группа с преподавателем: {advisor_id} не найдена")
                    group_pydantic = ShowGroup.model_validate(group, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/groups/search/by_group_name/{group.group_name}',
                        "update": f'{api_base_url}/groups/update',
                        "delete": f'{api_base_url}/groups/delete/{group.group_name}',
                        "groups": f'{api_base_url}/groups',
                        "advisor": f'{api_base_url}/teachers/search/by_id/{advisor_id}',
                        "speciality": f'{api_base_url}/specialities/search/by_speciality_code/{group.speciality_code}' if group.speciality_code else None,
                        "sessions": f'{api_base_url}/sessions/search/by_group/{group.group_name}',
                        "streams": f'{api_base_url}/streams/search/by_group/{group.group_name}',
                        "teachers_in_plans": f'{api_base_url}/teachers_in_plans/search/by_group/{group.group_name}'
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowGroupWithHATEOAS(group=group_pydantic, links=hateoas_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"Неожиданная ошибка при получении группы по преподавателю {advisor_id}: {e}", exc_info=True)
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при получении группы по преподавателю.")


    async def _get_all_groups(self, page: int, limit: int, request: Request, db) -> ShowGroupListWithHATEOAS:
        async with db as session:
            async with session.begin():
                group_dal = GroupDAL(session)
                try:
                    groups = await group_dal.get_all_groups(page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    groups_with_hateoas = []
                    for group in groups:
                        group_pydantic = ShowGroup.model_validate(group, from_attributes=True)
                        group_name = group.group_name
                        group_links = {
                            "self": f'{api_base_url}/groups/search/by_group_name/{group_name}',
                            "update": f'{api_base_url}/groups/update',
                            "delete": f'{api_base_url}/groups/delete/{group_name}',
                            "groups": f'{api_base_url}/groups',
                            "advisor": f'{api_base_url}/teachers/search/by_id/{group.group_advisor_id}' if group.group_advisor_id else None,
                            "speciality": f'{api_base_url}/specialities/search/by_speciality_code/{group.speciality_code}' if group.speciality_code else None,
                            "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}',
                            "streams": f'{api_base_url}/streams/search/by_group/{group_name}',
                            "teachers_in_plans": f'{api_base_url}/teachers_in_plans/search/by_group/{group_name}'
                        }
                        group_links = {k: v for k, v in group_links.items() if v is not None}
                        group_with_links = ShowGroupWithHATEOAS(group=group_pydantic, links=group_links)
                        groups_with_hateoas.append(group_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/groups/search?page={page}&limit={limit}',
                        "create": f'{api_base_url}/groups/create'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowGroupListWithHATEOAS(groups=groups_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение групп отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_groups_by_speciality(self, speciality_code: str, page: int, limit: int, request: Request, db) -> ShowGroupListWithHATEOAS:
        async with db as session:
            async with session.begin():
                speciality_dal = SpecialityDAL(session)
                group_dal = GroupDAL(session)
                try:
                    if not await ensure_speciality_exists(speciality_dal, speciality_code):
                        raise HTTPException(status_code=404, detail=f"Специальность с кодом {speciality_code} не найдена")

                    groups = await group_dal.get_groups_by_speciality(speciality_code, page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    groups_with_hateoas = []
                    for group in groups:
                        group_pydantic = ShowGroup.model_validate(group, from_attributes=True)
                        group_name = group.group_name
                        group_links = {
                            "self": f'{api_base_url}/groups/search/by_group_name/{group_name}',
                            "update": f'{api_base_url}/groups/update',
                            "delete": f'{api_base_url}/groups/delete/{group_name}',
                            "groups": f'{api_base_url}/groups',
                            "advisor": f'{api_base_url}/teachers/search/by_id/{group.group_advisor_id}' if group.group_advisor_id else None,
                            "speciality": f'{api_base_url}/specialities/search/by_speciality_code/{speciality_code}',
                            "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}',
                            "streams": f'{api_base_url}/streams/search/by_group/{group_name}',
                            "teachers_in_plans": f'{api_base_url}/teachers_in_plans/search/by_group/{group_name}'
                        }
                        group_links = {k: v for k, v in group_links.items() if v is not None}
                        group_with_links = ShowGroupWithHATEOAS(group=group_pydantic, links=group_links)
                        groups_with_hateoas.append(group_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/groups/search/by_speciality/{speciality_code}?page={page}&limit={limit}',
                        "create": f'{api_base_url}/groups/create',
                        "speciality": f'{api_base_url}/specialities/search/by_speciality_code/{speciality_code}'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowGroupListWithHATEOAS(groups=groups_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение групп для специальности {speciality_code} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _delete_group(self, group_name: str, request: Request, db) -> ShowGroupWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    group_dal = GroupDAL(session)
                    group = await group_dal.delete_group(group_name)
                    if not group:
                        raise HTTPException(status_code=404, detail=f"Группа с названием: {group_name} не найдена")

                    group_pydantic = ShowGroup.model_validate(group, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "groups": f'{api_base_url}/groups',
                        "create": f'{api_base_url}/groups/create'
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowGroupWithHATEOAS(group=group_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при удалении группы {group_name}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении группы.")


    async def _update_group(self, body: UpdateGroup, request: Request, db) -> ShowGroupWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["group_name", "new_group_name"]}
                    
                    if body.new_group_name is not None:
                        update_data["group_name"] = body.new_group_name
                        
                        group_dal = GroupDAL(session)
                        if not await ensure_group_unique(group_dal, body.new_group_name):
                            raise HTTPException(status_code=400, detail=f"Группа {body.new_group_name} уже существует")

                    group_dal = GroupDAL(session)
                    teacher_dal = TeacherDAL(session)
                    speciality_dal = SpecialityDAL(session)
                    payment_dal = PaymentFormDAL(session)

                    if not await ensure_group_exists(group_dal, body.group_name):
                        raise HTTPException(status_code=404, detail=f"Группа {body.group_name} не найдена")

                    if "group_advisor_id" in update_data and update_data["group_advisor_id"] is not None:
                        if not await ensure_teacher_exists(teacher_dal, update_data["group_advisor_id"]):
                            raise HTTPException(status_code=404, detail=f"Преподаватель с id {update_data['group_advisor_id']} не найден")
                    if "speciality_code" in update_data and update_data["speciality_code"] is not None:
                        if not await ensure_speciality_exists(speciality_dal, update_data["speciality_code"]):
                            raise HTTPException(status_code=404, detail=f"Специальность с кодом {update_data['speciality_code']} не найдена")
                    if "payment" in update_data and update_data["payment"] is not None:
                        if not await ensure_payment_form_exists(payment_dal, body.payment_form):
                            raise HTTPException(status_code=404, detail=f"Форма оплаты {body.payment_form} не найдена")
                    
                    group = await group_dal.update_group(target_group_name=body.group_name, **update_data)
                    if not group:
                        raise HTTPException(status_code=404, detail=f"Группа {body.group_name} не найдена")

                    group_name = group.group_name
                    group_pydantic = ShowGroup.model_validate(group, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/groups/search/by_group_name/{group_name}',
                        "update": f'{api_base_url}/groups/update',
                        "delete": f'{api_base_url}/groups/delete/{group_name}',
                        "groups": f'{api_base_url}/groups',
                        "advisor": f'{api_base_url}/teachers/search/by_id/{group.group_advisor_id}' if group.group_advisor_id else None,
                        "speciality": f'{api_base_url}/specialities/search/by_speciality_code/{group.speciality_code}' if group.speciality_code else None,
                        "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}',
                        "streams": f'{api_base_url}/streams/search/by_group/{group_name}',
                        "teachers_in_plans": f'{api_base_url}/teachers_in_plans/search/by_group/{group_name}'
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowGroupWithHATEOAS(group=group_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.warning(f"Изменение данных о группе отменено (Ошибка: {e})")
                raise e
                