from api.teacher_building.teacher_building_pydantic import *
from api.services_helpers import  ensure_building_exists, ensure_teacher_building_exists, ensure_teacher_exists
from api.teacher_building.teacher_building_DAL import TeacherBuildingDAL
from api.teacher.teacher_DAL import TeacherDAL
from api.building.building_DAL import BuildingDAL 
from fastapi import HTTPException, Request

from config.logging_config import configure_logging

# Create logger object
logger = configure_logging()


class TeacherBuildingService:
    async def _create_new_teacher_building(self, body: CreateTeacherBuilding, request: Request, db) -> ShowTeacherBuildingWithHATEOAS:
        async with db as session:
            async with session.begin():
                teacher_dal = TeacherDAL(session)
                building_dal = BuildingDAL(session)
                teacher_building_dal = TeacherBuildingDAL(session)
                try:
                    if not await ensure_teacher_exists(teacher_dal, body.teacher_id):
                        raise HTTPException(status_code=404, detail=f"Преподаватель с id {body.teacher_id} не найден")
                    if not await ensure_building_exists(building_dal, body.building_number):
                        raise HTTPException(status_code=404, detail=f"Здание с номером {body.building_number} не найдено")

                    teacher_building = await teacher_building_dal.create_teacher_building(
                        teacher_id=body.teacher_id,
                        building_number=body.building_number
                    )
                    teacher_building_id = teacher_building.id
                    teacher_building_pydantic = ShowTeacherBuilding.model_validate(teacher_building, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/teachers_buildings/search/by_id/{teacher_building_id}',
                        "update": f'{api_base_url}/teachers_buildings/update',
                        "delete": f'{api_base_url}/teachers_buildings/delete/{teacher_building_id}',
                        "teachers_buildings": f'{api_base_url}/teachers_buildings',
                        "teacher": f'{api_base_url}/teachers/search/by_id/{body.teacher_id}',
                        "building": f'{api_base_url}/buildings/search/by_number/{body.building_number}'
                    }

                    return ShowTeacherBuildingWithHATEOAS(teacher_building=teacher_building_pydantic, links=hateoas_links)

                except HTTPException:
                    await session.rollback()
                    raise
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Неожиданная ошибка при создании связи преподавателя и здания: {e}", exc_info=True)
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_teacher_building_by_id(self, teacher_building_id: int, request: Request, db) -> ShowTeacherBuildingWithHATEOAS:
        async with db as session:
            async with session.begin():
                teacher_building_dal = TeacherBuildingDAL(session)
                try:
                    if not await ensure_teacher_building_exists(teacher_building_dal, teacher_building_id):
                        raise HTTPException(status_code=404, detail=f"Связь преподавателя и здания с id {teacher_building_id} не найдена")

                    teacher_building = await teacher_building_dal.get_teacher_building_by_id(teacher_building_id)
                    teacher_building_pydantic = ShowTeacherBuilding.model_validate(teacher_building, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/teachers_buildings/search/by_id/{teacher_building_id}',
                        "update": f'{api_base_url}/teachers_buildings/update',
                        "delete": f'{api_base_url}/teachers_buildings/delete/{teacher_building_id}',
                        "teachers_buildings": f'{api_base_url}/teachers_buildings',
                        "teacher": f'{api_base_url}/teachers/search/by_id/{teacher_building.teacher_id}',
                        "building": f'{api_base_url}/buildings/search/by_number/{teacher_building.building_number}'
                    }

                    return ShowTeacherBuildingWithHATEOAS(teacher_building=teacher_building_pydantic, links=hateoas_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение связи преподавателя и здания {teacher_building_id} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_teachers_buildings_by_teacher(self, teacher_id: int, page: int, limit: int, request: Request, db) -> ShowTeacherBuildingListWithHATEOAS:
        async with db as session:
            async with session.begin():
                teacher_dal = TeacherDAL(session)
                teacher_building_dal = TeacherBuildingDAL(session)
                try:
                    if not await ensure_teacher_exists(teacher_dal, teacher_id):
                        raise HTTPException(status_code=404, detail=f"Преподаватель с id {teacher_id} не найден")

                    teacher_buildings = await teacher_building_dal.get_teachers_buildings_by_teacher(teacher_id, page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    teacher_buildings_with_hateoas = []
                    for teacher_building in teacher_buildings:
                        teacher_building_pydantic = ShowTeacherBuilding.model_validate(teacher_building, from_attributes=True)
                        teacher_building_id = teacher_building.id
                        teacher_building_links = {
                            "self": f'{api_base_url}/teachers_buildings/search/by_id/{teacher_building_id}',
                            "update": f'{api_base_url}/teachers_buildings/update',
                            "delete": f'{api_base_url}/teachers_buildings/delete/{teacher_building_id}',
                            "teachers_buildings": f'{api_base_url}/teachers_buildings',
                            "teacher": f'{api_base_url}/teachers/search/by_id/{teacher_id}',
                            "building": f'{api_base_url}/buildings/search/by_number/{teacher_building.building_number}'
                        }
                        teacher_building_with_links = ShowTeacherBuildingWithHATEOAS(teacher_building=teacher_building_pydantic, links=teacher_building_links)
                        teacher_buildings_with_hateoas.append(teacher_building_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/teachers_buildings/search/by_teacher/{teacher_id}?page={page}&limit={limit}',
                        "create": f'{api_base_url}/teachers_buildings/create',
                        "teacher": f'{api_base_url}/teachers/search/by_id/{teacher_id}'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowTeacherBuildingListWithHATEOAS(teacher_buildings=teacher_buildings_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение связей преподавателя и зданий для преподавателя {teacher_id} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_teachers_buildings_by_building(self, building_number: int, page: int, limit: int, request: Request, db) -> ShowTeacherBuildingListWithHATEOAS:
        async with db as session:
            async with session.begin():
                building_dal = BuildingDAL(session)
                teacher_building_dal = TeacherBuildingDAL(session)
                try:
                    if not await ensure_building_exists(building_dal, building_number):
                        raise HTTPException(status_code=404, detail=f"Здание с номером {building_number} не найдено")

                    teacher_buildings = await teacher_building_dal.get_teachers_buildings_by_building(building_number, page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    teacher_buildings_with_hateoas = []
                    for teacher_building in teacher_buildings:
                        teacher_building_pydantic = ShowTeacherBuilding.model_validate(teacher_building, from_attributes=True)
                        teacher_building_id = teacher_building.id
                        teacher_building_links = {
                            "self": f'{api_base_url}/teachers_buildings/search/by_id/{teacher_building_id}',
                            "update": f'{api_base_url}/teachers_buildings/update',
                            "delete": f'{api_base_url}/teachers_buildings/delete/{teacher_building_id}',
                            "teachers_buildings": f'{api_base_url}/teachers_buildings',
                            "teacher": f'{api_base_url}/teachers/search/by_id/{teacher_building.teacher_id}',
                            "building": f'{api_base_url}/buildings/search/by_number/{building_number}'
                        }
                        teacher_building_with_links = ShowTeacherBuildingWithHATEOAS(teacher_building=teacher_building_pydantic, links=teacher_building_links)
                        teacher_buildings_with_hateoas.append(teacher_building_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/teachers_buildings/search/by_building/{building_number}?page={page}&limit={limit}',
                        "create": f'{api_base_url}/teachers_buildings/create',
                        "building": f'{api_base_url}/buildings/search/by_number/{building_number}'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowTeacherBuildingListWithHATEOAS(teacher_buildings=teacher_buildings_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение связей преподавателей и здания для здания {building_number} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_all_teachers_buildings(self, page: int, limit: int, request: Request, db) -> ShowTeacherBuildingListWithHATEOAS:
        async with db as session:
            async with session.begin():
                teacher_building_dal = TeacherBuildingDAL(session)
                try:
                    teacher_buildings = await teacher_building_dal.get_all_teachers_buildings(page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    teacher_buildings_with_hateoas = []
                    for teacher_building in teacher_buildings:
                        teacher_building_pydantic = ShowTeacherBuilding.model_validate(teacher_building, from_attributes=True)
                        teacher_building_id = teacher_building.id
                        teacher_building_links = {
                            "self": f'{api_base_url}/teachers_buildings/search/by_id/{teacher_building_id}',
                            "update": f'{api_base_url}/teachers_buildings/update',
                            "delete": f'{api_base_url}/teachers_buildings/delete/{teacher_building_id}',
                            "teachers_buildings": f'{api_base_url}/teachers_buildings',
                            "teacher": f'{api_base_url}/teachers/search/by_id/{teacher_building.teacher_id}',
                            "building": f'{api_base_url}/buildings/search/by_number/{teacher_building.building_number}'
                        }
                        teacher_building_with_links = ShowTeacherBuildingWithHATEOAS(teacher_building=teacher_building_pydantic, links=teacher_building_links)
                        teacher_buildings_with_hateoas.append(teacher_building_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/teachers_buildings/search?page={page}&limit={limit}',
                        "create": f'{api_base_url}/teachers_buildings/create'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowTeacherBuildingListWithHATEOAS(teacher_buildings=teacher_buildings_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение связей преподавателей и зданий отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _delete_teacher_building(self, teacher_building_id: int, request: Request, db) -> ShowTeacherBuildingWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    teacher_building_dal = TeacherBuildingDAL(session)
                    
                    if not await ensure_teacher_building_exists(teacher_building_dal, teacher_building_id):
                        raise HTTPException(status_code=404, detail=f"Связь преподавателя и здания с id {teacher_building_id} не найдена")

                    teacher_building = await teacher_building_dal.delete_teacher_building(teacher_building_id)
                    
                    if not teacher_building:
                        raise HTTPException(status_code=404, detail=f"Связь преподавателя и здания с id {teacher_building_id} не найдена")

                    teacher_building_pydantic = ShowTeacherBuilding.model_validate(teacher_building, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "teachers_buildings": f'{api_base_url}/teachers_buildings',
                        "create": f'{api_base_url}/teachers_buildings/create'
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowTeacherBuildingWithHATEOAS(teacher_building=teacher_building_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при удалении связи преподавателя и здания {teacher_building_id}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении связи преподавателя и здания.")


    async def _update_teacher_building(self, body: UpdateTeacherBuilding, request: Request, db) -> ShowTeacherBuildingWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["teacher_building_id"]}
                    
                    if "teacher_id" in update_data:
                        teacher_dal = TeacherDAL(session)
                        if not await ensure_teacher_exists(teacher_dal, update_data["teacher_id"]):
                            raise HTTPException(status_code=404, detail=f"Преподаватель с id {update_data['teacher_id']} не найден")
                    if "building_number" in update_data:
                        building_dal = BuildingDAL(session)
                        if not await ensure_building_exists(building_dal, update_data["building_number"]):
                            raise HTTPException(status_code=404, detail=f"Здание с номером {update_data['building_number']} не найдено")

                    teacher_building_dal = TeacherBuildingDAL(session)

                    if not await ensure_teacher_building_exists(teacher_building_dal, body.teacher_building_id):
                        raise HTTPException(status_code=404, detail=f"Связь преподавателя и здания с id {body.teacher_building_id} не найдена")

                    teacher_building = await teacher_building_dal.update_teacher_building(target_id=body.teacher_building_id, **update_data)
                    if not teacher_building:
                        raise HTTPException(status_code=404, detail=f"Связь преподавателя и здания с id {body.teacher_building_id} не найдена")

                    teacher_building_id = teacher_building.id
                    teacher_building_pydantic = ShowTeacherBuilding.model_validate(teacher_building, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/teachers_buildings/search/by_id/{teacher_building_id}',
                        "update": f'{api_base_url}/teachers_buildings/update',
                        "delete": f'{api_base_url}/teachers_buildings/delete/{teacher_building_id}',
                        "teachers_buildings": f'{api_base_url}/teachers_buildings',
                        "teacher": f'{api_base_url}/teachers/search/by_id/{teacher_building.teacher_id}',
                        "building": f'{api_base_url}/buildings/search/by_number/{teacher_building.building_number}'
                    }

                    return ShowTeacherBuildingWithHATEOAS(teacher_building=teacher_building_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.warning(f"Изменение данных о связи преподавателя и здания отменено (Ошибка: {e})")
                raise e
            