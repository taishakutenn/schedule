from api.teacher.teacher_pydantic import *
from api.services_helpers import ensure_category_exists, ensure_teacher_email_unique, ensure_teacher_exists, ensure_teacher_phone_unique
from api.teacher.teacher_DAL import TeacherDAL
from api.teacher_category.teacher_category_DAL import TeacherCategoryDAL
from fastapi import HTTPException, status, Request

from config.logging_config import configure_logging

# Create logger object
logger = configure_logging()


class TeacherService:
    async def _create_new_teacher(self, body: CreateTeacher, request: Request, db) -> ShowTeacherWithHATEOAS:
        async with db as session:
            async with session.begin():
                teacher_dal = TeacherDAL(session)
                category_dal = TeacherCategoryDAL(session)
                try:
                    if not await ensure_teacher_phone_unique(teacher_dal, body.phone_number):
                        raise HTTPException(status_code=400, detail=f"Преподаватель с номером телефона '{body.phone_number}' уже существует")
                    if body.email and not await ensure_teacher_email_unique(teacher_dal, body.email):
                        raise HTTPException(status_code=400, detail=f"Преподаватель с email '{body.email}' уже существует")

                    if body.teacher_category and not await ensure_category_exists(category_dal, body.teacher_category):
                        raise HTTPException(status_code=404, detail=f"Категория преподавателя '{body.teacher_category}' не найдена")

                    new_teacher_orm = await teacher_dal.create_teacher(
                        name=body.name,
                        surname=body.surname,
                        fathername=body.fathername,
                        phone_number=body.phone_number,
                        email=body.email,
                        teacher_category=body.teacher_category
                    )
                    new_teacher_pydantic = ShowTeacher.model_validate(new_teacher_orm, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/teachers/search/by_id/{new_teacher_orm.id}',
                        "update": f'{api_base_url}/teachers/update',
                        "delete": f'{api_base_url}/teachers/delete/{new_teacher_orm.id}',
                        "teachers": f'{api_base_url}/teachers',
                        "category": f'{api_base_url}/categories/search/{new_teacher_orm.teacher_category}' if new_teacher_orm.teacher_category else None
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowTeacherWithHATEOAS(teacher=new_teacher_pydantic, links=hateoas_links)

                except HTTPException:
                    await session.rollback()
                    raise
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Неожиданная ошибка при создании преподавателя '{body.name} {body.surname}': {e}", exc_info=True)
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка сервера при создании преподавателя.")


    async def _get_teacher_by_id(self, teacher_id: int, request: Request, db) -> ShowTeacherWithHATEOAS:
        async with db as session:
            async with session.begin():
                teacher_dal = TeacherDAL(session)
                try:
                    teacher_orm = await teacher_dal.get_teacher_by_id(teacher_id)
                    if not teacher_orm:
                        raise HTTPException(status_code=404, detail=f"Преподаватель с id: {teacher_id} не найден")

                    teacher_pydantic = ShowTeacher.model_validate(teacher_orm, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/teachers/search/by_id/{teacher_id}',
                        "update": f'{api_base_url}/teachers/update',
                        "delete": f'{api_base_url}/teachers/delete/{teacher_id}',
                        "teachers": f'{api_base_url}/teachers',
                        "category": f'{api_base_url}/categories/search/{teacher_orm.teacher_category}' if teacher_orm.teacher_category else None
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowTeacherWithHATEOAS(teacher=teacher_pydantic, links=hateoas_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"Неожиданная ошибка при получении преподавателя с id: {teacher_id}: {e}", exc_info=True)
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка сервера при получении преподавателя.")


    async def _get_all_teachers(self, page: int, limit: int, request: Request, db) -> ShowTeacherListWithHATEOAS:
        async with db as session:
            async with session.begin():
                teacher_dal = TeacherDAL(session)
                try:
                    teachers_orm_list = await teacher_dal.get_all_teachers(page, limit)
                    if teachers_orm_list is None:
                        teachers_orm_list = []

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    teachers_with_hateoas = []
                    for teacher_orm in teachers_orm_list:
                        teacher_pydantic = ShowTeacher.model_validate(teacher_orm, from_attributes=True)
                        teacher_links = {
                            "self": f'{api_base_url}/teachers/search/by_id/{teacher_orm.id}',
                            "update": f'{api_base_url}/teachers/update',
                            "delete": f'{api_base_url}/teachers/delete/{teacher_orm.id}',
                            "teachers": f'{api_base_url}/teachers',
                            "category": f'{api_base_url}/categories/search/{teacher_orm.teacher_category}' if teacher_orm.teacher_category else None
                        }
                        teacher_links = {k: v for k, v in teacher_links.items() if v is not None}
                        teacher_with_links = ShowTeacherWithHATEOAS(teacher=teacher_pydantic, links=teacher_links)
                        teachers_with_hateoas.append(teacher_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/teachers/search?page={page}&limit={limit}',
                        "create": f'{api_base_url}/teachers/create',
                    }

                    return ShowTeacherListWithHATEOAS(teachers=teachers_with_hateoas, links=collection_links)

                except Exception as e:
                    logger.error(f"Неожиданная ошибка при получении списка преподавателей (page={page}, limit={limit}): {e}", exc_info=True)
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при получении списка преподавателей.")


    async def _delete_teacher(self, teacher_id: int, request: Request, db) -> ShowTeacherWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    teacher_dal = TeacherDAL(session)
                    deleted_teacher_orm = await teacher_dal.delete_teacher(teacher_id)
                    if not deleted_teacher_orm:
                        raise HTTPException(status_code=404, detail=f"Преподаватель с id: {teacher_id} не найден для удаления")

                    deleted_teacher_pydantic = ShowTeacher.model_validate(deleted_teacher_orm, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "teachers": f'{api_base_url}/teachers',
                    }

                    return ShowTeacherWithHATEOAS(teacher=deleted_teacher_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при удалении преподавателя с id: {teacher_id}: {e}", exc_info=True)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка сервера при удалении преподавателя.")


    async def _update_teacher(self, body: UpdateTeacher, request: Request, db) -> ShowTeacherWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    teacher_dal = TeacherDAL(session)
                    category_dal = TeacherCategoryDAL(session) 

                    if not await ensure_teacher_exists(teacher_dal, body.id):
                        raise HTTPException(status_code=404, detail=f"Преподаватель с id: {body.id} не найден для обновления")

                    update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["id"]}

                    if 'email' in update_data and update_data['email'] is not None:
                        if not await ensure_teacher_email_unique(teacher_dal, update_data['email'], exclude_id=body.id):
                            raise HTTPException(status_code=400, detail=f"Email '{update_data['email']}' уже используется другим преподавателем")
                    if 'phone_number' in update_data:
                        if not await ensure_teacher_phone_unique(teacher_dal, update_data['phone_number'], exclude_id=body.id):
                            raise HTTPException(status_code=400, detail=f"Номер телефона '{update_data['phone_number']}' уже используется другим преподавателем")

                    if 'teacher_category' in update_data and update_data['teacher_category'] is not None:
                        if not await ensure_category_exists(category_dal, update_data['teacher_category']):
                            raise HTTPException(status_code=404, detail=f"Категория преподавателя '{update_data['teacher_category']}' не найдена")

                    updated_teacher_orm = await teacher_dal.update_teacher(id=body.id, **update_data)
                    if not updated_teacher_orm:
                        raise HTTPException(status_code=404, detail=f"Преподаватель с id: {body.id} не найден для обновления")

                    updated_teacher_pydantic = ShowTeacher.model_validate(updated_teacher_orm, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/teachers/search/by_id/{updated_teacher_orm.id}',
                        "delete": f'{api_base_url}/teachers/delete/{updated_teacher_orm.id}',
                        "teachers": f'{api_base_url}/teachers',
                        "category": f'{api_base_url}/categories/search/{updated_teacher_orm.teacher_category}' if updated_teacher_orm.teacher_category else None
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowTeacherWithHATEOAS(teacher=updated_teacher_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при обновлении преподавателя с id: {body.id}: {e}", exc_info=True)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка сервера при обновлении преподавателя.")
