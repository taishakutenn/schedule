from api.teacher_category.teacher_category_pydantic import *
from api.services_helpers import ensure_category_unique
from api.teacher_category.teacher_category_DAL import TeacherCategoryDAL
from fastapi import HTTPException, status, Request

from config.logging_config import configure_logging

# Create logger object
logger = configure_logging()


class TeacherCategoryService:
    async def _create_new_category(body: CreateTeacherCategory, request: Request, db) -> ShowTeacherCategoryWithHATEOAS:
        async with db as session:
            async with session.begin():
                category_dal = TeacherCategoryDAL(session)
                try:
                    if not await ensure_category_unique(category_dal, body.teacher_category):
                        raise HTTPException(status_code=400,
                                            detail=f"Категория преподавателя '{body.teacher_category}' уже существует")

                    new_category_orm = await category_dal.create_teacher_category(
                        teacher_category=body.teacher_category
                    )
                    new_category_pydantic = ShowTeacherCategory.model_validate(new_category_orm, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/categories/search/{new_category_orm.teacher_category}',
                        "update": f'{api_base_url}/categories/update',
                        "delete": f'{api_base_url}/categories/delete/{new_category_orm.teacher_category}',
                        "categories": f'{api_base_url}/categories',
                    }

                    return ShowTeacherCategoryWithHATEOAS(category=new_category_pydantic, links=hateoas_links)

                except HTTPException:
                    await session.rollback()
                    raise
                except Exception as e:
                    await session.rollback()
                    logger.error(
                        f"Неожиданная ошибка при создании категории преподавателя '{body.teacher_category}': {e}",
                        exc_info=True)
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                        detail="Внутренняя ошибка сервера при создании категории преподавателя.")

    async def _get_category(teacher_category: str, request: Request, db) -> ShowTeacherCategoryWithHATEOAS:
        async with db as session:
            async with session.begin():
                category_dal = TeacherCategoryDAL(session)
                try:
                    category_orm = await category_dal.get_teacher_category(teacher_category)
                    if not category_orm:
                        raise HTTPException(status_code=404,
                                            detail=f"Категория преподавателя '{teacher_category}' не найдена")

                    category_pydantic = ShowTeacherCategory.model_validate(category_orm, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/categories/search/{teacher_category}',
                        "update": f'{api_base_url}/categories/update',
                        "delete": f'{api_base_url}/categories/delete/{teacher_category}',
                        "categories": f'{api_base_url}/categories',
                    }

                    return ShowTeacherCategoryWithHATEOAS(category=category_pydantic, links=hateoas_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"Неожиданная ошибка при получении категории преподавателя '{teacher_category}': {e}",
                                 exc_info=True)
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                        detail="Внутренняя ошибка сервера при получении категории преподавателя.")

    async def _get_all_categories(page: int, limit: int, request: Request, db) -> ShowTeacherCategoryListWithHATEOAS:
        async with db as session:
            async with session.begin():
                category_dal = TeacherCategoryDAL(session)
                try:
                    categories_orm_list = await category_dal.get_all_teacher_categories(page, limit)
                    if categories_orm_list is None:
                        categories_orm_list = []

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    categories_with_hateoas = []
                    for category_orm in categories_orm_list:
                        category_pydantic = ShowTeacherCategory.model_validate(category_orm, from_attributes=True)
                        category_links = {
                            "self": f'{api_base_url}/categories/search/{category_orm.teacher_category}',
                            "update": f'{api_base_url}/categories/update',
                            "delete": f'{api_base_url}/categories/delete/{category_orm.teacher_category}',
                            "categories": f'{api_base_url}/categories',
                        }
                        category_with_links = ShowTeacherCategoryWithHATEOAS(category=category_pydantic,
                                                                             links=category_links)
                        categories_with_hateoas.append(category_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/categories/search?page={page}&limit={limit}',
                        "create": f'{api_base_url}/categories/create',
                    }

                    return ShowTeacherCategoryListWithHATEOAS(categories=categories_with_hateoas,
                                                              links=collection_links)

                except Exception as e:
                    logger.error(
                        f"Неожиданная ошибка при получении списка категорий преподавателей (page={page}, limit={limit}): {e}",
                        exc_info=True)
                    raise HTTPException(status_code=500,
                                        detail="Внутренняя ошибка сервера при получении списка категорий преподавателей.")

    async def _delete_category(teacher_category: str, request: Request, db) -> ShowTeacherCategoryWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    category_dal = TeacherCategoryDAL(session)
                    deleted_category_orm = await category_dal.delete_teacher_category(teacher_category)
                    if not deleted_category_orm:
                        raise HTTPException(status_code=404,
                                            detail=f"Категория преподавателя '{teacher_category}' не найдена для удаления")

                    deleted_category_pydantic = ShowTeacherCategory.model_validate(deleted_category_orm,
                                                                                   from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "categories": f'{api_base_url}/categories',
                    }

                    return ShowTeacherCategoryWithHATEOAS(category=deleted_category_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при удалении категории преподавателя '{teacher_category}': {e}",
                             exc_info=True)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="Внутренняя ошибка сервера при удалении категории преподавателя.")

    async def _update_category(body: UpdateTeacherCategory, request: Request, db) -> ShowTeacherCategoryWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    update_data = {key: value for key, value in body.dict().items() if
                                   value is not None and key not in ["teacher_category", "new_teacher_category"]}

                    target_category = body.teacher_category
                    if body.new_teacher_category is not None:
                        update_data["teacher_category"] = body.new_teacher_category
                        category_dal = TeacherCategoryDAL(session)
                        if target_category != body.new_teacher_category and not await ensure_category_unique(
                                category_dal,
                                body.new_teacher_category):
                            raise HTTPException(status_code=400,
                                                detail=f"Категория преподавателя '{body.new_teacher_category}' уже существует")

                    category_dal = TeacherCategoryDAL(session)
                    updated_category_orm = await category_dal.update_teacher_category(target_category, **update_data)
                    if not updated_category_orm:
                        raise HTTPException(status_code=404,
                                            detail=f"Категория преподавателя '{target_category}' не найдена для обновления")

                    updated_category_pydantic = ShowTeacherCategory.model_validate(updated_category_orm,
                                                                                   from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/categories/search/{updated_category_orm.teacher_category}',
                        "delete": f'{api_base_url}/categories/delete/{updated_category_orm.teacher_category}',
                        "categories": f'{api_base_url}/categories',
                    }

                    return ShowTeacherCategoryWithHATEOAS(category=updated_category_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(
                    f"Неожиданная ошибка при обновлении категории преподавателя '{body.teacher_category}': {e}",
                    exc_info=True)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="Внутренняя ошибка сервера при обновлении категории преподавателя.")
