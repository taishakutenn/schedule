"""
file for handlers
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Union

# from api.models import ShowTeacher, CreateTeacher, QueryParams, UpdateTeacher, ShowCabinet, CreateCabinet, UpdateCabinet
# from api.models import ShowBuilding, CreateBuilding, UpdateBuilding
from api.models import *
#from api.services_helpers import ensure_building_exists, ensure_cabinet_unique, ensure_group_unique, ensure_speciality_exists, ensure_teacher_exists, ensure_group_exists, ensure_subject_exists, ensure_subject_unique, ensure_employment_unique, ensure_request_unique, ensure_session_unique, ensure_cabinet_exists, ensure_teacher_group_relation_unique, ensure_teacher_subject_relation_unique
#from db.dals import TeacherDAL, BuildingDAL, CabinetDAL, SpecialityDAL, GroupDAL, SubjectDAL, EmployTeacherDAL, TeacherRequestDAL, SessionDAL, 
from api.services_helpers import ensure_category_exists, ensure_category_unique, ensure_teacher_email_unique, ensure_teacher_exists, ensure_teacher_phone_unique
from db.dals import TeacherCategoryDAL, TeacherDAL
from db.session import get_db

from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status, Request

from config.logging_config import configure_logging

# Create logger object
logger = configure_logging()

teacher_router = APIRouter()  # Create router for teachers
building_router = APIRouter()  # Create router for buildings
cabinet_router = APIRouter()  # Create route for cabinets
speciality_router = APIRouter() # Create router for speciality
group_router = APIRouter() # Create router for group
curriculum_router = APIRouter() # Create router for curriculum
subject_router = APIRouter() # Create router for subject
employment_router = APIRouter() # Create router for EmploymentTeacher
request_router = APIRouter() # Create router for TeacherRequest
session_router = APIRouter() # Create router for Session
teachers_groups_router = APIRouter() # Create router for teacher and his groups
teachers_subjects_router = APIRouter() # Create router for teacher and his subjects


'''
==============================
CRUD operations for Teacher
==============================
'''

async def _create_new_teacher(body: CreateTeacher, request: Request, db) -> ShowTeacherWithHATEOAS:
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
                    salary_rate=body.salary_rate,
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


async def _get_teacher_by_id(teacher_id: int, request: Request, db) -> ShowTeacherWithHATEOAS:
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


async def _get_all_teachers(page: int, limit: int, request: Request, db) -> ShowTeacherListWithHATEOAS:
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


async def _delete_teacher(teacher_id: int, request: Request, db) -> ShowTeacherWithHATEOAS:
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


async def _update_teacher(body: UpdateTeacher, request: Request, db) -> ShowTeacherWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                teacher_dal = TeacherDAL(session)
                category_dal = TeacherCategoryDAL(session) 

                if not await ensure_teacher_exists(teacher_dal, body.teacher_id):
                     raise HTTPException(status_code=404, detail=f"Преподаватель с id: {body.teacher_id} не найден для обновления")

                update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["teacher_id"]}

                if 'email' in update_data and update_data['email'] is not None:
                    if not await ensure_teacher_email_unique(teacher_dal, update_data['email'], exclude_id=body.teacher_id):
                        raise HTTPException(status_code=400, detail=f"Email '{update_data['email']}' уже используется другим преподавателем")
                if 'phone_number' in update_data:
                    if not await ensure_teacher_phone_unique(teacher_dal, update_data['phone_number'], exclude_id=body.teacher_id):
                        raise HTTPException(status_code=400, detail=f"Номер телефона '{update_data['phone_number']}' уже используется другим преподавателем")

                if 'teacher_category' in update_data and update_data['teacher_category'] is not None:
                    if not await ensure_category_exists(category_dal, update_data['teacher_category']):
                        raise HTTPException(status_code=404, detail=f"Категория преподавателя '{update_data['teacher_category']}' не найдена")

                updated_teacher_orm = await teacher_dal.update_teacher(id=body.teacher_id, **update_data)
                if not updated_teacher_orm:
                    raise HTTPException(status_code=404, detail=f"Преподаватель с id: {body.teacher_id} не найден для обновления")

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
            logger.error(f"Неожиданная ошибка при обновлении преподавателя с id: {body.teacher_id}: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка сервера при обновлении преподавателя.")


@teacher_router.post("/create", response_model=ShowTeacherWithHATEOAS, status_code=status.HTTP_201_CREATED)
async def create_teacher(body: CreateTeacher, request: Request, db: AsyncSession = Depends(get_db)):
    return await _create_new_teacher(body, request, db)


@teacher_router.get("/search/by_id/{teacher_id}", response_model=ShowTeacherWithHATEOAS, responses={404: {"description": "Преподаватель не найден"}})
async def get_teacher_by_id(teacher_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_teacher_by_id(teacher_id, request, db)


@teacher_router.get("/search", response_model=ShowTeacherListWithHATEOAS, responses={404: {"description": "Преподаватели не найдены"}})
async def get_all_teachers(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_all_teachers(query_param.page, query_param.limit, request, db)


@teacher_router.delete("/delete/{teacher_id}", response_model=ShowTeacherWithHATEOAS, responses={404: {"description": "Преподаватель не найден"}})
async def delete_teacher(teacher_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _delete_teacher(teacher_id, request, db)


@teacher_router.put("/update", response_model=ShowTeacherWithHATEOAS, responses={404: {"description": "Преподаватель не найден"}})
async def update_teacher(body: UpdateTeacher, request: Request, db: AsyncSession = Depends(get_db)):
    return await _update_teacher(body, request, db)


# '''
# ============================
# CRUD operations for Building
# ============================
# '''


# async def _create_new_building(body: CreateBuilding, request: Request, db) -> ShowBuildingWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             building_dal = BuildingDAL(session)
#             try:
#                 building = await building_dal.create_building(
#                     building_number=body.building_number,
#                     city=body.city,
#                     building_address=body.building_address
#                 )

#                 building_number = building.building_number
#                 building_pydantic = ShowBuilding.model_validate(building)

#                 # Add HATEOAS
#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 hateoas_links = {
#                     "self": f'{api_base_url}/buildings/search/by_number/{building_number}',
#                     "update": f'{api_base_url}/buildings/update/{building_number}',
#                     "delete": f'{api_base_url}/buildings/delete/{building_number}',
#                     "buildings": f'{api_base_url}/buildings/search',
#                     "cabinets": f'{api_base_url}/cabinets/search/by_building/{building_number}'
#                 }

#                 return ShowBuildingWithHATEOAS(building=building_pydantic, links=hateoas_links)

#             except IntegrityError as e:
#                 await session.rollback()
#                 logger.error(f"Ошибка целостности БД при создании здания: {e}", exc_info=True)
#                 raise HTTPException(
#                     status_code=400,
#                     detail="Невозможно создать здание из-за конфликта данных."
#                 )

#             except HTTPException:
#                 raise

#             except Exception as e:
#                 await session.rollback()
#                 logger.error(f"Неожиданная ошибка при создании здания: {e}", exc_info=True)
#                 raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


# async def _get_building_by_number(building_number, request: Request, db) -> ShowBuildingWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             building_dal = BuildingDAL(session)

#             try:
#                 building = await building_dal.get_building_by_number(building_number)

#                 # if building exist
#                 if not building:
#                     raise HTTPException(status_code=404, detail=f"Здание с номером: {building_number} не найдено")

#                 building_pydantic = ShowBuilding.model_validate(building)

#                 # Add HATEOAS
#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 hateoas_links = {
#                     "self": f'{api_base_url}/buildings/search/by_number/{building_number}',
#                     "update": f'{api_base_url}/buildings/update/{building_number}',
#                     "delete": f'{api_base_url}/buildings/delete/{building_number}',
#                     "buildings": f'{api_base_url}/buildings/search',
#                     "cabinets": f'{api_base_url}/cabinets/search/by_building/{building_number}'
#                 }

#                 return ShowBuildingWithHATEOAS(building=building_pydantic, links=hateoas_links)

#             except HTTPException:
#                 raise

#             except Exception as e:
#                 logger.warning(f"Получение здания отменено (Ошибка: {e})")
#                 raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


# async def _get_building_by_address(address, request: Request, db) -> ShowBuildingWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             building_dal = BuildingDAL(session)

#             try:
#                 building = await building_dal.get_building_by_address(address)

#                 # if building exist
#                 if not building:
#                     raise HTTPException(status_code=404, detail=f"Здание по адресу: {address} не найдено")

#                 building_number = building.building_number
#                 building_pydantic = ShowBuilding.model_validate(building)

#                 # Add HATEOAS
#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 hateoas_links = {
#                     "self": f'{api_base_url}/buildings/search/by_number/{building_number}',
#                     "update": f'{api_base_url}/buildings/update/{building_number}',
#                     "delete": f'{api_base_url}/buildings/delete/{building_number}',
#                     "buildings": f'{api_base_url}/buildings/search',
#                     "cabinets": f'{api_base_url}/cabinets/search/by_building/{building_number}'
#                 }

#                 return ShowBuildingWithHATEOAS(building=building_pydantic, links=hateoas_links)

#             except HTTPException:
#                 raise

#             except Exception as e:
#                 logger.warning(f"Получение здания отменено (Ошибка: {e})")
#                 raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


# async def _get_all_buildings(page: int, limit: int, request: Request, db) -> ShowBuildingWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             building_dal = BuildingDAL(session)

#             try:
#                 buildings = await building_dal.get_all_buildings(page, limit)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 buildings_with_hateoas = []
#                 for building in buildings:
#                     building_pydantic = ShowBuilding.model_validate(building)

#                     # add HATEOAS
#                     building_number = building.building_number
#                     building_links = {
#                         "self": f'{api_base_url}/buildings/search/by_number/{building_number}',
#                         "update": f'{api_base_url}/buildings/update/{building_number}',
#                         "delete": f'{api_base_url}/buildings/delete/{building_number}',
#                         "buildings": f'{api_base_url}/buildings/search',
#                         "cabinets": f'{api_base_url}/cabinets/search/by_building/{building_number}'
#                     }

#                     building_with_links = ShowBuildingWithHATEOAS(
#                         building=building_pydantic,
#                         links=building_links
#                     )
#                     buildings_with_hateoas.append(building_with_links)

#                 collection_links = {
#                     "self": f'{api_base_url}/building?page={page}&limit={limit}',
#                     "create": f'{api_base_url}/buildings/create'
#                 }
#                 collection_links = {k: v for k, v in collection_links.items() if v is not None}

#                 return ShowBuildingListWithHATEOAS(
#                     buildings=buildings_with_hateoas,
#                     links=collection_links
#                 )

#             except HTTPException:
#                 raise

#             except Exception as e:
#                 logger.warning(f"Получение зданий отменено (Ошибка: {e})")
#                 raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


# async def _delete_building(building_number: int, request: Request, db) -> ShowBuildingWithHATEOAS:
#     async with db as session:
#         try:
#             async with session.begin():
#                 building_dal = BuildingDAL(session)
#                 building = await building_dal.delete_building(building_number)

#                 if not building:
#                     raise HTTPException(status_code=404, detail=f"Здание с номером: {building_number} не найдено")

#                 building_pydantic = ShowBuilding.model_validate(building)

#                 # Add HATEOAS
#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 hateoas_links = {
#                     "self": f'{api_base_url}/buildings/search/by_number/{building_number}',
#                     "buildings": f'{api_base_url}/buildings/search',
#                     "create": f'{api_base_url}/buildings/create',
#                     "cabinets": f'{api_base_url}/cabinets/search/by_building/{building_number}'
#                 }

#                 return ShowBuildingWithHATEOAS(building=building_pydantic, links=hateoas_links)

#         except HTTPException:
#             await session.rollback()
#             raise

#         except Exception as e:
#             await session.rollback()
#             logger.error(f"Неожиданная ошибка при удалении здания {building_number}: {e}", exc_info=True)
#             raise HTTPException(
#                 status_code=500,
#                 detail="Внутренняя ошибка сервера при удалении здания."
#             )


# async def _update_building(body: UpdateBuilding, request: Request, db) -> ShowBuildingWithHATEOAS:
#     async with db as session:
#         try:
#             async with session.begin():
#                 # exclusion of None-fields from the transmitted data
#                 update_data = {
#                     key: value for key, value in body.dict().items() if value is not None and key != "building_number"
#                 }

#                 # Rename field new_building_data to building_data
#                 if "new_building_number" in update_data:
#                     update_data["building_number"] = update_data.pop("new_building_number")

#                 # change data
#                 building_dal = BuildingDAL(session)
#                 building = await building_dal.update_building(
#                     target_number=body.building_number,
#                     **update_data
#                 )

#                 if not building:
#                     raise HTTPException(status_code=404, detail=f"Здание с номером: {body.building_number} не найдено")

#                 building_number = building.building_number
#                 building_pydantic = ShowBuilding.model_validate(building)

#                 # Add HATEOAS
#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 hateoas_links = {
#                     "self": f'{api_base_url}/buildings/search/by_number/{building_number}',
#                     "update": f'{api_base_url}/buildings/update/{building_number}',
#                     "delete": f'{api_base_url}/buildings/delete/{building_number}',
#                     "buildings": f'{api_base_url}/buildings/search',
#                     "cabinets": f'{api_base_url}/cabinets/search/by_building/{building_number}'
#                 }

#                 return ShowBuildingWithHATEOAS(building=building_pydantic, links=hateoas_links)

#         except HTTPException:
#             await session.rollback()
#             raise

#         except Exception as e:
#             await session.rollback()
#             logger.warning(f"Изменение данных о здании отменено (Ошибка: {e})")
#             raise e


# @building_router.post("/create", response_model=ShowBuildingWithHATEOAS, status_code=201)
# async def create_building(body: CreateBuilding, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _create_new_building(body, request, db)


# @building_router.get("/search/by_number/{building_number}", response_model=ShowBuildingWithHATEOAS,
#                      responses={404: {"description": "Здание не найдено"}})
# async def get_building_by_number(building_number: int, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _get_building_by_number(building_number, request, db)


# @building_router.get("/search/by_address/{building_address}", response_model=ShowBuildingWithHATEOAS,
#                      responses={404: {"description": "Здание не найдено"}})
# async def get_building_by_address(address: str, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _get_building_by_address(address, request, db)


# @building_router.get("/search", response_model=ShowBuildingListWithHATEOAS)
# async def get_all_buildings(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
#     return await _get_all_buildings(query_param.page, query_param.limit, request, db)


# @building_router.delete("/delete/{building_number}", response_model=ShowBuildingWithHATEOAS,
#                      responses={404: {"description": "Здание не найдено"}})
# async def delete_building(building_number: int, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _delete_building(building_number, request, db)


# @building_router.put("/update", response_model=ShowBuildingWithHATEOAS,
#                     responses={404: {"description": "Здание не найдено"}})
# async def update_building(body: UpdateBuilding, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _update_building(body, request, db)


# '''
# ===========================
# CRUD operations for Cabinet
# ===========================
# '''


# async def _create_cabinet(body: CreateCabinet, request: Request, db) -> ShowCabinetWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             building_dal = BuildingDAL(session)
#             cabinet_dal = CabinetDAL(session)

#             try:
#                 # Check that the building exists
#                 # Check that the cabinet is unique
#                 # By using helpers
#                 if not await ensure_building_exists(building_dal, body.building_number):
#                     raise HTTPException(
#                         status_code=404,
#                         detail=f"Здание с номером {body.building_number} не найдено"
#                     )

#                 if not await ensure_cabinet_unique(cabinet_dal, body.building_number, body.cabinet_number):
#                     raise HTTPException(
#                         status_code=400,
#                         detail=f"Кабинет {body.cabinet_number} уже существует в здании {body.building_number}"
#                     )

#                 # Create cabinet
#                 cabinet = await cabinet_dal.create_cabinet(
#                     cabinet_number=body.cabinet_number,
#                     building_number=body.building_number,
#                     capacity=body.capacity,
#                     cabinet_state=body.cabinet_state
#                 )

#                 cabinet_number = cabinet.cabinet_number
#                 building_number = cabinet.building_number
#                 cabinet_pydantic = ShowCabinet.model_validate(cabinet)

#                 # add HATEOAS
#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 hateoas_links = {
#                     "self": f'{api_base_url}/cabinets/search/by_building_and_number/{building_number}/{cabinet_number}',
#                     "update": f'{api_base_url}/cabinets/update/{building_number}/{cabinet_number}',
#                     "delete": f'{api_base_url}/cabinets/delete/{building_number}/{cabinet_number}',
#                     "cabinets": f'{api_base_url}/cabinets',
#                     "building": f'{api_base_url}/buildings/search/by_number/{building_number}'
#                 }

#                 return ShowCabinetWithHATEOAS(cabinet=cabinet_pydantic, links=hateoas_links)

#             except IntegrityError as e:
#                 await session.rollback()
#                 logger.error(f"Неожиданная ошибка при создании кабинета: {e}", exc_info=True)
#                 raise HTTPException(status_code=400, detail="Кабинет с таким номером уже существует.")

#             except HTTPException:
#                 await session.rollback()
#                 raise

#             except Exception as e:
#                 await session.rollback()
#                 logger.error(f"Неожиданная ошибка при создании кабинета: {e}", exc_info=True)
#                 raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


# async def _get_all_cabinets(page: int, limit: int, request: Request, db) -> ShowBuildingListWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             cabinet_dal = CabinetDAL(session)
#             try:
#                 cabinets = await cabinet_dal.get_all_cabinets(page, limit)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 cabinets_with_hateoas = []
#                 for cabinet in cabinets:
#                     cabinet_pydantic = ShowCabinet.model_validate(cabinet)

#                     # add HATEOAS
#                     cabinet_number = cabinet.cabinet_number
#                     building_number = cabinet.building_number
#                     cabinet_links = {
#                         "self": f'{api_base_url}/cabinets/search/by_building_and_number/{building_number}/{cabinet_number}',
#                         "update": f'{api_base_url}/cabinets/update/{building_number}/{cabinet_number}',
#                         "delete": f'{api_base_url}/cabinets/delete/{building_number}/{cabinet_number}',
#                         "cabinets": f'{api_base_url}/cabinets',
#                         "building": f'{api_base_url}/buildings/search/by_number/{building_number}'
#                     }

#                     cabinet_with_links = ShowCabinetWithHATEOAS(
#                         cabinet=cabinet_pydantic,
#                         links=cabinet_links
#                     )
#                     cabinets_with_hateoas.append(cabinet_with_links)

#                 collection_links = {
#                     "self": f'{api_base_url}/cabinets?page={page}&limit={limit}',
#                     "create": f'{api_base_url}/cabinets/create'
#                 }
#                 collection_links = {k: v for k, v in collection_links.items() if v is not None}

#                 return ShowCabinetListWithHATEOAS(
#                     cabinets=cabinets_with_hateoas,
#                     links=collection_links
#                 )

#             except HTTPException:
#                 raise

#             except Exception as e:
#                 logger.warning(f"Получение кабинета отменено (Ошибка: {e})")
#                 raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


# async def _get_cabinets_by_building(building_number: int, page: int, limit: int, request: Request, db) -> ShowCabinetListWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             cabinet_dal = CabinetDAL(session)

#             try:
#                 cabinets = await cabinet_dal.get_cabinets_by_building(building_number, page, limit)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 cabinets_with_hateoas = []
#                 for cabinet in cabinets:
#                     cabinet_pydantic = ShowCabinet.model_validate(cabinet)

#                     # add HATEOAS
#                     cabinet_number = cabinet.cabinet_number
#                     cabinet_links = {
#                         "self": f'{api_base_url}/cabinets/search/by_building_and_number/{building_number}/{cabinet_number}',
#                         "update": f'{api_base_url}/cabinets/update/{building_number}/{cabinet_number}',
#                         "delete": f'{api_base_url}/cabinets/delete/{building_number}/{cabinet_number}',
#                         "cabinets": f'{api_base_url}/cabinets',
#                         "building": f'{api_base_url}/buildings/search/by_number/{building_number}'
#                     }

#                     cabinet_with_links = ShowCabinetWithHATEOAS(
#                         cabinet=cabinet_pydantic,
#                         links=cabinet_links
#                     )
#                     cabinets_with_hateoas.append(cabinet_with_links)

#                 collection_links = {
#                     "self": f'{api_base_url}/cabinets?page={page}&limit={limit}',
#                     "create": f'{api_base_url}/cabinets/create'
#                 }
#                 collection_links = {k: v for k, v in collection_links.items() if v is not None}

#                 return ShowCabinetListWithHATEOAS(
#                     cabinets=cabinets_with_hateoas,
#                     links=collection_links
#                 )

#             except HTTPException:
#                 raise

#             except Exception as e:
#                 logger.warning(f"Получение кабинета отменено (Ошибка: {e})")
#                 raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


# async def _get_cabinet_by_building_and_number(building_number: int, cabinet_number: int, request: Request, db) -> ShowCabinetWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             cabinet_dal = CabinetDAL(session)

#             try:
#                 cabinet = await cabinet_dal.get_cabinet_by_number_and_building(building_number, cabinet_number)

#                 if not cabinet:
#                     raise HTTPException(status_code=404,
#                                         detail=f"Кабинет с номером: {cabinet_number} в здании с номером: {building_number} - не найден")

#                 cabinet_number = cabinet.cabinet_number
#                 building_number = cabinet.building_number
#                 cabinet_pydantic = ShowCabinet.model_validate(cabinet)

#                 # add HATEOAS
#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 hateoas_links = {
#                     "self": f'{api_base_url}/cabinets/search/by_building_and_number/{building_number}/{cabinet_number}',
#                     "update": f'{api_base_url}/cabinets/update/{building_number}/{cabinet_number}',
#                     "delete": f'{api_base_url}/cabinets/delete/{building_number}/{cabinet_number}',
#                     "cabinets": f'{api_base_url}/cabinets',
#                     "building": f'{api_base_url}/buildings/search/by_number/{building_number}'
#                 }

#                 return ShowCabinetWithHATEOAS(cabinet=cabinet_pydantic, links=hateoas_links)

#             except HTTPException:
#                 raise

#             except Exception as e:
#                 logger.warning(f"Получение кабинета отменено (Ошибка: {e})")
#                 raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


# async def _delete_cabinet(building_number: int, cabinet_number: int, request: Request, db) -> ShowCabinetWithHATEOAS:
#     async with db as session:
#         try:
#             async with session.begin():
#                 cabinet_dal = CabinetDAL(session)
#                 cabinet = await cabinet_dal.delete_cabinet(building_number, cabinet_number)

#                 if not cabinet:
#                     raise HTTPException(status_code=404,
#                                         detail=f"Кабинет с номером: {cabinet_number} в здании {building_number} не может быть удалён, т.к. не найден")

#                 cabinet_pydantic = ShowCabinet.model_validate(cabinet)

#                 # add HATEOAS
#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 hateoas_links = {
#                     "self": f'{api_base_url}/cabinets/search/by_building_and_number/{building_number}/{cabinet_number}',
#                     "cabinets": f'{api_base_url}/cabinets',
#                     "create": f'{api_base_url}/cabinets/create',
#                     "building": f'{api_base_url}/buildings/search/by_number/{building_number}'
#                 }

#                 return ShowCabinetWithHATEOAS(cabinet=cabinet_pydantic, links=hateoas_links)

#         except HTTPException:
#             await session.rollback()
#             raise

#         except Exception as e:
#             await session.rollback()
#             logger.warning(f"Получение кабинета отменено (Ошибка: {e})")
#             raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


# async def _update_cabinet(body: UpdateCabinet, request: Request, db) -> ShowCabinetWithHATEOAS:
#     async with db as session:
#         try:
#             async with session.begin():
#                 # exclusion of None-fields from the transmitted data
#                 update_data = {
#                     key: value for key, value in body.dict().items() if
#                     value is not None and key not in ["building_number", "cabinet_number"]
#                 }

#                 # Create cabinet dal
#                 cabinet_dal = CabinetDAL(session)

#                 # Rename the fields new_cabinet_number and new_building_number to cabinet_number and building_number
#                 # And check the transferred data, we can change the parameters of the cabinet by using helpers
#                 if "new_building_number" in update_data:
#                     update_data["building_number"] = update_data.pop("new_building_number")
#                     if not await ensure_building_exists(BuildingDAL(session), update_data["building_number"]):
#                         raise HTTPException(
#                             status_code=404,
#                             detail=f"Здание с номером {body.building_number} не найдено"
#                         )

#                 if "new_cabinet_number" in update_data:
#                     update_data["cabinet_number"] = update_data.pop("new_cabinet_number")
#                     if not await ensure_cabinet_unique(cabinet_dal,
#                                                        update_data.get("building_number", body.building_number),
#                                                        update_data["cabinet_number"]):
#                         raise HTTPException(
#                             status_code=400,
#                             detail=f"Кабинет {body.cabinet_number} уже существует в здании {body.building_number}"
#                         )

#                 # Change data
#                 updated_cabinet = await cabinet_dal.update_cabinet(body.building_number, body.cabinet_number, **update_data)

#                 if not updated_cabinet:
#                     raise HTTPException(status_code=404, detail="Кабинет не был обновлён")

#                 cabinet_number = updated_cabinet.cabinet_number
#                 building_number = updated_cabinet.building_number
#                 cabinet_pydantic = ShowCabinet.model_validate(updated_cabinet)

#                 # add HATEOAS
#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 hateoas_links = {
#                     "self": f'{api_base_url}/cabinets/search/by_building_and_number/{building_number}/{cabinet_number}',
#                     "update": f'{api_base_url}/cabinets/update/{building_number}/{cabinet_number}',
#                     "delete": f'{api_base_url}/cabinets/delete/{building_number}/{cabinet_number}',
#                     "cabinets": f'{api_base_url}/cabinets',
#                     "building": f'{api_base_url}/buildings/search/by_number/{building_number}'
#                 }

#                 return ShowCabinetWithHATEOAS(cabinet=cabinet_pydantic, links=hateoas_links)

#         except HTTPException:
#             await session.rollback()
#             raise

#         except Exception as e:
#             await session.rollback()
#             logger.error(f"Неожиданная ошибка при обновлении кабинета {cabinet_number}: {e}", exc_info=True)
#             raise HTTPException(
#                 status_code=500,
#                 detail="Внутренняя ошибка сервера при обновлении кабинета."
#             )


# @cabinet_router.post("/create", response_model=ShowCabinetWithHATEOAS)
# async def create_cabinet(body: CreateCabinet, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _create_cabinet(body, request, db)


# @cabinet_router.get("/search", response_model=ShowCabinetListWithHATEOAS, responses={404: {"description": "Кабинеты не найдены"}})
# async def get_all_cabinets(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
#     return await _get_all_cabinets(query_param.page, query_param.limit, request, db)


# @cabinet_router.get("/search/by_building/{building_number}", response_model=ShowCabinetListWithHATEOAS,
#                     responses={404: {"description": "Кабинеты не найдены"}})
# async def get_cabinets_by_building(building_number: int,
#                                    query_param: Annotated[QueryParams, Depends()],
#                                    request: Request,
#                                    db: AsyncSession = Depends(get_db)):
#     return await _get_cabinets_by_building(building_number, query_param.page, query_param.limit, request, db)


# @cabinet_router.get("/search/by_building_and_number", response_model=ShowCabinetWithHATEOAS,
#                     responses={404: {"description": "Кабинет не найден"}})
# async def get_cabinet_by_building_and_number(building_number: int,
#                                              cabinet_number: int,
#                                              request: Request,
#                                              db: AsyncSession = Depends(get_db)):
#     return await _get_cabinet_by_building_and_number(building_number, cabinet_number, request, db)


# @cabinet_router.delete("/delete/{building_number}/{cabinet_number}", response_model=ShowCabinetWithHATEOAS,
#                     responses={404: {"description": "Не удаётся удалить кабинет"}})
# async def delete_cabinet(building_number: int, cabinet_number: int, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _delete_cabinet(building_number, cabinet_number, request, db)


# @cabinet_router.put("/update", response_model=ShowCabinetWithHATEOAS,
#                     responses={404: {"description": "Кабинет не найден или нет возможности изменить его параметры"}})
# async def update_cabinet(body: UpdateCabinet, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _update_cabinet(body, request, db)


# '''
# ==============================
# CRUD operations for Speciality
# ==============================
# '''


# async def _create_speciality(body: CreateSpeciality, request: Request, db) -> ShowSpecialityWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             speciality_dal = SpecialityDAL(session)

#             try:
#                 speciality = await speciality_dal.create_speciality(speciality_code=body.speciality_code)

#                 speciality_code = speciality.speciality_code
#                 speciality_pydantic = ShowSpeciality.model_validate(speciality)

#                 # Add HATEOAS
#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 hateoas_links = {
#                     "self": f'{api_base_url}/specialities/search/by_speciality_code/{speciality_code}',
#                     "update": f'{api_base_url}/specialities/update/{speciality_code}',
#                     "delete": f'{api_base_url}/specialities/delete/{speciality_code}',
#                     "specialities": f'{api_base_url}/specialities',
#                     "groups": f'{api_base_url}/groups/search/by_speciality/{speciality_code}'
#                 }

#                 return ShowSpecialityWithHATEOAS(speciality=speciality_pydantic, links=hateoas_links)

#             except IntegrityError as e:
#                 await session.rollback()
#                 logger.error(f"Ошибка целостности БД при создании специальности: {e}")
#                 raise HTTPException(status_code=400, detail="Невозможно создать специальность из-за конфликта данных.")

#             except HTTPException:
#                 await session.rollback()
#                 raise

#             except Exception as e:
#                 await session.rollback()
#                 logger.error(f"Неожиданная ошибка при создании специальности: {e}", exc_info=True)
#                 raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")



# async def _get_all_specialties(page: int, limit: int, request: Request, db) -> ShowSpecialityListWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             speciality_dal = SpecialityDAL(session)

#             try:
#                 specialities = await speciality_dal.get_all_specialties(page, limit)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 specialities_with_hateoas = []
#                 for speciality in specialities:
#                     speciality_pydantic = ShowSpeciality.model_validate(speciality)

#                     # add HATEOAS
#                     speciality_code = speciality.speciality_code
#                     speciality_links = {
#                         "self": f'{api_base_url}/specialities/search/by_speciality_code/{speciality_code}',
#                         "update": f'{api_base_url}/specialities/update/{speciality_code}',
#                         "delete": f'{api_base_url}/specialities/delete/{speciality_code}',
#                         "groups": f'{api_base_url}/groups/search/by_speciality/{speciality_code}'
#                 }

#                     speciality_with_links = ShowSpecialityWithHATEOAS(
#                         speciality=speciality_pydantic,
#                         links=speciality_links
#                     )
#                     specialities_with_hateoas.append(speciality_with_links)

#                 collection_links = {
#                     "self": f'{api_base_url}/specialities?page={page}&limit={limit}',
#                     "create": f'{api_base_url}/specialities/create'
#                 }
#                 collection_links = {k: v for k, v in collection_links.items() if v is not None}

#                 return ShowSpecialityListWithHATEOAS(
#                     specialities=specialities_with_hateoas,
#                     links=collection_links
#                 )

#             except HTTPException:
#                 raise

#             except Exception as e:
#                 logger.warning(f"Получение специальностей отменено (Ошибка: {e})")
#                 raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


# async def _get_speciality(speciality_code: str, request: Request, db) -> ShowSpecialityWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             speciality_dal = SpecialityDAL(session)

#             try:
#                 speciality = await speciality_dal.get_speciality(speciality_code)

#                 # if speciality doesn't exist
#                 if not speciality:
#                     raise HTTPException(status_code=404, detail=f"Специальность с кодом: {speciality_code} не найдена")

#                 speciality_pydantic = ShowSpeciality.model_validate(speciality)

#                 # Add HATEOAS
#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 hateoas_links = {
#                     "self": f'{api_base_url}/specialities/search/by_speciality_code/{speciality_code}',
#                     "update": f'{api_base_url}/specialities/update/{speciality_code}',
#                     "delete": f'{api_base_url}/specialities/delete/{speciality_code}',
#                     "specialities": f'{api_base_url}/specialities',
#                     "groups": f'{api_base_url}/groups/search/by_speciality/{speciality_code}'
#                 }

#                 return ShowSpecialityWithHATEOAS(speciality=speciality_pydantic, links=hateoas_links)

#             except HTTPException:
#                 raise

#             except Exception as e:
#                 logger.warning(f"Получение специальности отменено (Ошибка: {e})")
#                 raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


# async def _delete_speciality(speciality_code: str, request: Request, db) -> ShowSpecialityWithHATEOAS:
#     async with db as session:
#         try:
#             async with session.begin():
#                 speciality_dal = SpecialityDAL(session)
#                 speciality = await speciality_dal.delete_speciality(speciality_code)

#                 if not speciality:
#                     raise HTTPException(status_code=404,
#                                         detail=f"Специальность с кодом: {speciality_code} не может быть удалена, т.к. не найдена")

#                 speciality_pydantic = ShowSpeciality.model_validate(speciality)

#                 # Add HATEOAS
#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 hateoas_links = {
#                     "self": f'{api_base_url}/specialities/search/by_speciality_code/{speciality_code}',
#                     "specialities": f'{api_base_url}/specialities',
#                     "create": f'{api_base_url}/specialities/create',
#                     "groups": f'{api_base_url}/groups/search/by_speciality/{speciality_code}'
#                 }

#                 return ShowSpecialityWithHATEOAS(speciality=speciality_pydantic, links=hateoas_links)

#         except HTTPException:
#             await session.rollback()
#             raise

#         except Exception as e:
#             await session.rollback()
#             logger.warning(f"Неожиданная ошибка при удалении специальности {speciality_code}: {e}", exc_info=True)
#             raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении специальности.")


# async def _update_speciality(body: UpdateSpeciality, request: Request, db) -> ShowSpecialityWithHATEOAS:
#     async with db as session:
#         try:
#             async with session.begin():
#                 # exclusion of None-fields from the transmitted data
#                 update_data = {
#                     key: value for key, value in body.dict().items() if
#                     value is not None and key != "speciality_code"
#                 }

#                 speciality_dal = SpecialityDAL(session)

#                 # Rename field new_speciality_code to speciality_code
#                 if "new_speciality_code" in update_data:
#                     update_data["speciality_code"] = update_data.pop("new_speciality_code")

#                 # Change data
#                 speciality = await speciality_dal.update_speciality(
#                     target_code=body.speciality_code,
#                     **update_data
#                     )

#                 if not speciality:
#                     raise HTTPException(status_code=404, detail="Специальность не была обновлена")

#                 speciality_code = body.speciality_code
#                 speciality_pydantic = ShowSpeciality.model_validate(speciality)

#                 # Add HATEOAS
#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 hateoas_links = {
#                     "self": f'{api_base_url}/specialities/search/by_speciality_code/{speciality_code}',
#                     "update": f'{api_base_url}/specialities/update/{speciality_code}',
#                     "delete": f'{api_base_url}/specialities/delete/{speciality_code}',
#                     "specialities": f'{api_base_url}/specialities',
#                     "groups": f'{api_base_url}/groups/search/by_speciality/{speciality_code}'
#                 }

#                 return ShowSpecialityWithHATEOAS(speciality=speciality_pydantic, links=hateoas_links)

#         except HTTPException:
#             await session.rollback()
#             raise

#         except Exception as e:
#             await session.rollback()
#             logger.error(f"Неожиданная ошибка при обновлении специальности {body.speciality_code}: {e}", exc_info=True)
#             raise HTTPException(
#                 status_code=500,
#                 detail="Внутренняя ошибка сервера при обновлении специальности."
#             )


# @speciality_router.post("/create", response_model=ShowSpecialityWithHATEOAS, status_code=201)
# async def create_speciality(body: CreateSpeciality, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _create_speciality(body, request, db)


# @speciality_router.get("/search", response_model=ShowSpecialityListWithHATEOAS, responses={404: {"description": "Специальность не найдена"}})
# async def get_all_specialities(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
#     return await _get_all_specialties(query_param.page, query_param.limit, request, db)


# @speciality_router.get("/search/by_code/{speciality_code}", response_model=ShowSpecialityWithHATEOAS,
#                     responses={404: {"description": "Специальность не найдена"}})
# async def get_speciality_by_code(speciality_code: str, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _get_speciality(speciality_code, request, db)


# @speciality_router.delete("/delete/{speciality_code}", response_model=ShowSpecialityWithHATEOAS,
#                     responses={404: {"description": "Не удаётся удалить специальность"}})
# async def delete_speciality(speciality_code: str, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _delete_speciality(speciality_code, request, db)


# @speciality_router.put("/update", response_model=ShowSpecialityWithHATEOAS,
#                     responses={404: {"description": "Специальность не найдена или нет возможности изменить её параметры"}})
# async def update_speciality(body: UpdateSpeciality, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _update_speciality(body, request, db)


# '''
# =========================
# CRUD operations for Group
# =========================
# '''


# async def _create_new_group(body: CreateGroup, request: Request, db) -> ShowGroupWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             group_dal = GroupDAL(session)
#             teacher_dal = TeacherDAL(session)
#             speciality_dal = SpecialityDAL(session)

#             try:
#                 # Check that the teacher and speciality exists
#                 # Check that the group is unique
#                 # By using helpers
#                 if body.speciality_code != None and not await ensure_speciality_exists(speciality_dal, body.speciality_code):
#                     raise HTTPException(
#                         status_code=404,
#                         detail=f"Специальность с кодом {body.speciality_code} не найдена"
#                     )

#                 if body.group_advisor_id != None and not await ensure_teacher_exists(teacher_dal, body.group_advisor_id):
#                     raise HTTPException(
#                         status_code=404,
#                         detail=f"Учитель с id {body.group_advisor_id} не найден"
#                     )

#                 if not await ensure_group_unique(group_dal, body.group_name):
#                     raise HTTPException(
#                         status_code=400,
#                         detail=f"Группа {body.group_name} уже существует"
#                     )

#                 group = await group_dal.create_group(
#                     group_name=body.group_name,
#                     speciality_code=body.speciality_code,
#                     quantity_students=body.quantity_students,
#                     group_advisor_id=body.group_advisor_id
#                 )

#                 group_name = group.group_name
#                 group_pydantic = ShowGroup.model_validate(group)

#                 # Add HATEOAS
#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 hateoas_links = {
#                     "self": f'{api_base_url}/groups/search/by_group-name/{group_name}',
#                     "update": f'{api_base_url}/groups/update/{group_name}',
#                     "delete": f'{api_base_url}/groups/delete/{group_name}',
#                     "groups": f'{api_base_url}/groups',
#                     "advisor": f'{api_base_url}/teachers/search/by_group/{group_name}' if group.group_advisor_id else None,
#                     "speciality": f'{api_base_url}/specialities/search/by_speciality_code/{group.speciality_code}' if group.speciality_code else None,
#                     "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}',
#                     "curriculums": f'{api_base_url}/curriculums/search/by_group/{group_name}',
#                     "requests": f'{api_base_url}/requests/search/by_group/{group_name}'
#                 }
#                 hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

#                 return ShowGroupWithHATEOAS(group=group_pydantic, links=hateoas_links)

#             except IntegrityError as e:
#                 await session.rollback()
#                 logger.error(f"Ошибка целостности БД при создании группы: {e}")
#                 raise HTTPException(status_code=400, detail="Невозможно создать группу из-за конфликта данных.")

#             except HTTPException:
#                 await session.rollback()
#                 raise

#             except Exception as e:
#                 await session.rollback()
#                 logger.error(f"Неожиданная ошибка при создании группы: {e}", exc_info=True)
#                 raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")



# async def _get_group_by_name(group_name: str, request: Request, db) -> ShowGroupWithHATEOAS:
#     async with db as session:
#         async with db as session:
#             group_dal = GroupDAL(session)
#             try:
#                 group = await group_dal.get_group(group_name)

#                 # if group doesn't exist
#                 if not group:
#                     raise HTTPException(
#                         status_code=404,
#                         detail=f"Группа с названием: {group_name} не найдена"
#                     )

#                 group_pydantic = ShowGroup.model_validate(group)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 hateoas_links = {
#                     "self": f'{api_base_url}/groups/search/by_group-name/{group_name}',
#                     "update": f'{api_base_url}/groups/update/{group_name}',
#                     "delete": f'{api_base_url}/groups/delete/{group_name}',
#                     "groups": f'{api_base_url}/groups',
#                     "advisor": f'{api_base_url}/teachers/search/{group.group_advisor_id}' if group.group_advisor_id else None,
#                     "speciality": f'{api_base_url}/specialities/search/{group.speciality_code}' if group.speciality_code else None,
#                     "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}',
#                     "curriculums": f'{api_base_url}/curriculums/search/by_group/{group_name}',
#                     "requests": f'{api_base_url}/requests/search/by_group/{group_name}'
#                 }
#                 hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

#                 return ShowGroupWithHATEOAS(group=group_pydantic, links=hateoas_links)

#             except HTTPException:
#                 raise

#             except Exception as e:
#                 logger.error(f"Неожиданная ошибка при получении группы {group_name}: {e}", exc_info=True)
#                 raise HTTPException(
#                     status_code=500,
#                     detail="Внутренняя ошибка сервера при получении группы."
#                 )


# async def _get_group_by_advisor(advisor_id: int, request: Request, db) -> ShowGroupWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             group_dal = GroupDAL(session)

#             try:
#                 group = await group_dal.get_group_by_advisor_id(advisor_id)

#                 # if group doesn't exist
#                 if not group:
#                     raise HTTPException(status_code=404, detail=f"Группа с преподавателем: {advisor_id} не найдена")

#                 group_pydantic = ShowGroup.model_validate(group)
#                 group_name = group.group_name

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 hateoas_links = {
#                     "self": f'{api_base_url}/groups/search/by_group-name/{group_name}',
#                     "update": f'{api_base_url}/groups/update/{group_name}',
#                     "delete": f'{api_base_url}/groups/delete/{group_name}',
#                     "groups": f'{api_base_url}/groups',
#                     "advisor": f'{api_base_url}/teachers/search/{group.group_advisor_id}' if group.group_advisor_id else None,
#                     "speciality": f'{api_base_url}/specialities/search/{group.speciality_code}' if group.speciality_code else None,
#                     "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}',
#                     "curriculums": f'{api_base_url}/curriculums/search/by_group/{group_name}',
#                     "requests": f'{api_base_url}/requests/search/by_group/{group_name}'
#                 }
#                 hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

#                 return ShowGroupWithHATEOAS(group=group_pydantic, links=hateoas_links)

#             except HTTPException:
#                 raise
#             except Exception as e:
#                 logger.error(f"Неожиданная ошибка при получении группы {group_name}: {e}", exc_info=True)
#                 raise HTTPException(
#                     status_code=500,
#                     detail="Внутренняя ошибка сервера при получении группы."
#                 )


# async def _get_all_groups(page: int, limit: int, request: Request, db) -> ShowGroupListWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             group_dal = GroupDAL(session)

#             try:
#                 groups = await group_dal.get_all_groups(page, limit)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 groups_with_hateoas = []
#                 for group in groups:
#                     group_pydantic = ShowGroup.model_validate(group)

#                     # add HATEOAS
#                     group_name = group.group_name
#                     group_links = {
#                         "self": f'{api_base_url}/groups/search/by_group-name/{group_name}',
#                         "update": f'{api_base_url}/groups/update/{group_name}',
#                         "delete": f'{api_base_url}/groups/delete/{group_name}',
#                         "advisor": f'{api_base_url}/teachers/search/{group.group_advisor_id}' if group.group_advisor_id else None,
#                         "speciality": f'{api_base_url}/specialities/search/{group.speciality_code}' if group.speciality_code else None,
#                         "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}',
#                         "curriculums": f'{api_base_url}/curriculums/search/by_group/{group_name}',
#                         "requests": f'{api_base_url}/requests/search/by_group/{group_name}'
#                     }
#                     group_links = {k: v for k, v in group_links.items() if v is not None}

#                     group_with_links = ShowGroupWithHATEOAS(
#                         group=group_pydantic,
#                         links=group_links
#                     )
#                     groups_with_hateoas.append(group_with_links)

#                 collection_links = {
#                     "self": f'{api_base_url}/groups?page={page}&limit={limit}',
#                     "create": f'{api_base_url}/groups/create'
#                 }
#                 collection_links = {k: v for k, v in collection_links.items() if v is not None}

#                 return ShowGroupListWithHATEOAS(
#                     groups=groups_with_hateoas,
#                     links=collection_links
#                 )

#             except HTTPException:
#                 raise

#             except Exception as e:
#                 logger.warning(f"Получение групп отменено (Ошибка: {e})")
#                 raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


# async def _get_all_groups_by_speciality(speciality_code: str, page: int, limit: int, request: Request, db) -> ShowGroupListWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             group_dal = GroupDAL(session)
#             speciality_dal = SpecialityDAL(session)

#             if not await ensure_speciality_exists(speciality_dal, speciality_code):
#                 raise HTTPException(
#                     status_code=404,
#                     detail=f"Специальность с кодом {speciality_code} не найдена"
#                 )

#             try:
#                 groups = await group_dal.get_all_groups_by_speciality(speciality_code, page, limit)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 groups_with_hateoas = []
#                 for group in groups:
#                     group_pydantic = ShowGroup.model_validate(group)

#                     # add HATEOAS
#                     group_name = group.group_name
#                     group_links = {
#                         "self": f'{api_base_url}/groups/search/by_group-name/{group_name}',
#                         "update": f'{api_base_url}/groups/update/{group_name}',
#                         "delete": f'{api_base_url}/groups/delete/{group_name}',
#                         "advisor": f'{api_base_url}/teachers/search/{group.group_advisor_id}' if group.group_advisor_id else None,
#                         "speciality": f'{api_base_url}/specialities/search/{group.speciality_code}' if group.speciality_code else None,
#                         "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}',
#                         "curriculums": f'{api_base_url}/curriculums/search/by_group/{group_name}',
#                         "requests": f'{api_base_url}/requests/search/by_group/{group_name}'
#                     }
#                     group_links = {k: v for k, v in group_links.items() if v is not None}

#                     group_with_links = ShowGroupWithHATEOAS(
#                         group=group_pydantic,
#                         links=group_links
#                     )
#                     groups_with_hateoas.append(group_with_links)

#                 collection_links = {
#                     "self": f'{api_base_url}/groups?page={page}&limit={limit}',
#                     "create": f'{api_base_url}/groups/create'
#                 }
#                 collection_links = {k: v for k, v in collection_links.items() if v is not None}

#                 return ShowGroupListWithHATEOAS(
#                     groups=groups_with_hateoas,
#                     links=collection_links
#                 )

#             except HTTPException:
#                 raise

#             except Exception as e:
#                 logger.warning(f"Получение групп отменено (Ошибка: {e})")
#                 raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


# async def _delete_group(group_name: str, request: Request, db) -> ShowGroupWithHATEOAS:
#     async with db as session:
#         try:
#             async with session.begin():
#                 group_dal = GroupDAL(session)
#                 group = await group_dal.delete_group(group_name)

#                 if not group:
#                     raise HTTPException(status_code=404, detail=f"Группа с названием: {group_name} не найдена")

#                 group_pydantic = ShowGroup.model_validate(group)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 hateoas_links = {
#                     "self": f'{api_base_url}/groups/search/by_group-name/{group_name}',
#                     "update": f'{api_base_url}/groups/update/{group_name}',
#                     "delete": f'{api_base_url}/groups/delete/{group_name}',
#                     "groups": f'{api_base_url}/groups',
#                     "advisor": f'{api_base_url}/teachers/search/{group.group_advisor_id}' if group.group_advisor_id else None,
#                     "speciality": f'{api_base_url}/specialities/search/{group.speciality_code}' if group.speciality_code else None,
#                     "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}',
#                     "curriculums": f'{api_base_url}/curriculums/search/by_group/{group_name}',
#                     "requests": f'{api_base_url}/requests/search/by_group/{group_name}'
#                 }
#                 hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

#                 return ShowGroupWithHATEOAS(group=group_pydantic, links=hateoas_links)

#         except HTTPException:
#             await session.rollback()
#             raise

#         except Exception as e:
#             await session.rollback()
#             logger.error(f"Неожиданная ошибка при удалении группы {group_name}: {e}", exc_info=True)
#             raise HTTPException(
#                 status_code=500,
#                 detail="Внутренняя ошибка сервера при удалении группы."
#             )


# async def _update_group(body: UpdateGroup, request: Request, db) -> ShowGroupWithHATEOAS:
#     async with db as session:
#         try:
#             async with session.begin():
#                 # exclusion of None-fields from the transmitted data
#                 update_data = {
#                     key: value for key, value in body.dict().items()
#                     if value is not None and key != "group_name"
#                 }

#                 group_dal = GroupDAL(session)
#                 teacher_dal = TeacherDAL(session)
#                 speciality_dal = SpecialityDAL(session)

#                 # Rename field new_speciality_code to speciality_code
#                 if "new_group_name" in update_data:
#                     update_data["group_name"] = update_data.pop("new_group_name")

#                 if body.speciality_code != None and not await ensure_speciality_exists(speciality_dal, body.speciality_code):
#                     raise HTTPException(
#                         status_code=404,
#                         detail=f"Специальность с кодом {body.speciality_code} не найдена"
#                     )

#                 if body.group_advisor_id != None and not await ensure_teacher_exists(teacher_dal, body.group_advisor_id):
#                     raise HTTPException(
#                         status_code=404,
#                         detail=f"Учитель с id {body.group_advisor_id} не найден"
#                     )

#                 if not await ensure_group_unique(group_dal, body.new_group_name):
#                     raise HTTPException(
#                         status_code=400,
#                         detail=f"Группа {body.new_group_name} уже существует"
#                     )

#                 group = await group_dal.update_group(
#                     target_group=body.group_name,
#                     **update_data
#                 )

#                 group_pydantic = ShowGroup.model_validate(group)
#                 group_name = group.group_name

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 hateoas_links = {
#                     "self": f'{api_base_url}/groups/search/by_group-name/{group_name}',
#                     "delete": f'{api_base_url}/groups/delete/{group_name}',
#                     "groups": f'{api_base_url}/groups',
#                     "advisor": f'{api_base_url}/teachers/search/{group.group_advisor_id}' if group.group_advisor_id else None,
#                     "speciality": f'{api_base_url}/specialities/search/{group.speciality_code}' if group.speciality_code else None,
#                     "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}',
#                     "curriculums": f'{api_base_url}/curriculums/search/by_group/{group_name}',
#                     "requests": f'{api_base_url}/requests/search/by_group/{group_name}'
#                 }
#                 hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

#                 return ShowGroupWithHATEOAS(group=group_pydantic, links=hateoas_links)

#         except HTTPException:
#             await session.rollback()
#             raise

#         except Exception as e:
#             await session.rollback()
#             logger.error(f"Неожиданная ошибка при обновлении группы {body.group_name}: {e}", exc_info=True)
#             raise HTTPException(
#                 status_code=500,
#                 detail="Внутренняя ошибка сервера при обновлении группы."
#             )


# @group_router.post("/create", response_model=ShowGroupWithHATEOAS, status_code=201)
# async def create_group(body: CreateGroup, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _create_new_group(body, request, db)


# @group_router.get("/search/by_group_name/{group_name}", response_model=ShowGroupWithHATEOAS,
#                     responses={404: {"description": "Группа не найдена"}})
# async def get_group_by_name(group_name: str, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _get_group_by_name(group_name, request, db)


# @group_router.get("/search/by_advisor/{advisor_id}", response_model=ShowGroupWithHATEOAS,
#                     responses={404: {"description": "Группа не найдена"}})
# async def get_group_by_advisor(advisor_id: int, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _get_group_by_advisor(advisor_id, request, db)


# @group_router.get("/search", response_model=ShowGroupListWithHATEOAS,
#                   responses={404: {"description": "Группы не найдены"}})
# async def get_all_groups(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
#     return await _get_all_groups(query_param.page, query_param.limit, request, db)


# @group_router.get("/search/by_speciality/{speciality_code}", response_model=ShowGroupListWithHATEOAS,
#                   responses={404: {"description": "Группы не найдены"}})
# async def get_all_groups_by_speciality(speciality_code: str, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
#     return await _get_all_groups_by_speciality(speciality_code, query_param.page, query_param.limit, request, db)


# @group_router.delete("/delete/{group_name}", response_model=ShowGroupWithHATEOAS,
#                     responses={404: {"description": "Группа не найдена"}})
# async def delete_group(group_name: str, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _delete_group(group_name, request, db)


# @group_router.put("/update", response_model=ShowGroupWithHATEOAS,
#                   responses={404: {"description": "Группа не найдена"}})
# async def update_group(body: UpdateGroup, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _update_group(body, request, db)


# '''
# ===========================
# CRUD operations for Subject
# ===========================
# '''


# async def _create_new_subject(body: CreateSubject, request: Request, db) -> ShowSubjectWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             subject_dal = SubjectDAL(session)

#             try:
#                 if not await ensure_subject_unique(subject_dal, body.subject_code):
#                     raise HTTPException(
#                         status_code=status.HTTP_400_BAD_REQUEST,
#                         detail=f"Предмет {body.subject_code} уже существует"
#                     )

#                 subject = await subject_dal.create_subject(
#                     subject_code=body.subject_code,
#                     name=body.name
#                 )

#                 subject_pydantic = ShowSubject.model_validate(subject)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 subject_code = subject.subject_code

#                 hateoas_links = {
#                     "self": f'{api_base_url}/subjects/search/{subject_code}',
#                     "update": f'{api_base_url}/subjects/update/{subject_code}',
#                     "delete": f'{api_base_url}/subjects/delete/{subject_code}',
#                     "subjects": f'{api_base_url}/subjects',
#                     "curriculums": f'{api_base_url}/curriculums/search/by_subject/{subject_code}',
#                     "requests": f'{api_base_url}/requests/search/by_subject/{subject_code}',
#                     "sessions": f'{api_base_url}/sessions/search/by_subject/{subject_code}',
#                 }

#                 return ShowSubjectWithHATEOAS(subject=subject_pydantic, links=hateoas_links)

#             except IntegrityError as e:
#                 await session.rollback()
#                 logger.error(f"Ошибка целостности БД при создании предмета '{body.subject_code}': {e}", exc_info=True)
#                 raise HTTPException(
#                     status_code=status.HTTP_400_BAD_REQUEST,
#                     detail="Невозможно создать предмет из-за конфликта данных (возможно, он уже существует)."
#                 )

#             except HTTPException:
#                 await session.rollback()
#                 raise

#             except Exception as e:
#                 await session.rollback()
#                 logger.error(f"Неожиданная ошибка при создании предмета '{body.subject_code}': {e}", exc_info=True)
#                 raise HTTPException(
#                     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                     detail="Внутренняя ошибка сервера при создании предмета."
#                 )


# async def _get_subject(subject_code: str, request: Request, db) -> ShowSubjectWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             subject_dal = SubjectDAL(session)
#             try:
#                 subject = await subject_dal.get_subject(subject_code)

#                 # if subject doesn't exist
#                 if not subject:
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail=f"Предмет {subject_code} не найден"
#                     )

#                 subject_pydantic = ShowSubject.model_validate(subject)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 hateoas_links = {
#                     "self": f'{api_base_url}/subjects/search/{subject_code}',
#                     "update": f'{api_base_url}/subjects/update/{subject_code}',
#                     "delete": f'{api_base_url}/subjects/delete/{subject_code}',
#                     "subjects": f'{api_base_url}/subjects',
#                     "curriculums": f'{api_base_url}/curriculums/search/by_subject/{subject_code}',
#                     "requests": f'{api_base_url}/requests/search/by_subject/{subject_code}',
#                     "sessions": f'{api_base_url}/sessions/search/by_subject/{subject_code}',
#                 }

#                 return ShowSubjectWithHATEOAS(subject=subject_pydantic, links=hateoas_links)

#             except HTTPException:
#                 raise
#             except Exception as e:
#                 logger.error(f"Неожиданная ошибка при получении предмета {subject_code}: {e}", exc_info=True)
#                 raise HTTPException(
#                     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                     detail="Внутренняя ошибка сервера при получении предмета."
#                 )


# async def _get_all_subjects(page: int, limit: int, request: Request, db) -> ShowSubjectListWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             subject_dal = SubjectDAL(session)
#             try:
#                 subjects_orm_list = await subject_dal.get_all_subjects(page, limit)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 subjects_with_hateoas = []
#                 for subject_orm in subjects_orm_list:
#                     subject_pydantic = ShowSubject.model_validate(subject_orm)

#                     subject_code = subject_orm.subject_code
#                     subject_links = {
#                         "self": f'{api_base_url}/subjects/search/{subject_code}',
#                         "update": f'{api_base_url}/subjects/update/{subject_code}',
#                         "delete": f'{api_base_url}/subjects/delete/{subject_code}',
#                         "curriculums": f'{api_base_url}/curriculums/search/by_subject/{subject_code}',
#                         "requests": f'{api_base_url}/requests/search/by_subject/{subject_code}',
#                         "sessions": f'{api_base_url}/sessions/search/by_subject/{subject_code}',
#                     }

#                     subject_with_links = ShowSubjectWithHATEOAS(
#                         subject=subject_pydantic,
#                         links=subject_links
#                     )
#                     subjects_with_hateoas.append(subject_with_links)

#                 collection_links = {
#                     "self": f'{api_base_url}/subjects?page={page}&limit={limit}',
#                     "create": f'{api_base_url}/subjects',
#                 }

#                 return ShowSubjectListWithHATEOAS(
#                     subjects=subjects_with_hateoas,
#                     links=collection_links
#                 )

#             except Exception as e:
#                 logger.error(f"Неожиданная ошибка при получении списка предметов (page={page}, limit={limit}): {e}", exc_info=True)
#                 raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при получении списка предметов.")


# async def _get_all_subjects_by_name(
#     name: str, page: int, limit: int, request: Request, db) -> ShowSubjectListWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             subject_dal = SubjectDAL(session)
#             try:
#                 subjects_orm_list = await subject_dal.get_subjects_by_name(name, page, limit)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 subjects_with_hateoas = []
#                 for subject_orm in subjects_orm_list:
#                     subject_pydantic = ShowSubject.model_validate(subject_orm)

#                     subject_code = subject_orm.subject_code
#                     subject_links = {
#                         "self": f'{api_base_url}/subjects/search/{subject_code}',
#                         "update": f'{api_base_url}/subjects/update/{subject_code}',
#                         "delete": f'{api_base_url}/subjects/delete/{subject_code}',
#                         "curriculums": f'{api_base_url}/curriculums/search/by_subject/{subject_code}',
#                         "requests": f'{api_base_url}/requests/search/by_subject/{subject_code}',
#                         "sessions": f'{api_base_url}/sessions/search/by_subject/{subject_code}',
#                     }

#                     subject_with_links = ShowSubjectWithHATEOAS(
#                         subject=subject_pydantic,
#                         links=subject_links
#                     )
#                     subjects_with_hateoas.append(subject_with_links)

#                 collection_links = {
#                     "self": f'{api_base_url}/subjects/search/by_name/{name}?page={page}&limit={limit}',
#                     "create": f'{api_base_url}/subjects',
#                     "subjects": f'{api_base_url}/subjects',
#                 }

#                 return ShowSubjectListWithHATEOAS(
#                     subjects=subjects_with_hateoas,
#                     links=collection_links
#                 )

#             except Exception as e:
#                 logger.error(f"Неожиданная ошибка при получении списка предметов по имени '{name}' (page={page}, limit={limit}): {e}", exc_info=True)
#                 raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при получении списка предметов.")


# async def _delete_subject(subject_code: str, request: Request, db) -> ShowSubjectWithHATEOAS:
#     async with db as session:
#         try:
#             async with session.begin():
#                 subject_dal = SubjectDAL(session)
#                 subject = await subject_dal.delete_subject(subject_code)

#                 if not subject:
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail=f"Предмет: {subject_code} не найден"
#                     )

#                 subject_pydantic = ShowSubject.model_validate(subject)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 hateoas_links = {
#                     "self": f'{api_base_url}/subjects/search/{subject_code}',
#                     "subjects": f'{api_base_url}/subjects',
#                     "create": f'{api_base_url}/subjects',
#                     "curriculums": f'{api_base_url}/curriculums/search/by_subject/{subject_code}',
#                     "requests": f'{api_base_url}/requests/search/by_subject/{subject_code}',
#                     "sessions": f'{api_base_url}/sessions/search/by_subject/{subject_code}'
#                 }

#                 return ShowSubjectWithHATEOAS(subject=subject_pydantic, links=hateoas_links)

#         except HTTPException:
#             await session.rollback()
#             raise

#         except Exception as e:
#             await session.rollback()
#             logger.error(f"Неожиданная ошибка при удалении предмета {subject_code}: {e}", exc_info=True)
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="Внутренняя ошибка сервера при удалении предмета."
#             )


# async def _update_subject(body: UpdateSubject, request: Request, db) -> ShowSubjectWithHATEOAS:
#     async with db as session:
#         try:
#             async with session.begin():
#                 update_data = {
#                     key: value for key, value in body.dict().items()
#                     if value is not None and key not in ["subject_code", "new_subject_code"]
#                 }

#                 subject_dal = SubjectDAL(session)

#                 if body.new_subject_code is not None and body.new_subject_code != body.subject_code:
#                     if not await ensure_subject_unique(subject_dal, body.new_subject_code):
#                         raise HTTPException(
#                             status_code=status.HTTP_400_BAD_REQUEST,
#                             detail=f"Предмет: {body.new_subject_code} уже существует"
#                         )

#                 if body.new_subject_code is not None and body.new_subject_code != body.subject_code:
#                      update_data["subject_code"] = body.new_subject_code

#                 subject = await subject_dal.update_subject(
#                     tg_subject_code=body.subject_code,
#                     **update_data
#                 )

#                 if not subject:
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail=f"Предмет: {body.subject_code} не найден"
#                     )

#                 subject_pydantic = ShowSubject.model_validate(subject)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 final_subject_code = subject.subject_code

#                 hateoas_links = {
#                     "self": f'{api_base_url}/subjects/search/{final_subject_code}',
#                     "update": f'{api_base_url}/subjects/update/{final_subject_code}',
#                     "delete": f'{api_base_url}/subjects/delete/{final_subject_code}',
#                     "subjects": f'{api_base_url}/subjects',
#                     "curriculums": f'{api_base_url}/curriculums/search/by_subject/{final_subject_code}',
#                     "requests": f'{api_base_url}/requests/search/by_subject/{final_subject_code}',
#                     "sessions": f'{api_base_url}/sessions/search/by_subject/{final_subject_code}'
#                 }

#                 return ShowSubjectWithHATEOAS(subject=subject_pydantic, links=hateoas_links)

#         except HTTPException:
#             await session.rollback()
#             raise
#         except Exception as e:
#             await session.rollback()
#             logger.error(f"Неожиданная ошибка при обновлении предмета {body.subject_code}: {e}", exc_info=True)
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="Внутренняя ошибка сервера при обновлении предмета."
#             )


# @subject_router.post("/create", response_model=ShowSubjectWithHATEOAS, status_code=status.HTTP_201_CREATED)
# async def create_subject(body: CreateSubject, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _create_new_subject(body, request, db)


# @subject_router.get("/search/by_code/{subject_code}", response_model=ShowSubjectWithHATEOAS,
#                     responses={404: {"description": "Предмет не найден"}})
# async def get_subject(subject_code: str, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _get_subject(subject_code, request, db)


# @subject_router.get("/search", response_model=ShowSubjectListWithHATEOAS,
#                     responses={404: {"description": "Предметы не найдены"}})
# async def get_all_subjects(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
#     return await _get_all_subjects(query_param.page, query_param.limit, request, db)


# @subject_router.get("/search/by_name/{name}", response_model=ShowSubjectListWithHATEOAS,
#                     responses={404: {"description": "Предметы не найдены"}})
# async def get_all_subjects_by_name(name: str, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
#     return await _get_all_subjects_by_name(name, query_param.page, query_param.limit, request, db)


# @subject_router.delete("/delete/{subject_code}", response_model=ShowSubjectWithHATEOAS,
#                     responses={404: {"description": "Предмет не найден"}})
# async def delete_subject(subject_code: str, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _delete_subject(subject_code, request, db)


# @subject_router.put("/update", response_model=ShowSubjectWithHATEOAS,
#                     responses={404: {"description": "Предмет не найден"}})
# async def update_subject(body: UpdateSubject, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _update_subject(body, request, db)


# '''
# =====================================
# CRUD operations for EmploymentTeacher
# =====================================
# '''


# async def _create_new_employment(body: CreateEmployment, request: Request, db) -> ShowEmploymentWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             employment_dal = EmployTeacherDAL(session)
#             teacher_dal = TeacherDAL(session)

#             try:
#                 if not await ensure_teacher_exists(teacher_dal, body.teacher_id):
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail=f"Учитель: {body.teacher_id} не существует"
#                     )

#                 if not await ensure_employment_unique(
#                     employment_dal,
#                     body.date_start_period,
#                     body.date_end_period,
#                     body.teacher_id
#                 ):
#                     raise HTTPException(
#                         status_code=status.HTTP_400_BAD_REQUEST,
#                         detail=f"График преподавателя {body.teacher_id} начиная с {body.date_start_period} и заканчивая {body.date_end_period} уже существует"
#                     )

#                 employment = await employment_dal.create_employTeacher(
#                     date_start_period=body.date_start_period,
#                     date_end_period=body.date_end_period,
#                     teacher_id=body.teacher_id,
#                     monday=body.monday,
#                     tuesday=body.tuesday,
#                     wednesday=body.wednesday,
#                     thursday=body.thursday,
#                     friday=body.friday,
#                     saturday=body.saturday
#                 )

#                 employment_pydantic = ShowEmployment.model_validate(employment)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 date_start = employment.date_start_period.isoformat()
#                 date_end = employment.date_end_period.isoformat()
#                 teacher_id = employment.teacher_id

#                 hateoas_links = {
#                     "self": f'{api_base_url}/employments/search/{teacher_id}/{date_start}/{date_end}',
#                     "update": f'{api_base_url}/employments/update/{teacher_id}/{date_start}/{date_end}',
#                     "delete": f'{api_base_url}/employments/delete/{teacher_id}/{date_start}/{date_end}',
#                     "employments": f'{api_base_url}/employments',
#                     "teacher": f'{api_base_url}/teachers/search/by_id/{teacher_id}'
#                 }

#                 return ShowEmploymentWithHATEOAS(employment=employment_pydantic, links=hateoas_links)

#             except HTTPException:
#                 await session.rollback()
#                 raise

#             except Exception as e:
#                 await session.rollback()
#                 logger.error(f"Неожиданная ошибка при создании графика занятости для учителя {body.teacher_id}: {e}", exc_info=True)
#                 raise HTTPException(
#                     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                     detail="Внутренняя ошибка сервера при создании графика занятости."
#                 )


# async def _get_employment(date_start_period: date, date_end_period: date, teacher_id: int, request: Request, db) -> ShowEmploymentWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             employment_dal = EmployTeacherDAL(session)
#             try:
#                 employment = await employment_dal.get_employTeacher(date_start_period, date_end_period, teacher_id)

#                 # if employment doesn't exist
#                 if not employment:
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail=f"График преподавателя {teacher_id} начиная с {date_start_period} и заканчивая {date_end_period} не найден"
#                     )

#                 employment_pydantic = ShowEmployment.model_validate(employment)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 start_date_str = date_start_period.isoformat()
#                 end_date_str = date_end_period.isoformat()

#                 hateoas_links = {
#                     "self": f'{api_base_url}/employments/search/{teacher_id}/{start_date_str}/{end_date_str}',
#                     "update": f'{api_base_url}/employments/update/{teacher_id}/{start_date_str}/{end_date_str}',
#                     "delete": f'{api_base_url}/employments/delete/{teacher_id}/{start_date_str}/{end_date_str}',
#                     "employments": f'{api_base_url}/employments',
#                     "teacher": f'{api_base_url}/teachers/search/{teacher_id}'
#                 }

#                 return ShowEmploymentWithHATEOAS(employment=employment_pydantic, links=hateoas_links)

#             except HTTPException:
#                 raise

#             except Exception as e:
#                 logger.error(
#                     f"Неожиданная ошибка при получении графика занятости преподавателя {teacher_id} с {date_start_period} по {date_end_period}: {e}",
#                     exc_info=True
#                 )
#                 raise HTTPException(
#                     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                     detail="Внутренняя ошибка сервера при получении графика занятости."
#                 )


# async def _get_all_employments(page: int, limit: int, request: Request, db) -> ShowEmploymentListWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             employment_dal = EmployTeacherDAL(session)
#             try:
#                 employments_orm_list = await employment_dal.get_all_employTeacher(page, limit)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 employments_with_hateoas = []
#                 for employment_orm in employments_orm_list:
#                     employment_pydantic = ShowEmployment.model_validate(employment_orm)

#                     emp_date_start = employment_orm.date_start_period.isoformat()
#                     emp_date_end = employment_orm.date_end_period.isoformat()
#                     emp_teacher_id = employment_orm.teacher_id

#                     employment_links = {
#                         "self": f'{api_base_url}/employments/search/{emp_teacher_id}/{emp_date_start}/{emp_date_end}',
#                         "update": f'{api_base_url}/employments/update/{emp_teacher_id}/{emp_date_start}/{emp_date_end}',
#                         "delete": f'{api_base_url}/employments/delete/{emp_teacher_id}/{emp_date_start}/{emp_date_end}',
#                         "teacher": f'{api_base_url}/teachers/search/{emp_teacher_id}'
#                     }

#                     employment_with_links = ShowEmploymentWithHATEOAS(
#                         employment=employment_pydantic,
#                         links=employment_links
#                     )
#                     employments_with_hateoas.append(employment_with_links)

#                 collection_links = {
#                     "self": f'{api_base_url}/employments/search?page={page}&limit={limit}',
#                     "create": f'{api_base_url}/employments/create',
#                     "employments": f'{api_base_url}/employments'
#                 }

#                 return ShowEmploymentListWithHATEOAS(
#                     employments=employments_with_hateoas,
#                     links=collection_links
#                 )

#             except Exception as e:
#                 logger.error(f"Неожиданная ошибка при получении списка графиков занятости (page={page}, limit={limit}): {e}", exc_info=True)
#                 raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при получении списка графиков занятости.")


# async def _get_all_employments_by_date(
#     date_start_period: date, date_end_period: date, page: int, limit: int, request: Request, db) -> ShowEmploymentListWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             employment_dal = EmployTeacherDAL(session)
#             try:
#                 employments_orm_list = await employment_dal.get_all_employTeacher_by_date(date_start_period, date_end_period, page, limit)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 employments_with_hateoas = []
#                 for employment_orm in employments_orm_list:
#                     employment_pydantic = ShowEmployment.model_validate(employment_orm)

#                     emp_date_start = employment_orm.date_start_period.isoformat()
#                     emp_date_end = employment_orm.date_end_period.isoformat()
#                     emp_teacher_id = employment_orm.teacher_id

#                     employment_links = {
#                         "self": f'{api_base_url}/employments/search/{emp_teacher_id}/{emp_date_start}/{emp_date_end}',
#                         "update": f'{api_base_url}/employments/update/{emp_teacher_id}/{emp_date_start}/{emp_date_end}',
#                         "delete": f'{api_base_url}/employments/delete/{emp_teacher_id}/{emp_date_start}/{emp_date_end}',
#                         "teacher": f'{api_base_url}/teachers/search/{emp_teacher_id}'
#                     }

#                     employment_with_links = ShowEmploymentWithHATEOAS(
#                         employment=employment_pydantic,
#                         links=employment_links
#                     )
#                     employments_with_hateoas.append(employment_with_links)

#                 # Форматируем даты для использования в URL
#                 start_date_str = date_start_period.isoformat()
#                 end_date_str = date_end_period.isoformat()

#                 collection_links = {
#                     "self": f'{api_base_url}/employments/search/by_date/{start_date_str}/{end_date_str}?page={page}&limit={limit}',
#                     "create": f'{api_base_url}/employments/create',
#                     "employments": f'{api_base_url}/employments'
#                 }

#                 return ShowEmploymentListWithHATEOAS(
#                     employments=employments_with_hateoas,
#                     links=collection_links
#                 )

#             except Exception as e:
#                 logger.error(
#                     f"Неожиданная ошибка при получении списка графиков занятости с {date_start_period} по {date_end_period} (page={page}, limit={limit}): {e}",
#                     exc_info=True
#                 )
#                 raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при получении списка графиков занятости.")



# async def _delete_employment(
#     date_start_period: date, date_end_period: date, teacher_id: int, request: Request, db) -> ShowEmploymentWithHATEOAS:
#     async with db as session:
#         try:
#             async with session.begin():
#                 employment_dal = EmployTeacherDAL(session)
#                 employment = await employment_dal.delete_employTeacher(date_start_period, date_end_period, teacher_id)

#                 if not employment:
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail=f"График преподавателя {teacher_id} начиная с {date_start_period} и заканчивая {date_end_period} не найден"
#                     )

#                 employment_pydantic = ShowEmployment.model_validate(employment)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 start_date_str = date_start_period.isoformat()
#                 end_date_str = date_end_period.isoformat()

#                 hateoas_links = {
#                     "self": f'{api_base_url}/employments/search/{teacher_id}/{start_date_str}/{end_date_str}',
#                     "employments": f'{api_base_url}/employments',
#                     "create": f'{api_base_url}/employments/create',
#                     "teacher": f'{api_base_url}/teachers/search/{teacher_id}'
#                 }

#                 return ShowEmploymentWithHATEOAS(employment=employment_pydantic, links=hateoas_links)

#         except HTTPException:
#             await session.rollback()
#             raise

#         except Exception as e:
#             await session.rollback()
#             logger.error(
#                 f"Неожиданная ошибка при удалении графика занятости преподавателя {teacher_id} с {date_start_period} по {date_end_period}: {e}",
#                 exc_info=True
#             )
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="Внутренняя ошибка сервера при удалении графика занятости."
#             )


# async def _update_employment(body: UpdateEmployment, request: Request, db) -> ShowEmploymentWithHATEOAS:
#     async with db as session:
#         try:
#             async with session.begin():
#                 update_data = {
#                     key: value for key, value in body.dict().items()
#                     if value is not None and key not in ["date_start_period", "date_end_period", "teacher_id", "new_date_start_period", "new_date_end_period", "new_teacher_id"]
#                 }

#                 employment_dal = EmployTeacherDAL(session)
#                 teacher_dal = TeacherDAL(session)

#                 new_date_start = body.new_date_start_period if body.new_date_start_period is not None else body.date_start_period
#                 new_date_end = body.new_date_end_period if body.new_date_end_period is not None else body.date_end_period
#                 new_teacher_id = body.new_teacher_id if body.new_teacher_id is not None else body.teacher_id

#                 if body.new_teacher_id is not None and body.new_teacher_id != body.teacher_id:
#                     if not await ensure_teacher_exists(teacher_dal, body.new_teacher_id):
#                         raise HTTPException(
#                             status_code=status.HTTP_404_NOT_FOUND,
#                             detail=f"Учитель: {body.new_teacher_id} не существует"
#                         )

#                 if (new_date_start != body.date_start_period or
#                     new_date_end != body.date_end_period or
#                     new_teacher_id != body.teacher_id):

#                     if not await ensure_employment_unique(employment_dal, new_date_start, new_date_end, new_teacher_id):
#                         raise HTTPException(
#                             status_code=status.HTTP_400_BAD_REQUEST,
#                             detail=f"График преподавателя {new_teacher_id} начиная с {new_date_start} и заканчивая {new_date_end} уже существует"
#                         )

#                 if body.new_date_start_period is not None:
#                     update_data["date_start_period"] = body.new_date_start_period
#                 if body.new_date_end_period is not None:
#                     update_data["date_end_period"] = body.new_date_end_period
#                 if body.new_teacher_id is not None:
#                     update_data["teacher_id"] = body.new_teacher_id

#                 employment = await employment_dal.update_employTeacher(
#                     tg_date_start_period=body.date_start_period,
#                     tg_date_end_period=body.date_end_period,
#                     tg_teacher_id=body.teacher_id,
#                     **update_data
#                 )

#                 if not employment:
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail=f"График преподавателя {body.teacher_id} начиная с {body.date_start_period} и заканчивая {body.date_end_period} не найден"
#                     )

#                 employment_pydantic = ShowEmployment.model_validate(employment)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 final_date_start = employment.date_start_period.isoformat()
#                 final_date_end = employment.date_end_period.isoformat()
#                 final_teacher_id = employment.teacher_id

#                 hateoas_links = {
#                     "self": f'{api_base_url}/employments/search/{final_teacher_id}/{final_date_start}/{final_date_end}',
#                     "update": f'{api_base_url}/employments/update/{final_teacher_id}/{final_date_start}/{final_date_end}',
#                     "delete": f'{api_base_url}/employments/delete/{final_teacher_id}/{final_date_start}/{final_date_end}',
#                     "employments": f'{api_base_url}/employments',
#                     "teacher": f'{api_base_url}/teachers/search/{final_teacher_id}'
#                 }

#                 return ShowEmploymentWithHATEOAS(employment=employment_pydantic, links=hateoas_links)

#         except HTTPException:
#             await session.rollback()
#             raise

#         except Exception as e:
#             await session.rollback()
#             logger.error(
#                 f"Неожиданная ошибка при обновлении графика занятости преподавателя {body.teacher_id} с {body.date_start_period} по {body.date_end_period}: {e}",
#                 exc_info=True
#             )
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="Внутренняя ошибка сервера при обновлении графика занятости."
#             )


# @employment_router.post("/create", response_model=ShowEmploymentWithHATEOAS, status_code=status.HTTP_201_CREATED)
# async def create_employment(body: CreateEmployment, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _create_new_employment(body, request, db)


# @employment_router.get("/search/by_date/{date_start_period}/{date_end_period}", response_model=ShowEmploymentListWithHATEOAS,
#                     responses={404: {"description": "Графики не найдены"}})
# async def get_all_employments_by_date(date_start_period: date, date_end_period: date, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
#     return await _get_all_employments_by_date(date_start_period, date_end_period, query_param.page, query_param.limit, request, db)


# @employment_router.get("/search/{teacher_id}/{date_start_period}/{date_end_period}", response_model=ShowEmploymentWithHATEOAS,
#                     responses={404: {"description": "График не найден"}})
# async def get_employment(date_start_period: date, date_end_period: date, teacher_id: int, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _get_employment(date_start_period, date_end_period, teacher_id, request, db)


# @employment_router.get("/search", response_model=ShowEmploymentListWithHATEOAS,
#                     responses={404: {"description": "Графики не найдены"}})
# async def get_all_employments(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
#     return await _get_all_employments(query_param.page, query_param.limit, request, db)


# @employment_router.delete("/delete/{teacher_id}/{date_start_period}/{date_end_period}", response_model=ShowEmploymentWithHATEOAS,
#                     responses={404: {"description": "График не найден"}})
# async def delete_employment(date_start_period: date, date_end_period: date, teacher_id: int, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _delete_employment(date_start_period, date_end_period, teacher_id, request, db)


# @employment_router.put("/update", response_model=ShowEmploymentWithHATEOAS,
#                     responses={404: {"description": "График не найден"}})
# async def update_employment(body: UpdateEmployment, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _update_employment(body, request, db)



# '''
# ==================================
# CRUD operations for TeacherRequest
# ==================================
# '''


# async def _create_new_request(body: CreateTeacherRequest, request: Request, db) -> ShowTeacherRequestWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             request_dal = TeacherRequestDAL(session)
#             group_dal = GroupDAL(session)
#             teacher_dal = TeacherDAL(session)
#             subject_dal = SubjectDAL(session)

#             try:
#                 if not await ensure_teacher_exists(teacher_dal, body.teacher_id):
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail=f"Учитель: {body.teacher_id} не существует"
#                     )

#                 if not await ensure_subject_exists(subject_dal, body.subject_code):
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail=f"Предмет: {body.subject_code} не существует"
#                     )

#                 if not await ensure_group_exists(group_dal, body.group_name):
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail=f"Группа: {body.group_name} не существует"
#                     )

#                 if not await ensure_request_unique(
#                     request_dal,
#                     body.date_request,
#                     body.teacher_id,
#                     body.subject_code,
#                     body.group_name
#                 ):
#                     raise HTTPException(
#                         status_code=status.HTTP_400_BAD_REQUEST,
#                         detail=f"Запрос преподавателя {body.teacher_id} на предмет {body.subject_code} для группы {body.group_name} на дату {body.date_request} уже существует"
#                     )

#                 request_obj = await request_dal.create_teacherRequest(
#                     date_request=body.date_request,
#                     teacher_id=body.teacher_id,
#                     subject_code=body.subject_code,
#                     group_name=body.group_name,
#                     lectures_hours=body.lectures_hours,
#                     laboratory_hours=body.laboratory_hours,
#                     practice_hours=body.practice_hours
#                 )

#                 request_pydantic = ShowTeacherRequest.model_validate(request_obj)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 date_req_str = request_obj.date_request.isoformat()
#                 teacher_id = request_obj.teacher_id
#                 subject_code = request_obj.subject_code
#                 group_name = request_obj.group_name

#                 hateoas_links = {
#                     "self": f'{api_base_url}/requests/search/{date_req_str}/{teacher_id}/{subject_code}/{group_name}',
#                     "update": f'{api_base_url}/requests/update/{date_req_str}/{teacher_id}/{subject_code}/{group_name}',
#                     "delete": f'{api_base_url}/requests/delete/{date_req_str}/{teacher_id}/{subject_code}/{group_name}',
#                     "requests": f'{api_base_url}/requests',
#                     "teacher": f'{api_base_url}/teachers/search/by_id/{teacher_id}',
#                     "subject": f'{api_base_url}/subjects/search/by_code/{subject_code}',
#                     "group": f'{api_base_url}/groups/search/by_group_name/{group_name}'
#                 }

#                 return ShowTeacherRequestWithHATEOAS(request=request_pydantic, links=hateoas_links)

#             except HTTPException:
#                 await session.rollback()
#                 raise

#             except Exception as e:
#                 await session.rollback()
#                 logger.error(
#                     f"Неожиданная ошибка при создании запроса преподавателя {body.teacher_id} на предмет {body.subject_code} для группы {body.group_name} на дату {body.date_request}: {e}",
#                     exc_info=True
#                 )
#                 raise HTTPException(
#                     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                     detail="Внутренняя ошибка сервера при создании запроса преподавателя."
#                 )


# async def _get_request(
#     date_request: date, teacher_id: int, subject_code: str, group_name: str, request: Request, db) -> ShowTeacherRequestWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             request_dal = TeacherRequestDAL(session)
#             try:
#                 request_obj = await request_dal.get_teacherRequest(date_request, teacher_id, subject_code, group_name)

#                 # if request doesn't exist
#                 if not request_obj:
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail=f"Запрос преподавателя {teacher_id} на предмет {subject_code} для группы {group_name} на дату {date_request} не найден"
#                     )

#                 request_pydantic = ShowTeacherRequest.model_validate(request_obj)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 date_req_str = date_request.isoformat()

#                 hateoas_links = {
#                     "self": f'{api_base_url}/requests/search/{date_req_str}/{teacher_id}/{subject_code}/{group_name}',
#                     "update": f'{api_base_url}/requests/update/{date_req_str}/{teacher_id}/{subject_code}/{group_name}',
#                     "delete": f'{api_base_url}/requests/delete/{date_req_str}/{teacher_id}/{subject_code}/{group_name}',
#                     "requests": f'{api_base_url}/requests',
#                     "teacher": f'{api_base_url}/teachers/search/by_id/{teacher_id}',
#                     "subject": f'{api_base_url}/subjects/search/by_code/{subject_code}',
#                     "group": f'{api_base_url}/groups/search/by_group_name/{group_name}'
#                 }

#                 return ShowTeacherRequestWithHATEOAS(request=request_pydantic, links=hateoas_links)

#             except HTTPException:
#                 raise
#             except Exception as e:
#                 logger.error(
#                     f"Неожиданная ошибка при получении запроса преподавателя {teacher_id} на предмет {subject_code} для группы {group_name} на дату {date_request}: {e}",
#                     exc_info=True
#                 )
#                 raise HTTPException(
#                     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                     detail="Внутренняя ошибка сервера при получении запроса преподавателя."
#                 )


# async def _get_all_requests(page: int, limit: int, request: Request, db) -> ShowTeacherRequestListWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             request_dal = TeacherRequestDAL(session)
#             try:
#                 requests_orm_list = await request_dal.get_all_teachersRequests(page, limit)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 requests_with_hateoas = []
#                 for request_orm in requests_orm_list:
#                     request_pydantic = ShowTeacherRequest.model_validate(request_orm)

#                     req_date_str = request_orm.date_request.isoformat()
#                     req_teacher_id = request_orm.teacher_id
#                     req_subject_code = request_orm.subject_code
#                     req_group_name = request_orm.group_name

#                     request_links = {
#                         "self": f'{api_base_url}/requests/search/{req_date_str}/{req_teacher_id}/{req_subject_code}/{req_group_name}',
#                         "update": f'{api_base_url}/requests/update/{req_date_str}/{req_teacher_id}/{req_subject_code}/{req_group_name}',
#                         "delete": f'{api_base_url}/requests/delete/{req_date_str}/{req_teacher_id}/{req_subject_code}/{req_group_name}',
#                         "teacher": f'{api_base_url}/teachers/search/by_id/{req_teacher_id}',
#                         "subject": f'{api_base_url}/subjects/search/by_code/{req_subject_code}',
#                         "group": f'{api_base_url}/groups/search/by_group_name/{req_group_name}',
#                     }

#                     request_with_links = ShowTeacherRequestWithHATEOAS(
#                         request=request_pydantic,
#                         links=request_links
#                     )
#                     requests_with_hateoas.append(request_with_links)

#                 collection_links = {
#                     "self": f'{api_base_url}/requests/search?page={page}&limit={limit}',
#                     "create": f'{api_base_url}/requests/create',
#                     "requests": f'{api_base_url}/requests',
#                 }

#                 return ShowTeacherRequestListWithHATEOAS(
#                     requests=requests_with_hateoas,
#                     links=collection_links
#                 )

#             except Exception as e:
#                 logger.error(f"Неожиданная ошибка при получении списка запросов преподавателей (page={page}, limit={limit}): {e}", exc_info=True)
#                 raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при получении списка запросов преподавателей.")



# async def _get_all_requests_by_teacher(
#     teacher_id: int, page: int, limit: int, request: Request, db) -> ShowTeacherRequestListWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             request_dal = TeacherRequestDAL(session)
#             try:
#                 requests_orm_list = await request_dal.get_all_requests_by_teacher(teacher_id, page, limit)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 requests_with_hateoas = []
#                 for request_orm in requests_orm_list:
#                     request_pydantic = ShowTeacherRequest.model_validate(request_orm)

#                     req_date_str = request_orm.date_request.isoformat()
#                     req_teacher_id = request_orm.teacher_id
#                     req_subject_code = request_orm.subject_code
#                     req_group_name = request_orm.group_name

#                     request_links = {
#                         "self": f'{api_base_url}/requests/search/{req_date_str}/{req_teacher_id}/{req_subject_code}/{req_group_name}',
#                         "update": f'{api_base_url}/requests/update/{req_date_str}/{req_teacher_id}/{req_subject_code}/{req_group_name}',
#                         "delete": f'{api_base_url}/requests/delete/{req_date_str}/{req_teacher_id}/{req_subject_code}/{req_group_name}',
#                         "teacher": f'{api_base_url}/teachers/search/by_id/{req_teacher_id}',
#                         "subject": f'{api_base_url}/subjects/search/by_code/{req_subject_code}',
#                         "group": f'{api_base_url}/groups/search/by_group_name/{req_group_name}',
#                     }

#                     request_with_links = ShowTeacherRequestWithHATEOAS(
#                         request=request_pydantic,
#                         links=request_links
#                     )
#                     requests_with_hateoas.append(request_with_links)

#                 collection_links = {
#                     "self": f'{api_base_url}/requests/search/by_teacher/{teacher_id}?page={page}&limit={limit}',
#                     "create": f'{api_base_url}/requests/create',
#                     "requests": f'{api_base_url}/requests',
#                     "teacher": f'{api_base_url}/teachers/search/{teacher_id}',
#                 }

#                 return ShowTeacherRequestListWithHATEOAS(
#                     requests=requests_with_hateoas,
#                     links=collection_links
#                 )

#             except Exception as e:
#                 logger.error(
#                     f"Неожиданная ошибка при получении списка запросов преподавателя {teacher_id} (page={page}, limit={limit}): {e}",
#                     exc_info=True
#                 )
#                 raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при получении списка запросов преподавателя.")



# async def _get_all_requests_by_group(group_name: str, page: int, limit: int, request: Request, db) -> ShowTeacherRequestListWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             request_dal = TeacherRequestDAL(session)
#             try:
#                 requests_orm_list = await request_dal.get_all_requests_by_group(group_name, page, limit)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 requests_with_hateoas = []
#                 for request_orm in requests_orm_list:
#                     request_pydantic = ShowTeacherRequest.model_validate(request_orm)

#                     req_date_str = request_orm.date_request.isoformat()
#                     req_teacher_id = request_orm.teacher_id
#                     req_subject_code = request_orm.subject_code
#                     req_group_name = request_orm.group_name

#                     request_links = {
#                         "self": f'{api_base_url}/requests/search/{req_date_str}/{req_teacher_id}/{req_subject_code}/{req_group_name}',
#                         "update": f'{api_base_url}/requests/update/{req_date_str}/{req_teacher_id}/{req_subject_code}/{req_group_name}',
#                         "delete": f'{api_base_url}/requests/delete/{req_date_str}/{req_teacher_id}/{req_subject_code}/{req_group_name}',
#                         "teacher": f'{api_base_url}/teachers/search/by_id/{req_teacher_id}',
#                         "subject": f'{api_base_url}/subjects/search/by_code/{req_subject_code}',
#                         "group": f'{api_base_url}/groups/search/by_group_name/{req_group_name}',
#                     }
#                     request_with_links = ShowTeacherRequestWithHATEOAS(
#                         request=request_pydantic,
#                         links=request_links
#                     )
#                     requests_with_hateoas.append(request_with_links)

#                 collection_links = {
#                     "self": f'{api_base_url}/requests/search/by_group/{group_name}?page={page}&limit={limit}',
#                     "create": f'{api_base_url}/requests/create',
#                     "requests": f'{api_base_url}/requests',
#                     "group": f'{api_base_url}/groups/search/by_group-name/{group_name}'
#                 }

#                 return ShowTeacherRequestListWithHATEOAS(
#                     requests=requests_with_hateoas,
#                     links=collection_links
#                 )

#             except Exception as e:
#                 logger.error(
#                     f"Неожиданная ошибка при получении списка запросов для группы {group_name} (page={page}, limit={limit}): {e}",
#                     exc_info=True
#                 )
#                 raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при получении списка запросов для группы.")



# async def _get_all_requests_by_subject(subject_code: str, page: int, limit: int, request: Request, db) -> ShowTeacherRequestListWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             request_dal = TeacherRequestDAL(session)
#             try:
#                 requests_orm_list = await request_dal.get_all_requests_by_subject(subject_code, page, limit)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 requests_with_hateoas = []
#                 for request_orm in requests_orm_list:
#                     request_pydantic = ShowTeacherRequest.model_validate(request_orm)

#                     req_date_str = request_orm.date_request.isoformat()
#                     req_teacher_id = request_orm.teacher_id
#                     req_subject_code = request_orm.subject_code
#                     req_group_name = request_orm.group_name

#                     request_links = {
#                         "self": f'{api_base_url}/requests/search/{req_date_str}/{req_teacher_id}/{req_subject_code}/{req_group_name}',
#                         "update": f'{api_base_url}/requests/update/{req_date_str}/{req_teacher_id}/{req_subject_code}/{req_group_name}',
#                         "delete": f'{api_base_url}/requests/delete/{req_date_str}/{req_teacher_id}/{req_subject_code}/{req_group_name}',
#                         "teacher": f'{api_base_url}/teachers/search/by_id/{req_teacher_id}',
#                         "subject": f'{api_base_url}/subjects/search/by_code/{req_subject_code}',
#                         "group": f'{api_base_url}/groups/search/by_group_name/{req_group_name}',
#                     }

#                     request_with_links = ShowTeacherRequestWithHATEOAS(
#                         request=request_pydantic,
#                         links=request_links
#                     )
#                     requests_with_hateoas.append(request_with_links)

#                 collection_links = {
#                     "self": f'{api_base_url}/requests/search/by_subject/{subject_code}?page={page}&limit={limit}',
#                     "create": f'{api_base_url}/requests/create',
#                     "requests": f'{api_base_url}/requests',
#                     "subject": f'{api_base_url}/subjects/search/by_code/{subject_code}'
#                 }

#                 return ShowTeacherRequestListWithHATEOAS(
#                     requests=requests_with_hateoas,
#                     links=collection_links
#                 )

#             except Exception as e:
#                 logger.error(
#                     f"Неожиданная ошибка при получении списка запросов для предмета {subject_code} (page={page}, limit={limit}): {e}",
#                     exc_info=True
#                 )
#                 raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при получении списка запросов для предмета.")



# async def _delete_request(date_request: date, teacher_id: int, subject_code: str, group_name: str, request: Request, db) -> ShowTeacherRequestWithHATEOAS:
#     async with db as session:
#         try:
#             async with session.begin():
#                 request_dal = TeacherRequestDAL(session)
#                 request_obj = await request_dal.delete_teacherRequest(date_request, teacher_id, subject_code, group_name)

#                 if not request_obj:
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail=f"Запрос преподавателя {teacher_id} на предмет {subject_code} для группы {group_name} на дату {date_request} не найден"
#                     )

#                 request_pydantic = ShowTeacherRequest.model_validate(request_obj)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 date_req_str = date_request.isoformat()

#                 hateoas_links = {
#                     "self": f'{api_base_url}/requests/search/{date_req_str}/{teacher_id}/{subject_code}/{group_name}',
#                     "requests": f'{api_base_url}/requests',
#                     "create": f'{api_base_url}/requests/create',
#                     "teacher": f'{api_base_url}/teachers/search/by_id/{teacher_id}',
#                     "subject": f'{api_base_url}/subjects/search/by_code/{subject_code}',
#                     "group": f'{api_base_url}/groups/search/by_group_name/{group_name}',
#                 }

#                 return ShowTeacherRequestWithHATEOAS(request=request_pydantic, links=hateoas_links)

#         except HTTPException:
#             await session.rollback()
#             raise
#         except Exception as e:
#             await session.rollback()
#             logger.error(
#                 f"Неожиданная ошибка при удалении запроса преподавателя {teacher_id} на предмет {subject_code} для группы {group_name} на дату {date_request}: {e}",
#                 exc_info=True
#             )
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="Внутренняя ошибка сервера при удалении запроса преподавателя." #
#             )


# async def _update_request(body: UpdateTeacherRequest, request: Request, db) -> ShowTeacherRequestWithHATEOAS:
#     async with db as session:
#         try:
#             async with session.begin():
#                 update_data = {
#                     key: value for key, value in body.dict().items()
#                     if value is not None and key not in ["date_request", "teacher_id", "subject_code", "group_name", "new_date_request", "new_teacher_id", "new_subject_code", "new_group_name"]
#                 }

#                 request_dal = TeacherRequestDAL(session)
#                 group_dal = GroupDAL(session)
#                 teacher_dal = TeacherDAL(session)
#                 subject_dal = SubjectDAL(session)

#                 new_date_req = body.new_date_request if body.new_date_request is not None else body.date_request
#                 new_teacher_id = body.new_teacher_id if body.new_teacher_id is not None else body.teacher_id
#                 new_subject_code = body.new_subject_code if body.new_subject_code is not None else body.subject_code
#                 new_group_name = body.new_group_name if body.new_group_name is not None else body.group_name

#                 if body.new_teacher_id is not None and body.new_teacher_id != body.teacher_id:
#                     if not await ensure_teacher_exists(teacher_dal, body.new_teacher_id):
#                         raise HTTPException(
#                             status_code=status.HTTP_404_NOT_FOUND,
#                             detail=f"Учитель: {body.new_teacher_id} не существует"
#                         )
#                 if body.new_subject_code is not None and body.new_subject_code != body.subject_code:
#                     if not await ensure_subject_exists(subject_dal, body.new_subject_code):
#                         raise HTTPException(
#                             status_code=status.HTTP_404_NOT_FOUND,
#                             detail=f"Предмет: {body.new_subject_code} не существует"
#                         )
#                 if body.new_group_name is not None and body.new_group_name != body.group_name:
#                     if not await ensure_group_exists(group_dal, body.new_group_name):
#                         raise HTTPException(
#                             status_code=status.HTTP_404_NOT_FOUND,
#                             detail=f"Группа: {body.new_group_name} не существует"
#                         )

#                 if (new_date_req != body.date_request or
#                     new_teacher_id != body.teacher_id or
#                     new_subject_code != body.subject_code or
#                     new_group_name != body.group_name):

#                     if not await ensure_request_unique(
#                         request_dal,
#                         new_date_req,
#                         new_teacher_id,
#                         new_subject_code,
#                         new_group_name
#                     ):
#                         raise HTTPException(
#                             status_code=status.HTTP_400_BAD_REQUEST,
#                             detail=f"Запрос преподавателя {new_teacher_id} на предмет {new_subject_code} для группы {new_group_name} на дату {new_date_req} уже существует"
#                         )

#                 if body.new_date_request is not None:
#                     update_data["date_request"] = body.new_date_request
#                 if body.new_teacher_id is not None:
#                     update_data["teacher_id"] = body.new_teacher_id
#                 if body.new_subject_code is not None:
#                     update_data["subject_code"] = body.new_subject_code
#                 if body.new_group_name is not None:
#                     update_data["group_name"] = body.new_group_name

#                 request_obj = await request_dal.update_teacherRequest(
#                     tg_date_request=body.date_request,
#                     tg_teacher_id=body.teacher_id,
#                     tg_subject_code=body.subject_code,
#                     tg_group_name=body.group_name,
#                     **update_data
#                 )

#                 if not request_obj:
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail=f"Запрос преподавателя {body.teacher_id} на предмет {body.subject_code} для группы {body.group_name} на дату {body.date_request} не найден"
#                     )

#                 request_pydantic = ShowTeacherRequest.model_validate(request_obj)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 final_date_req_str = request_obj.date_request.isoformat()
#                 final_teacher_id = request_obj.teacher_id
#                 final_subject_code = request_obj.subject_code
#                 final_group_name = request_obj.group_name

#                 hateoas_links = {
#                     "self": f'{api_base_url}/requests/search/{final_date_req_str}/{final_teacher_id}/{final_subject_code}/{final_group_name}',
#                     "update": f'{api_base_url}/requests/update/{final_date_req_str}/{final_teacher_id}/{final_subject_code}/{final_group_name}',
#                     "delete": f'{api_base_url}/requests/delete/{final_date_req_str}/{final_teacher_id}/{final_subject_code}/{final_group_name}',
#                     "requests": f'{api_base_url}/requests',
#                     "teacher": f'{api_base_url}/teachers/search/by_id/{final_teacher_id}',
#                     "subject": f'{api_base_url}/subjects/search/by_code/{final_subject_code}',
#                     "group": f'{api_base_url}/groups/search/by_group_name/{final_group_name}'
#                 }

#                 return ShowTeacherRequestWithHATEOAS(request=request_pydantic, links=hateoas_links)

#         except HTTPException:
#             await session.rollback()
#             raise
#         except Exception as e:
#             await session.rollback()
#             logger.error(
#                 f"Неожиданная ошибка при обновлении запроса преподавателя {body.teacher_id} на предмет {body.subject_code} для группы {body.group_name} на дату {body.date_request}: {e}",
#                 exc_info=True
#             )
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="Внутренняя ошибка сервера при обновлении запроса преподавателя."
#             )


# @request_router.post("/create", response_model=ShowTeacherRequestWithHATEOAS, status_code=status.HTTP_201_CREATED)
# async def create_request(body: CreateTeacherRequest, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _create_new_request(body, request, db)


# @request_router.get("/search/{date_request}/{teacher_id}/{subject_code}/{group_name}", response_model=ShowTeacherRequestWithHATEOAS,
#                     responses={404: {"description": "Запрос не найден"}})
# async def get_request(date_request: date, teacher_id: int, subject_code: str, group_name: str, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _get_request(date_request, teacher_id, subject_code, group_name, request, db)


# @request_router.get("/search", response_model=ShowTeacherRequestListWithHATEOAS,
#                     responses={404: {"description": "Запросы не найдены"}})
# async def get_all_requests(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
#     return await _get_all_requests(query_param.page, query_param.limit, request, db)


# @request_router.get("/search/by_teacher/{teacher_id}",
#                     response_model=ShowTeacherRequestListWithHATEOAS,
#                     responses={404: {"description": "Запросы не найдены"}})
# async def get_all_requests_by_teacher(teacher_id: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
#     return await _get_all_requests_by_teacher(teacher_id, query_param.page, query_param.limit, request, db)


# @request_router.get("/search/by_group/{group_name}",
#                     response_model=ShowTeacherRequestListWithHATEOAS,
#                     responses={404: {"description": "Запросы не найдены"}})
# async def get_all_requests_by_group(group_name: str, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
#     return await _get_all_requests_by_group(group_name, query_param.page, query_param.limit, request, db)


# @request_router.get("/search/by_subject/{subject_code}",
#                     response_model=ShowTeacherRequestListWithHATEOAS,
#                     responses={404: {"description": "Запросы не найдены"}})
# async def get_all_requests_by_subject(subject_code: str, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
#     return await _get_all_requests_by_subject(subject_code, query_param.page, query_param.limit, request, db)


# @request_router.delete("/delete/{date_request}/{teacher_id}/{subject_code}/{group_name}", response_model=ShowTeacherRequestWithHATEOAS,
#                     responses={404: {"description": "Запрос не найден"}})
# async def delete_request(date_request: date, teacher_id: int, subject_code: str, group_name: str, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _delete_request(date_request, teacher_id, subject_code, group_name, request, db)


# @request_router.put("/update", response_model=ShowTeacherRequestWithHATEOAS,
#                     responses={404: {"description": "Запрос не найден"}})
# async def update_request(body: UpdateTeacherRequest, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _update_request(body, request, db)


# '''
# ===========================
# CRUD operations for Session
# ===========================
# '''


# async def _create_new_session(body: CreateSession, request: Request, db) -> ShowSessionWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             session_dal = SessionDAL(session)
#             group_dal = GroupDAL(session)
#             cabinet_dal = CabinetDAL(session)
#             subject_dal = SubjectDAL(session)
#             teacher_dal = TeacherDAL(session)

#             try:
#                 if not await ensure_group_exists(group_dal, body.group_name):
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail=f"Группа: {body.group_name} не существует"
#                     )

#                 if body.subject_code is not None and not await ensure_subject_exists(subject_dal, body.subject_code):
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail=f"Предмет: {body.subject_code} не существует"
#                     )

#                 if body.teacher_id is not None and not await ensure_teacher_exists(teacher_dal, body.teacher_id):
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail=f"Преподаватель: {body.teacher_id} не существует"
#                     )

#                 if (body.cabinet_number is not None and body.building_number is not None and
#                     not await ensure_cabinet_exists(cabinet_dal, body.cabinet_number, body.building_number)):
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail=f"Кабинет: {body.cabinet_number} в здании номер: {body.building_number} не существует"
#                     )

#                 if not await ensure_session_unique(session_dal, body.session_number, body.date, body.group_name):
#                     raise HTTPException(
#                         status_code=status.HTTP_400_BAD_REQUEST,
#                         detail=f"Сессия у преподавателя под номером {body.session_number} для группы {body.group_name} на дату {body.date} уже существует"
#                     )

#                 session_obj = await session_dal.create_session(
#                     session_number=body.session_number,
#                     date=body.date,
#                     group_name=body.group_name,
#                     session_type=body.session_type,
#                     subject_code=body.subject_code,
#                     teacher_id=body.teacher_id,
#                     cabinet_number=body.cabinet_number,
#                     building_number=body.building_number
#                 )

#                 session_pydantic = ShowSession.model_validate(session_obj)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 sess_number = session_obj.session_number
#                 sess_date_str = session_obj.date.isoformat()
#                 sess_group_name = session_obj.group_name

#                 hateoas_links = {
#                     "self": f'{api_base_url}/sessions/search/{sess_number}/{sess_date_str}/{sess_group_name}',
#                     "update": f'{api_base_url}/sessions/update/{sess_number}/{sess_date_str}/{sess_group_name}',
#                     "delete": f'{api_base_url}/sessions/delete/{sess_number}/{sess_date_str}/{sess_group_name}',
#                     "sessions": f'{api_base_url}/sessions',
#                     "group": f'{api_base_url}/groups/search/by_group-name/{sess_group_name}',
#                     "subject": f'{api_base_url}/subjects/search/{session_obj.subject_code}' if session_obj.subject_code else None,
#                     "teacher": f'{api_base_url}/teachers/search/{session_obj.teacher_id}' if session_obj.teacher_id else None,
#                     "cabinet": f'{api_base_url}/cabinets/search/{session_obj.building_number}/{session_obj.cabinet_number}' if session_obj.cabinet_number is not None and session_obj.building_number is not None else None
#                 }
#                 hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

#                 return ShowSessionWithHATEOAS(session=session_pydantic, links=hateoas_links)

#             except HTTPException:
#                 await session.rollback()
#                 raise
#             except Exception as e:
#                 await session.rollback()
#                 logger.error(f"Неожиданная ошибка при создании сессии: {e}", exc_info=True)
#                 raise HTTPException(
#                     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                     detail="Внутренняя ошибка сервера при создании сессии."
#                 )


# async def _get_session(
#     session_number: int, date: date, group_name: str, request: Request, db) -> ShowSessionWithHATEOAS:
#     async with db as session:
#         session_dal = SessionDAL(session)
#         try:
#             data_session = await session_dal.get_session(session_number, date, group_name)

#             if not data_session:
#                 raise HTTPException(
#                     status_code=status.HTTP_404_NOT_FOUND,
#                     detail=f"Сессия под номером {session_number} для группы {group_name} на дату {date} не найдена"
#                 )

#             session_pydantic = ShowSession.model_validate(data_session)

#             base_url = str(request.base_url).rstrip('/')
#             api_prefix = ''
#             api_base_url = f'{base_url}{api_prefix}'

#             sess_date_str = date.isoformat()

#             sess_number = session_number
#             sess_group_name = group_name

#             hateoas_links = {
#                 "self": f'{api_base_url}/sessions/search/{sess_number}/{sess_date_str}/{sess_group_name}',
#                 "update": f'{api_base_url}/sessions/update/{sess_number}/{sess_date_str}/{sess_group_name}',
#                 "delete": f'{api_base_url}/sessions/delete/{sess_number}/{sess_date_str}/{sess_group_name}',
#                 "sessions": f'{api_base_url}/sessions',
#                 "group": f'{api_base_url}/groups/search/by_group-name/{sess_group_name}',
#                 "subject": f'{api_base_url}/subjects/search/{data_session.subject_code}' if data_session.subject_code else None,
#                 "teacher": f'{api_base_url}/teachers/search/{data_session.teacher_id}' if data_session.teacher_id else None,
#                 "cabinet": f'{api_base_url}/cabinets/search/{data_session.building_number}/{data_session.cabinet_number}' if data_session.cabinet_number is not None and data_session.building_number is not None else None
#             }
#             hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

#             return ShowSessionWithHATEOAS(session=session_pydantic, links=hateoas_links)

#         except HTTPException:
#             raise
#         except Exception as e:
#             logger.error(
#                 f"Неожиданная ошибка при получении сессии {session_number} для группы {group_name} на дату {date}: {e}",
#                 exc_info=True
#             )
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="Внутренняя ошибка сервера при получении сессии."
#             )


# async def _get_all_sessions(page: int, limit: int, request: Request, db) -> ShowSessionListWithHATEOAS:
#     async with db as session:
#         session_dal = SessionDAL(session)
#         try:
#             data_sessions_orm_list = await session_dal.get_all_sessions(page, limit)

#             base_url = str(request.base_url).rstrip('/')
#             api_prefix = ''
#             api_base_url = f'{base_url}{api_prefix}'

#             sessions_with_hateoas = []
#             for session_orm in data_sessions_orm_list:
#                 session_pydantic = ShowSession.model_validate(session_orm)

#                 sess_number = session_orm.session_number
#                 sess_date_str = session_orm.date.isoformat()
#                 sess_group_name = session_orm.group_name

#                 session_links = {
#                     "self": f'{api_base_url}/sessions/search/{sess_number}/{sess_date_str}/{sess_group_name}',
#                     "update": f'{api_base_url}/sessions/update/{sess_number}/{sess_date_str}/{sess_group_name}',
#                     "delete": f'{api_base_url}/sessions/delete/{sess_number}/{sess_date_str}/{sess_group_name}',
#                     "group": f'{api_base_url}/groups/search/by_group-name/{sess_group_name}',
#                     "subject": f'{api_base_url}/subjects/search/{session_orm.subject_code}' if session_orm.subject_code else None,
#                     "teacher": f'{api_base_url}/teachers/search/{session_orm.teacher_id}' if session_orm.teacher_id else None,
#                     "cabinet": f'{api_base_url}/cabinets/search/{session_orm.building_number}/{session_orm.cabinet_number}' if session_orm.cabinet_number is not None and session_orm.building_number is not None else None,
#                 }
#                 session_links = {k: v for k, v in session_links.items() if v is not None}

#                 session_with_links = ShowSessionWithHATEOAS(
#                     session=session_pydantic,
#                     links=session_links
#                 )
#                 sessions_with_hateoas.append(session_with_links)

#             collection_links = {
#                 "self": f'{api_base_url}/sessions/search?page={page}&limit={limit}',
#                 "create": f'{api_base_url}/sessions/create',
#                 "sessions": f'{api_base_url}/sessions'
#             }

#             return ShowSessionListWithHATEOAS(
#                 sessions=sessions_with_hateoas,
#                 links=collection_links
#             )

#         except Exception as e:
#             logger.error(f"Неожиданная ошибка при получении списка сессий (page={page}, limit={limit}): {e}", exc_info=True)
#             raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при получении списка сессий.")


# async def _get_all_sessions_by_date(date: date, page: int, limit: int, request: Request, db) -> ShowSessionListWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             session_dal = SessionDAL(session)
#             try:
#                 data_sessions_orm_list = await session_dal.get_all_sessions_by_date(date, page, limit)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 sessions_with_hateoas = []
#                 for session_orm in data_sessions_orm_list:
#                     session_pydantic = ShowSession.model_validate(session_orm)

#                     sess_number = session_orm.session_number
#                     sess_date_str = session_orm.date.isoformat()
#                     sess_group_name = session_orm.group_name

#                     session_links = {
#                         "self": f'{api_base_url}/sessions/search/{sess_number}/{sess_date_str}/{sess_group_name}',
#                         "update": f'{api_base_url}/sessions/update/{sess_number}/{sess_date_str}/{sess_group_name}',
#                         "delete": f'{api_base_url}/sessions/delete/{sess_number}/{sess_date_str}/{sess_group_name}',
#                         "group": f'{api_base_url}/groups/search/by_group-name/{sess_group_name}',
#                         "subject": f'{api_base_url}/subjects/search/{session_orm.subject_code}' if session_orm.subject_code else None,
#                         "teacher": f'{api_base_url}/teachers/search/{session_orm.teacher_id}' if session_orm.teacher_id else None,
#                         "cabinet": f'{api_base_url}/cabinets/search/{session_orm.building_number}/{session_orm.cabinet_number}' if session_orm.cabinet_number is not None and session_orm.building_number is not None else None,
#                     }
#                     session_links = {k: v for k, v in session_links.items() if v is not None}

#                     session_with_links = ShowSessionWithHATEOAS(
#                         session=session_pydantic,
#                         links=session_links
#                     )
#                     sessions_with_hateoas.append(session_with_links)

#                 date_str_for_url = date.isoformat()
#                 collection_links = {
#                     "self": f'{api_base_url}/sessions/search/by_date/{date_str_for_url}?page={page}&limit={limit}',
#                     "create": f'{api_base_url}/sessions/create',
#                     "sessions": f'{api_base_url}/sessions',
#                     "by_date": f'{api_base_url}/sessions/search/by_date/{date_str_for_url}'
#                 }

#                 return ShowSessionListWithHATEOAS(
#                     sessions=sessions_with_hateoas,
#                     links=collection_links
#                 )

#             except Exception as e:
#                 logger.error(f"Неожиданная ошибка при получении списка сессий по дате {date} (page={page}, limit={limit}): {e}", exc_info=True)
#                 raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при получении списка сессий.")



# async def _get_all_sessions_by_group( group_name: str, page: int, limit: int, request: Request, db) -> ShowSessionListWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             session_dal = SessionDAL(session)
#             try:
#                 data_sessions_orm_list = await session_dal.get_all_sessions_by_group(group_name, page, limit)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 sessions_with_hateoas = []
#                 for session_orm in data_sessions_orm_list:
#                     session_pydantic = ShowSession.model_validate(session_orm)

#                     sess_number = session_orm.session_number
#                     sess_date_str = session_orm.date.isoformat()
#                     sess_group_name = session_orm.group_name

#                     session_links = {
#                         "self": f'{api_base_url}/sessions/search/{sess_number}/{sess_date_str}/{sess_group_name}',
#                         "update": f'{api_base_url}/sessions/update/{sess_number}/{sess_date_str}/{sess_group_name}',
#                         "delete": f'{api_base_url}/sessions/delete/{sess_number}/{sess_date_str}/{sess_group_name}',
#                         "group": f'{api_base_url}/groups/search/by_group-name/{sess_group_name}',
#                         "subject": f'{api_base_url}/subjects/search/{session_orm.subject_code}' if session_orm.subject_code else None,
#                         "teacher": f'{api_base_url}/teachers/search/{session_orm.teacher_id}' if session_orm.teacher_id else None,
#                         "cabinet": f'{api_base_url}/cabinets/search/{session_orm.building_number}/{session_orm.cabinet_number}' if session_orm.cabinet_number is not None and session_orm.building_number is not None else None,
#                     }
#                     session_links = {k: v for k, v in session_links.items() if v is not None}

#                     session_with_links = ShowSessionWithHATEOAS(
#                         session=session_pydantic,
#                         links=session_links
#                     )
#                     sessions_with_hateoas.append(session_with_links)

#                 collection_links = {
#                     "self": f'{api_base_url}/sessions/search/by_group/{group_name}?page={page}&limit={limit}',
#                     "create": f'{api_base_url}/sessions/create',
#                     "sessions": f'{api_base_url}/sessions',
#                     "group": f'{api_base_url}/groups/search/by_group-name/{group_name}'
#                 }

#                 return ShowSessionListWithHATEOAS(
#                     sessions=sessions_with_hateoas,
#                     links=collection_links
#                 )

#             except Exception as e:
#                 logger.error(f"Неожиданная ошибка при получении списка сессий для группы {group_name} (page={page}, limit={limit}): {e}", exc_info=True)
#                 raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при получении списка сессий.")



# async def _get_all_sessions_by_subject(subject_code: str, page: int, limit: int, request: Request, db) -> ShowSessionListWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             session_dal = SessionDAL(session)
#             try:
#                 data_sessions_orm_list = await session_dal.get_all_sessions_by_subject(subject_code, page, limit)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 sessions_with_hateoas = []
#                 for session_orm in data_sessions_orm_list:
#                     session_pydantic = ShowSession.model_validate(session_orm)

#                     sess_number = session_orm.session_number
#                     sess_date_str = session_orm.date.isoformat()
#                     sess_group_name = session_orm.group_name

#                     session_links = {
#                         "self": f'{api_base_url}/sessions/search/{sess_number}/{sess_date_str}/{sess_group_name}',
#                         "update": f'{api_base_url}/sessions/update/{sess_number}/{sess_date_str}/{sess_group_name}',
#                         "delete": f'{api_base_url}/sessions/delete/{sess_number}/{sess_date_str}/{sess_group_name}',
#                         "group": f'{api_base_url}/groups/search/by_group-name/{sess_group_name}',
#                         "subject": f'{api_base_url}/subjects/search/{session_orm.subject_code}' if session_orm.subject_code else None,
#                         "teacher": f'{api_base_url}/teachers/search/{session_orm.teacher_id}' if session_orm.teacher_id else None,
#                         "cabinet": f'{api_base_url}/cabinets/search/{session_orm.building_number}/{session_orm.cabinet_number}' if session_orm.cabinet_number is not None and session_orm.building_number is not None else None,
#                     }
#                     session_links = {k: v for k, v in session_links.items() if v is not None}

#                     session_with_links = ShowSessionWithHATEOAS(
#                         session=session_pydantic,
#                         links=session_links
#                     )
#                     sessions_with_hateoas.append(session_with_links)

#                 collection_links = {
#                     "self": f'{api_base_url}/sessions/search/by_subject/{subject_code}?page={page}&limit={limit}',
#                     "create": f'{api_base_url}/sessions/create',
#                     "sessions": f'{api_base_url}/sessions',
#                     "subject": f'{api_base_url}/subjects/search/{subject_code}'
#                 }

#                 return ShowSessionListWithHATEOAS(
#                     sessions=sessions_with_hateoas,
#                     links=collection_links
#                 )

#             except Exception as e:
#                 logger.error(f"Неожиданная ошибка при получении списка сессий для предмета {subject_code} (page={page}, limit={limit}): {e}", exc_info=True)
#                 raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при получении списка сессий.")


# async def _get_all_sessions_by_teacher(teacher_id: int, page: int, limit: int, request: Request, db) -> ShowSessionListWithHATEOAS:
#     async with db as session:
#         async with session.begin():
#             session_dal = SessionDAL(session)
#             try:
#                 data_sessions_orm_list = await session_dal.get_all_sessions_by_teacher(teacher_id, page, limit)
#                 if data_sessions_orm_list is None:
#                     data_sessions_orm_list = []

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 sessions_with_hateoas = []
#                 for session_orm in data_sessions_orm_list:
#                     session_pydantic = ShowSession.model_validate(session_orm)

#                     sess_number = session_orm.session_number
#                     sess_date_str = session_orm.date.isoformat()
#                     sess_group_name = session_orm.group_name

#                     session_links = {
#                         "self": f'{api_base_url}/sessions/search/{sess_number}/{sess_date_str}/{sess_group_name}',
#                         "update": f'{api_base_url}/sessions/update/{sess_number}/{sess_date_str}/{sess_group_name}',
#                         "delete": f'{api_base_url}/sessions/delete/{sess_number}/{sess_date_str}/{sess_group_name}',
#                         "group": f'{api_base_url}/groups/search/by_group-name/{sess_group_name}',
#                         "subject": f'{api_base_url}/subjects/search/{session_orm.subject_code}' if session_orm.subject_code else None,
#                         "teacher": f'{api_base_url}/teachers/search/{session_orm.teacher_id}' if session_orm.teacher_id else None,
#                         "cabinet": f'{api_base_url}/cabinets/search/{session_orm.building_number}/{session_orm.cabinet_number}' if session_orm.cabinet_number is not None and session_orm.building_number is not None else None,
#                     }
#                     session_links = {k: v for k, v in session_links.items() if v is not None}

#                     session_with_links = ShowSessionWithHATEOAS(
#                         session=session_pydantic,
#                         links=session_links
#                     )
#                     sessions_with_hateoas.append(session_with_links)

#                 collection_links = {
#                     "self": f'{api_base_url}/sessions/search/by_teacher/{teacher_id}?page={page}&limit={limit}',
#                     "create": f'{api_base_url}/sessions/create',
#                     "sessions": f'{api_base_url}/sessions',
#                     "teacher": f'{api_base_url}/teachers/search/{teacher_id}'
#                 }

#                 return ShowSessionListWithHATEOAS(
#                     sessions=sessions_with_hateoas,
#                     links=collection_links
#                 )

#             except Exception as e:
#                 logger.error(f"Неожиданная ошибка при получении списка сессий для учителя {teacher_id} (page={page}, limit={limit}): {e}", exc_info=True)
#                 raise HTTPException(
#                     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                     detail="Внутренняя ошибка сервера при получении списка сессий."
#                 )


# async def _delete_session(session_number: int, date: date, group_name: str, request: Request, db) -> ShowSessionWithHATEOAS:
#     async with db as session:
#         try:
#             async with session.begin():
#                 session_dal = SessionDAL(session)
#                 data_session = await session_dal.delete_session(session_number, date, group_name)

#                 if not data_session:
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail=f"Сессия у преподавателя под номером {session_number} для группы {group_name} на дату {date} не найдена" # <-- Исправлено сообщение
#                     )

#                 session_pydantic = ShowSession.model_validate(data_session)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 sess_date_str = date.isoformat()

#                 sess_number = session_number
#                 sess_group_name = group_name

#                 hateoas_links = {
#                     "self": f'{api_base_url}/sessions/search/{sess_number}/{sess_date_str}/{sess_group_name}',
#                     "sessions": f'{api_base_url}/sessions',
#                     "create": f'{api_base_url}/sessions/create',
#                     "group": f'{api_base_url}/groups/search/by_group-name/{sess_group_name}',
#                     "subject": f'{api_base_url}/subjects/search/{data_session.subject_code}' if data_session.subject_code else None,
#                     "teacher": f'{api_base_url}/teachers/search/{data_session.teacher_id}' if data_session.teacher_id else None,
#                     "cabinet": f'{api_base_url}/cabinets/search/{data_session.building_number}/{data_session.cabinet_number}' if data_session.cabinet_number is not None and data_session.building_number is not None else None,
#                 }
#                 hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

#                 return ShowSessionWithHATEOAS(session=session_pydantic, links=hateoas_links)

#         except HTTPException:
#             await session.rollback()
#             raise
#         except Exception as e:
#             await session.rollback()
#             logger.error(
#                 f"Неожиданная ошибка при удалении сессии {session_number} для группы {group_name} на дату {date}: {e}",
#                 exc_info=True
#             )
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="Внутренняя ошибка сервера при удалении сессии."
#             )


# async def _update_session(body: UpdateSession, request: Request, db) -> ShowSessionWithHATEOAS:
#     async with db as session:
#         try:
#             async with session.begin():
#                 update_data = {
#                     key: value for key, value in body.dict().items()
#                     if value is not None and key not in ["session_number", "session_date", "group_name", "new_session_number", "new_session_date", "new_group_name"]
#                 }

#                 session_dal = SessionDAL(session)
#                 group_dal = GroupDAL(session)
#                 cabinet_dal = CabinetDAL(session)
#                 subject_dal = SubjectDAL(session)
#                 teacher_dal = TeacherDAL(session)

#                 if body.new_group_name is not None and body.new_group_name != body.group_name:
#                     if not await ensure_group_exists(group_dal, body.new_group_name):
#                         raise HTTPException(
#                             status_code=status.HTTP_404_NOT_FOUND,
#                             detail=f"Группа: {body.new_group_name} не существует"
#                         )

#                 if body.subject_code is not None and not await ensure_subject_exists(subject_dal, body.subject_code):
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail=f"Предмет: {body.subject_code} не существует"
#                     )

#                 if body.teacher_id is not None and not await ensure_teacher_exists(teacher_dal, body.teacher_id):
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail=f"Преподаватель: {body.teacher_id} не существует"
#                     )

#                 if (body.cabinet_number is not None and body.building_number is not None and
#                     not await ensure_cabinet_exists(cabinet_dal, body.cabinet_number, body.building_number)):
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail=f"Кабинет: {body.cabinet_number} в здании номер: {body.building_number} не существует"
#                     )

#                 if body.new_session_number is not None:
#                     update_data["session_number"] = body.new_session_number
#                 if body.new_session_date is not None:
#                     update_data["date"] = body.new_session_date
#                 if body.new_group_name is not None:
#                     update_data["group_name"] = body.new_group_name

#                 session_data = await session_dal.update_session(
#                     tg_session_number=body.session_number,
#                     tg_date=body.session_date,
#                     tg_group_name=body.group_name,
#                     **update_data
#                 )

#                 if not session_data:
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail=f"Сессия под номером {body.session_number} для группы {body.group_name} на дату {body.session_date} не найдена"
#                     )

#                 session_pydantic = ShowSession.model_validate(session_data)

#                 base_url = str(request.base_url).rstrip('/')
#                 api_prefix = ''
#                 api_base_url = f'{base_url}{api_prefix}'

#                 final_sess_number = session_data.session_number
#                 final_sess_date_str = session_data.date.isoformat()
#                 final_group_name = session_data.group_name

#                 hateoas_links = {
#                     "self": f'{api_base_url}/sessions/search/{final_sess_number}/{final_sess_date_str}/{final_group_name}',
#                     "update": f'{api_base_url}/sessions/update/{final_sess_number}/{final_sess_date_str}/{final_group_name}',
#                     "delete": f'{api_base_url}/sessions/delete/{final_sess_number}/{final_sess_date_str}/{final_group_name}',
#                     "sessions": f'{api_base_url}/sessions',
#                     "group": f'{api_base_url}/groups/search/by_group-name/{final_group_name}',
#                     "subject": f'{api_base_url}/subjects/search/{session_data.subject_code}' if session_data.subject_code else None,
#                     "teacher": f'{api_base_url}/teachers/search/{session_data.teacher_id}' if session_data.teacher_id else None,
#                     "cabinet": f'{api_base_url}/cabinets/search/{session_data.building_number}/{session_data.cabinet_number}' if session_data.cabinet_number is not None and session_data.building_number is not None else None
#                 }
#                 hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

#                 return ShowSessionWithHATEOAS(session=session_pydantic, links=hateoas_links)

#         except HTTPException:
#             await session.rollback()
#             raise
#         except Exception as e:
#             await session.rollback()
#             logger.error(
#                 f"Неожиданная ошибка при обновлении сессии {body.session_number} для группы {body.group_name} на дату {body.session_date}: {e}",
#                 exc_info=True
#             )
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="Внутренняя ошибка сервера при обновлении сессии."
#             )


# @session_router.post("/create", response_model=ShowSessionWithHATEOAS, status_code=status.HTTP_201_CREATED)
# async def create_session(body: CreateSession, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _create_new_session(body, request, db)

# @session_router.get("/search/{session_number}/{date}/{group_name}", response_model=ShowSessionWithHATEOAS,
#                     responses={404: {"description": "Сессия не найдена"}})
# async def get_session(session_number: int, date: date, group_name: str, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _get_session(session_number, date, group_name, request, db)

# @session_router.get("/search", response_model=ShowSessionListWithHATEOAS,
#                     responses={404: {"description": "Сессии не найдены"}})
# async def get_all_sessions(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
#     return await _get_all_sessions(query_param.page, query_param.limit, request, db)

# @session_router.get("/search/by_date/{date}", response_model=ShowSessionListWithHATEOAS,
#                     responses={404: {"description": "Сессии не найдены"}})
# async def get_all_sessions_by_date(date: date, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
#     return await _get_all_sessions_by_date(date, query_param.page, query_param.limit, request, db)

# @session_router.get("/search/by_teacher/{teacher_id}", response_model=ShowSessionListWithHATEOAS,
#                     responses={404: {"description": "Сессии не найдены"}})
# async def get_all_sessions_by_teacher(teacher_id: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
#     return await _get_all_sessions_by_teacher(teacher_id, query_param.page, query_param.limit, request, db)

# @session_router.get("/search/by_group/{group_name}", response_model=ShowSessionListWithHATEOAS,
#                     responses={404: {"description": "Сессии не найдены"}})
# async def get_all_sessions_by_group(group_name: str, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
#     return await _get_all_sessions_by_group(group_name, query_param.page, query_param.limit, request, db)

# @session_router.get("/search/by_subject/{subject_code}", response_model=ShowSessionListWithHATEOAS,
#                     responses={404: {"description": "Сессии не найдены"}})
# async def get_all_sessions_by_subject(subject_code: str, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
#     return await _get_all_sessions_by_subject(subject_code, query_param.page, query_param.limit, request, db)

# @session_router.delete("/delete/{session_number}/{date}/{group_name}", response_model=ShowSessionWithHATEOAS,
#                     responses={404: {"description": "Сессия не найдена"}})
# async def delete_session(session_number: int, date: date, group_name: str, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _delete_session(session_number, date, group_name, request, db)

# @session_router.put("/update", response_model=ShowSessionWithHATEOAS,
#                     responses={404: {"description": "Сессия не найдена"}})
# async def update_session(body: UpdateSession, request: Request, db: AsyncSession = Depends(get_db)):
#     return await _update_session(body, request, db)






category_router = APIRouter()

'''
==============================
CRUD operations for TeacherCategory
==============================
'''

async def _create_new_category(body: CreateTeacherCategory, request: Request, db) -> ShowTeacherCategoryWithHATEOAS:
    async with db as session:
        async with session.begin():
            category_dal = TeacherCategoryDAL(session)
            try:
                if not await ensure_category_unique(category_dal, body.teacher_category):
                    raise HTTPException(status_code=400, detail=f"Категория преподавателя '{body.teacher_category}' уже существует")

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
                logger.error(f"Неожиданная ошибка при создании категории преподавателя '{body.teacher_category}': {e}", exc_info=True)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка сервера при создании категории преподавателя.")


async def _get_category(teacher_category: str, request: Request, db) -> ShowTeacherCategoryWithHATEOAS:
    async with db as session:
        async with session.begin():
            category_dal = TeacherCategoryDAL(session)
            try:
                category_orm = await category_dal.get_teacher_category(teacher_category)
                if not category_orm:
                    raise HTTPException(status_code=404, detail=f"Категория преподавателя '{teacher_category}' не найдена")

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
                logger.error(f"Неожиданная ошибка при получении категории преподавателя '{teacher_category}': {e}", exc_info=True)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка сервера при получении категории преподавателя.")


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
                    category_with_links = ShowTeacherCategoryWithHATEOAS(category=category_pydantic, links=category_links)
                    categories_with_hateoas.append(category_with_links)

                collection_links = {
                    "self": f'{api_base_url}/categories/search?page={page}&limit={limit}',
                    "create": f'{api_base_url}/categories/create',
                }

                return ShowTeacherCategoryListWithHATEOAS(categories=categories_with_hateoas, links=collection_links)

            except Exception as e:
                logger.error(f"Неожиданная ошибка при получении списка категорий преподавателей (page={page}, limit={limit}): {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при получении списка категорий преподавателей.")


async def _delete_category(teacher_category: str, request: Request, db) -> ShowTeacherCategoryWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                category_dal = TeacherCategoryDAL(session)
                deleted_category_orm = await category_dal.delete_teacher_category(teacher_category)
                if not deleted_category_orm:
                    raise HTTPException(status_code=404, detail=f"Категория преподавателя '{teacher_category}' не найдена для удаления")

                deleted_category_pydantic = ShowTeacherCategory.model_validate(deleted_category_orm, from_attributes=True)

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
            logger.error(f"Неожиданная ошибка при удалении категории преподавателя '{teacher_category}': {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка сервера при удалении категории преподавателя.")


async def _update_category(body: UpdateTeacherCategory, request: Request, db) -> ShowTeacherCategoryWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["teacher_category", "new_teacher_category"]}

                target_category = body.teacher_category
                if body.new_teacher_category is not None:
                    update_data["teacher_category"] = body.new_teacher_category
                    category_dal = TeacherCategoryDAL(session)
                    if target_category != body.new_teacher_category and not await ensure_category_unique(category_dal, body.new_teacher_category):
                        raise HTTPException(status_code=400, detail=f"Категория преподавателя '{body.new_teacher_category}' уже существует")

                category_dal = TeacherCategoryDAL(session)
                updated_category_orm = await category_dal.update_teacher_category(target_category, **update_data)
                if not updated_category_orm:
                    raise HTTPException(status_code=404, detail=f"Категория преподавателя '{target_category}' не найдена для обновления")

                updated_category_pydantic = ShowTeacherCategory.model_validate(updated_category_orm, from_attributes=True)

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
            logger.error(f"Неожиданная ошибка при обновлении категории преподавателя '{body.teacher_category}': {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка сервера при обновлении категории преподавателя.")



@category_router.post("/create", response_model=ShowTeacherCategoryWithHATEOAS, status_code=status.HTTP_201_CREATED)
async def create_category(body: CreateTeacherCategory, request: Request, db: AsyncSession = Depends(get_db)):
    return await _create_new_category(body, request, db)


@category_router.get("/search/{teacher_category}", response_model=ShowTeacherCategoryWithHATEOAS, responses={404: {"description": "Категория преподавателя не найдена"}})
async def get_category(teacher_category: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_category(teacher_category, request, db)


@category_router.get("/search", response_model=ShowTeacherCategoryListWithHATEOAS, responses={404: {"description": "Категории преподавателей не найдены"}})
async def get_all_categories(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_all_categories(query_param.page, query_param.limit, request, db)


@category_router.delete("/delete/{teacher_category}", response_model=ShowTeacherCategoryWithHATEOAS, responses={404: {"description": "Категория преподавателя не найдена"}})
async def delete_category(teacher_category: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await _delete_category(teacher_category, request, db)


@category_router.put("/update", response_model=ShowTeacherCategoryWithHATEOAS, responses={404: {"description": "Категория преподавателя не найдена"}})
async def update_category(body: UpdateTeacherCategory, request: Request, db: AsyncSession = Depends(get_db)):
    return await _update_category(body, request, db)
