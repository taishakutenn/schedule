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
from api.services_helpers import ensure_category_exists, ensure_category_unique, ensure_certification_exists, ensure_group_exists, ensure_group_unique, ensure_session_exists, ensure_session_unique, ensure_stream_unique, ensure_teacher_building_exists, ensure_teacher_email_unique, ensure_teacher_exists, ensure_teacher_phone_unique, \
    ensure_building_exists, ensure_building_unique, ensure_cabinet_exists, ensure_cabinet_unique, ensure_session_type_exists, ensure_session_type_unique, \
    ensure_semester_exists, ensure_semester_unique, ensure_plan_exists, ensure_plan_unique, ensure_speciality_exists, ensure_speciality_unique, \
    ensure_chapter_exists, ensure_chapter_unique, ensure_cycle_exists, ensure_cycle_unique, ensure_module_exists, ensure_module_unique, ensure_cycle_contains_modules, \
    ensure_subject_in_cycle_exists, ensure_subject_in_cycle_unique, ensure_subject_in_cycle_hours_exists, ensure_subject_in_cycle_hours_unique, \
    ensure_teacher_in_plan_unique, ensure_teacher_in_plan_exists
    
from db.dals import CertificationDAL, GroupDAL, SessionDAL, StreamDAL, SubjectsInCycleHoursDAL, TeacherBuildingDAL, TeacherCategoryDAL, TeacherDAL, BuildingDAL, CabinetDAL, SessionTypeDAL, SemesterDAL, PlanDAL, SpecialityDAL, ChapterDAL, CycleDAL, ModuleDAL, SubjectsInCycleDAL, TeacherInPlanDAL
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


'''
==============================
CRUD operations for Building
==============================
'''

async def _create_new_building(body: CreateBuilding, request: Request, db) -> ShowBuildingWithHATEOAS:
    async with db as session:
        async with session.begin():
            building_dal = BuildingDAL(session)
            try:
                if not await ensure_building_unique(building_dal, body.building_number):
                    raise HTTPException(status_code=400, detail=f"Здание с номером {body.building_number} уже существует")

                building = await building_dal.create_building(
                    building_number=body.building_number,
                    city=body.city,
                    building_address=body.building_address
                )
                building_number = building.building_number
                building_pydantic = ShowBuilding.model_validate(building, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/buildings/search/by_number/{building_number}',
                    "update": f'{api_base_url}/buildings/update',
                    "delete": f'{api_base_url}/buildings/delete/{building_number}',
                    "buildings": f'{api_base_url}/buildings',
                    "cabinets": f'{api_base_url}/cabinets/search/by_building/{building_number}'
                }

                return ShowBuildingWithHATEOAS(building=building_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при создании здания: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_building_by_number(building_number, request: Request, db) -> ShowBuildingWithHATEOAS:
    async with db as session:
        async with session.begin():
            building_dal = BuildingDAL(session)
            try:
                building = await building_dal.get_building_by_number(building_number)
                if not building:
                    raise HTTPException(status_code=404, detail=f"Здание с номером: {building_number} не найдено")
                building_pydantic = ShowBuilding.model_validate(building, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/buildings/search/by_number/{building_number}',
                    "update": f'{api_base_url}/buildings/update',
                    "delete": f'{api_base_url}/buildings/delete/{building_number}',
                    "buildings": f'{api_base_url}/buildings',
                    "cabinets": f'{api_base_url}/cabinets/search/by_building/{building_number}'
                }

                return ShowBuildingWithHATEOAS(building=building_pydantic, links=hateoas_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Получение здания отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_building_by_address(address, request: Request, db) -> ShowBuildingWithHATEOAS:
    async with db as session:
        async with session.begin():
            building_dal = BuildingDAL(session)
            try:
                building = await building_dal.get_building_by_address(address)
                if not building:
                    raise HTTPException(status_code=404, detail=f"Здание по адресу: {address} не найдено")
                building_number = building.building_number
                building_pydantic = ShowBuilding.model_validate(building, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/buildings/search/by_number/{building_number}',
                    "update": f'{api_base_url}/buildings/update',
                    "delete": f'{api_base_url}/buildings/delete/{building_number}',
                    "buildings": f'{api_base_url}/buildings',
                    "cabinets": f'{api_base_url}/cabinets/search/by_building/{building_number}'
                }

                return ShowBuildingWithHATEOAS(building=building_pydantic, links=hateoas_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Получение здания отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_all_buildings(page: int, limit: int, request: Request, db) -> ShowBuildingListWithHATEOAS:
    async with db as session:
        async with session.begin():
            building_dal = BuildingDAL(session)
            try:
                buildings = await building_dal.get_all_buildings(page, limit)
                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                buildings_with_hateoas = []
                for building in buildings:
                    building_pydantic = ShowBuilding.model_validate(building, from_attributes=True)
                    building_number = building.building_number
                    building_links = {
                        "self": f'{api_base_url}/buildings/search/by_number/{building_number}',
                        "update": f'{api_base_url}/buildings/update',
                        "delete": f'{api_base_url}/buildings/delete/{building_number}',
                        "buildings": f'{api_base_url}/buildings',
                        "cabinets": f'{api_base_url}/cabinets/search/by_building/{building_number}'
                    }
                    building_with_links = ShowBuildingWithHATEOAS(building=building_pydantic, links=building_links)
                    buildings_with_hateoas.append(building_with_links)

                collection_links = {
                    "self": f'{api_base_url}/buildings/search?page={page}&limit={limit}',
                    "create": f'{api_base_url}/buildings/create'
                }
                collection_links = {k: v for k, v in collection_links.items() if v is not None}

                return ShowBuildingListWithHATEOAS(buildings=buildings_with_hateoas, links=collection_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Получение зданий отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _delete_building(building_number: int, request: Request, db) -> ShowBuildingWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                building_dal = BuildingDAL(session)
                if not await ensure_building_exists(building_dal, building_number):
                    raise HTTPException(status_code=404, detail=f"Здание с номером: {building_number} не найдено")

                building = await building_dal.delete_building(building_number)
                if not building:
                    raise HTTPException(status_code=404, detail=f"Здание с номером: {building_number} не найдено")

                building_pydantic = ShowBuilding.model_validate(building, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "buildings": f'{api_base_url}/buildings',
                    "create": f'{api_base_url}/buildings/create',
                    "cabinets": f'{api_base_url}/cabinets/search/by_building/{building_number}'
                }
                hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                return ShowBuildingWithHATEOAS(building=building_pydantic, links=hateoas_links)

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Неожиданная ошибка при удалении здания {building_number}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении здания.")


async def _update_building(body: UpdateBuilding, request: Request, db) -> ShowBuildingWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["building_number", "new_building_number"]}
                if body.new_building_number is not None:
                    update_data["building_number"] = body.new_building_number
                    building_dal = BuildingDAL(session)
                    if not await ensure_building_unique(building_dal, body.new_building_number):
                        raise HTTPException(status_code=400, detail=f"Здание с номером {body.new_building_number} уже существует")

                building_dal = BuildingDAL(session)
                if not await ensure_building_exists(building_dal, body.building_number):
                    raise HTTPException(status_code=404, detail=f"Здание с номером: {body.building_number} не найдено")

                building = await building_dal.update_building(target_number=body.building_number, **update_data)
                if not building:
                    raise HTTPException(status_code=404, detail=f"Здание с номером: {body.building_number} не найдено")

                building_number = building.building_number 
                building_pydantic = ShowBuilding.model_validate(building, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/buildings/search/by_number/{building_number}',
                    "update": f'{api_base_url}/buildings/update',
                    "delete": f'{api_base_url}/buildings/delete/{building_number}',
                    "buildings": f'{api_base_url}/buildings',
                    "cabinets": f'{api_base_url}/cabinets/search/by_building/{building_number}'
                }

                return ShowBuildingWithHATEOAS(building=building_pydantic, links=hateoas_links)

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.warning(f"Изменение данных о здании отменено (Ошибка: {e})")
            raise e


@building_router.post("/create", response_model=ShowBuildingWithHATEOAS, status_code=201)
async def create_building(body: CreateBuilding, request: Request, db: AsyncSession = Depends(get_db)):
    return await _create_new_building(body, request, db)


@building_router.get("/search/by_number/{building_number}", response_model=ShowBuildingWithHATEOAS, responses={404: {"description": "Здание не найдено"}})
async def get_building_by_number(building_number: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_building_by_number(building_number, request, db)


@building_router.get("/search/by_address/{building_address}", response_model=ShowBuildingWithHATEOAS, responses={404: {"description": "Здание не найдено"}})
async def get_building_by_address(address: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_building_by_address(address, request, db)


@building_router.get("/search", response_model=ShowBuildingListWithHATEOAS)
async def get_all_buildings(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_all_buildings(query_param.page, query_param.limit, request, db)


@building_router.delete("/delete/{building_number}", response_model=ShowBuildingWithHATEOAS, responses={404: {"description": "Здание не найдено"}})
async def delete_building(building_number: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _delete_building(building_number, request, db)


@building_router.put("/update", response_model=ShowBuildingWithHATEOAS, responses={404: {"description": "Здание не найдено"}})
async def update_building(body: UpdateBuilding, request: Request, db: AsyncSession = Depends(get_db)):
    return await _update_building(body, request, db)


'''
===========================
CRUD operations for Cabinet
===========================
'''

async def _create_new_cabinet(body: CreateCabinet, request: Request, db) -> ShowCabinetWithHATEOAS:
    async with db as session:
        async with session.begin():
            building_dal = BuildingDAL(session)
            cabinet_dal = CabinetDAL(session)
            try:
                # Check that the building exists
                if not await ensure_building_exists(building_dal, body.building_number):
                    raise HTTPException(status_code=404,
                                        detail=f"Здание с номером {body.building_number} не найдено")
                # Check that the cabinet is unique
                if not await ensure_cabinet_unique(cabinet_dal, body.building_number, body.cabinet_number):
                    raise HTTPException(status_code=400,
                                        detail=f"Кабинет с номером {body.cabinet_number} в здании {body.building_number} уже существует")

                cabinet = await cabinet_dal.create_cabinet(
                    cabinet_number=body.cabinet_number,
                    building_number=body.building_number,
                    capacity=body.capacity,
                    cabinet_state=body.cabinet_state
                )
                cabinet_number = cabinet.cabinet_number
                building_number = cabinet.building_number
                cabinet_pydantic = ShowCabinet.model_validate(cabinet, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/cabinets/search/by_building_and_number/{building_number}/{cabinet_number}',
                    "update": f'{api_base_url}/cabinets/update',
                    "delete": f'{api_base_url}/cabinets/delete/{building_number}/{cabinet_number}',
                    "cabinets": f'{api_base_url}/cabinets',
                    "building": f'{api_base_url}/buildings/search/by_number/{building_number}',
                    "sessions": f'{api_base_url}/sessions/search/by_cabinet/{building_number}/{cabinet_number}'
                }

                return ShowCabinetWithHATEOAS(cabinet=cabinet_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при создании кабинета: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_cabinet_by_number_and_building(building_number: int, cabinet_number: int, request: Request, db) -> ShowCabinetWithHATEOAS:
    async with db as session:
        async with session.begin():
            cabinet_dal = CabinetDAL(session)
            try:
                cabinet = await cabinet_dal.get_cabinet_by_number_and_building(building_number, cabinet_number)
                if not cabinet:
                    raise HTTPException(status_code=404, detail=f"Кабинет с номером {cabinet_number} в здании {building_number} не найден")
                cabinet_pydantic = ShowCabinet.model_validate(cabinet, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/cabinets/search/by_building_and_number/{building_number}/{cabinet_number}',
                    "update": f'{api_base_url}/cabinets/update',
                    "delete": f'{api_base_url}/cabinets/delete/{building_number}/{cabinet_number}',
                    "cabinets": f'{api_base_url}/cabinets',
                    "building": f'{api_base_url}/buildings/search/by_number/{building_number}',
                    "sessions": f'{api_base_url}/sessions/search/by_cabinet/{building_number}/{cabinet_number}'
                }

                return ShowCabinetWithHATEOAS(cabinet=cabinet_pydantic, links=hateoas_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Получение кабинета отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_all_cabinets(page: int, limit: int, request: Request, db) -> ShowCabinetListWithHATEOAS:
    async with db as session:
        async with session.begin():
            cabinet_dal = CabinetDAL(session)
            try:
                cabinets = await cabinet_dal.get_all_cabinets(page, limit)
                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                cabinets_with_hateoas = []
                for cabinet in cabinets:
                    cabinet_pydantic = ShowCabinet.model_validate(cabinet, from_attributes=True)
                    cabinet_number = cabinet.cabinet_number
                    building_number = cabinet.building_number
                    cabinet_links = {
                        "self": f'{api_base_url}/cabinets/search/by_building_and_number/{building_number}/{cabinet_number}',
                        "update": f'{api_base_url}/cabinets/update',
                        "delete": f'{api_base_url}/cabinets/delete/{building_number}/{cabinet_number}',
                        "cabinets": f'{api_base_url}/cabinets',
                        "building": f'{api_base_url}/buildings/search/by_number/{building_number}',
                        "sessions": f'{api_base_url}/sessions/search/by_cabinet/{building_number}/{cabinet_number}'
                    }
                    cabinet_with_links = ShowCabinetWithHATEOAS(cabinet=cabinet_pydantic, links=cabinet_links)
                    cabinets_with_hateoas.append(cabinet_with_links)

                collection_links = {
                    "self": f'{api_base_url}/cabinets/search?page={page}&limit={limit}',
                    "create": f'{api_base_url}/cabinets/create'
                }
                collection_links = {k: v for k, v in collection_links.items() if v is not None}

                return ShowCabinetListWithHATEOAS(cabinets=cabinets_with_hateoas, links=collection_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Получение кабинетов отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_cabinets_by_building(building_number: int, page: int, limit: int, request: Request, db) -> ShowCabinetListWithHATEOAS:
    async with db as session:
        async with session.begin():
            building_dal = BuildingDAL(session)
            cabinet_dal = CabinetDAL(session)
            try:
                # Check that the building exists
                if not await ensure_building_exists(building_dal, building_number):
                    raise HTTPException(status_code=404,
                                        detail=f"Здание с номером {building_number} не найдено")

                cabinets = await cabinet_dal.get_cabinets_by_building(building_number, page, limit)
                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                cabinets_with_hateoas = []
                for cabinet in cabinets:
                    cabinet_pydantic = ShowCabinet.model_validate(cabinet, from_attributes=True)
                    cabinet_number = cabinet.cabinet_number
                    cabinet_links = {
                        "self": f'{api_base_url}/cabinets/search/by_building_and_number/{building_number}/{cabinet_number}',
                        "update": f'{api_base_url}/cabinets/update',
                        "delete": f'{api_base_url}/cabinets/delete/{building_number}/{cabinet_number}',
                        "cabinets": f'{api_base_url}/cabinets',
                        "building": f'{api_base_url}/buildings/search/by_number/{building_number}',
                        "sessions": f'{api_base_url}/sessions/search/by_cabinet/{building_number}/{cabinet_number}'
                    }
                    cabinet_with_links = ShowCabinetWithHATEOAS(cabinet=cabinet_pydantic, links=cabinet_links)
                    cabinets_with_hateoas.append(cabinet_with_links)

                collection_links = {
                    "self": f'{api_base_url}/cabinets/search/by_building/{building_number}?page={page}&limit={limit}',
                    "create": f'{api_base_url}/cabinets/create',
                    "building": f'{api_base_url}/buildings/search/by_number/{building_number}'
                }
                collection_links = {k: v for k, v in collection_links.items() if v is not None}

                return ShowCabinetListWithHATEOAS(cabinets=cabinets_with_hateoas, links=collection_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Получение кабинетов отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _delete_cabinet(building_number: int, cabinet_number: int, request: Request, db) -> ShowCabinetWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                cabinet_dal = CabinetDAL(session)
                cabinet = await cabinet_dal.delete_cabinet(building_number, cabinet_number)
                if not cabinet:
                    raise HTTPException(status_code=404, detail=f"Кабинет с номером: {cabinet_number} в здании {building_number} не может быть удалён, т.к. не найден")

                cabinet_pydantic = ShowCabinet.model_validate(cabinet, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "cabinets": f'{api_base_url}/cabinets',
                    "create": f'{api_base_url}/cabinets/create',
                    "building": f'{api_base_url}/buildings/search/by_number/{building_number}'
                }
                hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                return ShowCabinetWithHATEOAS(cabinet=cabinet_pydantic, links=hateoas_links)

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Неожиданная ошибка при удалении кабинета {cabinet_number} в здании {building_number}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении кабинета.")


async def _update_cabinet(body: UpdateCabinet, request: Request, db) -> ShowCabinetWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                # exclusion of None-fields from the transmitted data
                update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["building_number", "cabinet_number"]}
                # Rename fields new_building_number and new_cabinet_number to building_number and cabinet_number
                if "new_building_number" in update_data:
                    update_data["building_number"] = update_data.pop("new_building_number")
                if "new_cabinet_number" in update_data:
                    update_data["cabinet_number"] = update_data.pop("new_cabinet_number")

                # change data
                cabinet_dal = CabinetDAL(session)
                building_dal = BuildingDAL(session)

                # Проверяем, существует ли кабинет, который мы хотим обновить
                if not await ensure_cabinet_exists(cabinet_dal, body.building_number, body.cabinet_number):
                    raise HTTPException(status_code=404, detail=f"Кабинет с номером: {body.cabinet_number} в здании: {body.building_number} не найден")

                # Если обновляем building_number или cabinet_number, проверяем уникальность
                target_building_number = body.building_number
                target_cabinet_number = body.cabinet_number
                if "building_number" in update_data or "cabinet_number" in update_data:
                    new_building_number = update_data.get("building_number", target_building_number)
                    new_cabinet_number = update_data.get("cabinet_number", target_cabinet_number)
                    # Проверяем, не конфликтует ли новая пара (building_number, cabinet_number) с существующей
                    if not await ensure_cabinet_unique(cabinet_dal, new_building_number, new_cabinet_number):
                        raise HTTPException(status_code=400, detail=f"Кабинет с номером {new_cabinet_number} в здании {new_building_number} уже существует")
                    # Проверяем, существует ли целевое здание, если оно меняется
                    if "building_number" in update_data and not await ensure_building_exists(building_dal, new_building_number):
                        raise HTTPException(status_code=404, detail=f"Здание с номером {new_building_number} не найдено")

                cabinet = await cabinet_dal.update_cabinet(
                    search_building_number=body.building_number,
                    search_cabinet_number=body.cabinet_number,
                    **update_data
                )
                if not cabinet:
                    raise HTTPException(status_code=404, detail="Кабинет не был обновлён")

                cabinet_number = cabinet.cabinet_number
                building_number = cabinet.building_number
                cabinet_pydantic = ShowCabinet.model_validate(cabinet, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/cabinets/search/by_building_and_number/{building_number}/{cabinet_number}',
                    "update": f'{api_base_url}/cabinets/update',
                    "delete": f'{api_base_url}/cabinets/delete/{building_number}/{cabinet_number}',
                    "cabinets": f'{api_base_url}/cabinets',
                    "building": f'{api_base_url}/buildings/search/by_number/{building_number}',
                    "sessions": f'{api_base_url}/sessions/search/by_cabinet/{building_number}/{cabinet_number}'
                }

                return ShowCabinetWithHATEOAS(cabinet=cabinet_pydantic, links=hateoas_links)

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.warning(f"Изменение данных о кабинете отменено (Ошибка: {e})")
            raise e


@cabinet_router.post("/create", response_model=ShowCabinetWithHATEOAS, status_code=201)
async def create_cabinet(body: CreateCabinet, request: Request, db: AsyncSession = Depends(get_db)):
    return await _create_new_cabinet(body, request, db)


@cabinet_router.get("/search/by_building_and_number/{building_number}/{cabinet_number}", response_model=ShowCabinetWithHATEOAS, responses={404: {"description": "Кабинет не найден"}})
async def get_cabinet_by_number_and_building(building_number: int, cabinet_number: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_cabinet_by_number_and_building(building_number, cabinet_number, request, db)


@cabinet_router.get("/search", response_model=ShowCabinetListWithHATEOAS)
async def get_all_cabinets(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_all_cabinets(query_param.page, query_param.limit, request, db)


@cabinet_router.get("/search/by_building/{building_number}", response_model=ShowCabinetListWithHATEOAS, responses={404: {"description": "Кабинеты не найдены"}})
async def get_cabinets_by_building(building_number: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_cabinets_by_building(building_number, query_param.page, query_param.limit, request, db)


@cabinet_router.delete("/delete/{building_number}/{cabinet_number}", response_model=ShowCabinetWithHATEOAS, responses={404: {"description": "Кабинет не найден"}})
async def delete_cabinet(building_number: int, cabinet_number: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _delete_cabinet(building_number, cabinet_number, request, db)


@cabinet_router.put("/update", response_model=ShowCabinetWithHATEOAS, responses={404: {"description": "Кабинет не найден"}})
async def update_cabinet(body: UpdateCabinet, request: Request, db: AsyncSession = Depends(get_db)):
    return await _update_cabinet(body, request, db)


'''
==============================
CRUD operations for Speciality
==============================
'''

async def _create_new_speciality(body: CreateSpeciality, request: Request, db) -> ShowSpecialityWithHATEOAS:
    async with db as session:
        async with session.begin():
            speciality_dal = SpecialityDAL(session)
            try:
                if not await ensure_speciality_unique(speciality_dal, body.speciality_code):
                    raise HTTPException(status_code=400, detail=f"Специальность с кодом '{body.speciality_code}' уже существует")

                speciality = await speciality_dal.create_speciality(
                    speciality_code=body.speciality_code
                )
                speciality_code = speciality.speciality_code
                speciality_pydantic = ShowSpeciality.model_validate(speciality, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/specialities/search/by_speciality_code/{speciality_code}',
                    "update": f'{api_base_url}/specialities/update',
                    "delete": f'{api_base_url}/specialities/delete/{speciality_code}',
                    "specialities": f'{api_base_url}/specialities',
                    "groups": f'{api_base_url}/groups/search/by_speciality/{speciality_code}',
                    "plans": f'{api_base_url}/plans/search/by_speciality/{speciality_code}'
                }

                return ShowSpecialityWithHATEOAS(speciality=speciality_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при создании специальности '{body.speciality_code}': {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_speciality_by_code(speciality_code: str, request: Request, db) -> ShowSpecialityWithHATEOAS:
    async with db as session:
        async with session.begin():
            speciality_dal = SpecialityDAL(session)
            try:
                speciality = await speciality_dal.get_speciality(speciality_code)
                if not speciality:
                    raise HTTPException(status_code=404, detail=f"Специальность с кодом '{speciality_code}' не найдена")
                speciality_pydantic = ShowSpeciality.model_validate(speciality, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/specialities/search/by_speciality_code/{speciality_code}',
                    "update": f'{api_base_url}/specialities/update',
                    "delete": f'{api_base_url}/specialities/delete/{speciality_code}',
                    "specialities": f'{api_base_url}/specialities',
                    "groups": f'{api_base_url}/groups/search/by_speciality/{speciality_code}',
                    "plans": f'{api_base_url}/plans/search/by_speciality/{speciality_code}'
                }

                return ShowSpecialityWithHATEOAS(speciality=speciality_pydantic, links=hateoas_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Получение специальности '{speciality_code}' отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_all_specialities(page: int, limit: int, request: Request, db) -> ShowSpecialityListWithHATEOAS:
    async with db as session:
        async with session.begin():
            speciality_dal = SpecialityDAL(session)
            try:
                specialities = await speciality_dal.get_all_specialities(page, limit)
                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                specialities_with_hateoas = []
                for speciality in specialities:
                    speciality_pydantic = ShowSpeciality.model_validate(speciality, from_attributes=True)
                    speciality_code = speciality.speciality_code
                    speciality_links = {
                        "self": f'{api_base_url}/specialities/search/by_speciality_code/{speciality_code}',
                        "update": f'{api_base_url}/specialities/update',
                        "delete": f'{api_base_url}/specialities/delete/{speciality_code}',
                        "specialities": f'{api_base_url}/specialities',
                        "groups": f'{api_base_url}/groups/search/by_speciality/{speciality_code}',
                        "plans": f'{api_base_url}/plans/search/by_speciality/{speciality_code}'
                    }
                    speciality_with_links = ShowSpecialityWithHATEOAS(speciality=speciality_pydantic, links=speciality_links)
                    specialities_with_hateoas.append(speciality_with_links)

                collection_links = {
                    "self": f'{api_base_url}/specialities/search?page={page}&limit={limit}',
                    "create": f'{api_base_url}/specialities/create'
                }
                collection_links = {k: v for k, v in collection_links.items() if v is not None}

                return ShowSpecialityListWithHATEOAS(specialities=specialities_with_hateoas, links=collection_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Получение специальностей отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _delete_speciality(speciality_code: str, request: Request, db) -> ShowSpecialityWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                speciality_dal = SpecialityDAL(session)
                
                if not await ensure_speciality_exists(speciality_dal, speciality_code):
                    raise HTTPException(status_code=404, detail=f"Специальность с кодом '{speciality_code}' не найдена")

                speciality = await speciality_dal.delete_speciality(speciality_code)
                
                if not speciality:
                    raise HTTPException(status_code=404, detail=f"Специальность с кодом '{speciality_code}' не найдена")

                speciality_pydantic = ShowSpeciality.model_validate(speciality, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "specialities": f'{api_base_url}/specialities',
                    "create": f'{api_base_url}/specialities/create'
                }
                hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                return ShowSpecialityWithHATEOAS(speciality=speciality_pydantic, links=hateoas_links)

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Неожиданная ошибка при удалении специальности '{speciality_code}': {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении специальности.")


async def _update_speciality(body: UpdateSpeciality, request: Request, db) -> ShowSpecialityWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["speciality_code", "new_speciality_code"]}
                
                if body.new_speciality_code is not None:
                    update_data["speciality_code"] = body.new_speciality_code
                    
                    speciality_dal = SpecialityDAL(session)
                    if not await ensure_speciality_unique(speciality_dal, body.new_speciality_code):
                        raise HTTPException(status_code=400, detail=f"Специальность с кодом '{body.new_speciality_code}' уже существует")

                speciality_dal = SpecialityDAL(session)
                
                if not await ensure_speciality_exists(speciality_dal, body.speciality_code):
                    raise HTTPException(status_code=404, detail=f"Специальность с кодом '{body.speciality_code}' не найдена")

                speciality = await speciality_dal.update_speciality(target_code=body.speciality_code, **update_data)
                if not speciality:
                    raise HTTPException(status_code=404, detail=f"Специальность с кодом '{body.speciality_code}' не найдена")

                speciality_code = speciality.speciality_code 
                speciality_pydantic = ShowSpeciality.model_validate(speciality, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/specialities/search/by_speciality_code/{speciality_code}',
                    "update": f'{api_base_url}/specialities/update',
                    "delete": f'{api_base_url}/specialities/delete/{speciality_code}',
                    "specialities": f'{api_base_url}/specialities',
                    "groups": f'{api_base_url}/groups/search/by_speciality/{speciality_code}',
                    "plans": f'{api_base_url}/plans/search/by_speciality/{speciality_code}'
                }

                return ShowSpecialityWithHATEOAS(speciality=speciality_pydantic, links=hateoas_links)

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.warning(f"Изменение данных о специальности отменено (Ошибка: {e})")
            raise e


@speciality_router.post("/create", response_model=ShowSpecialityWithHATEOAS, status_code=201)
async def create_speciality(body: CreateSpeciality, request: Request, db: AsyncSession = Depends(get_db)):
    return await _create_new_speciality(body, request, db)


@speciality_router.get("/search/by_speciality_code/{speciality_code}", response_model=ShowSpecialityWithHATEOAS, responses={404: {"description": "Специальность не найдена"}})
async def get_speciality_by_code(speciality_code: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_speciality_by_code(speciality_code, request, db)


@speciality_router.get("/search", response_model=ShowSpecialityListWithHATEOAS)
async def get_all_specialities(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_all_specialities(query_param.page, query_param.limit, request, db)


@speciality_router.delete("/delete/{speciality_code}", response_model=ShowSpecialityWithHATEOAS, responses={404: {"description": "Специальность не найдена"}})
async def delete_speciality(speciality_code: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await _delete_speciality(speciality_code, request, db)


@speciality_router.put("/update", response_model=ShowSpecialityWithHATEOAS, responses={404: {"description": "Специальность не найдена"}})
async def update_speciality(body: UpdateSpeciality, request: Request, db: AsyncSession = Depends(get_db)):
    return await _update_speciality(body, request, db)


'''
==============================
CRUD operations for Group
==============================
'''

async def _create_new_group(body: CreateGroup, request: Request, db) -> ShowGroupWithHATEOAS:
    async with db as session:
        async with session.begin():
            group_dal = GroupDAL(session)
            teacher_dal = TeacherDAL(session)
            speciality_dal = SpecialityDAL(session)
            try:
                if body.speciality_code is not None and not await ensure_speciality_exists(speciality_dal, body.speciality_code):
                    raise HTTPException(status_code=404, detail=f"Специальность с кодом {body.speciality_code} не найдена")
                
                if body.group_advisor_id is not None and not await ensure_teacher_exists(teacher_dal, body.group_advisor_id):
                    raise HTTPException(status_code=404, detail=f"Преподаватель с id {body.group_advisor_id} не найден")
                
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


async def _get_group_by_name(group_name: str, request: Request, db) -> ShowGroupWithHATEOAS:
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


async def _get_group_by_advisor(advisor_id: int, request: Request, db) -> ShowGroupWithHATEOAS:
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


async def _get_all_groups(page: int, limit: int, request: Request, db) -> ShowGroupListWithHATEOAS:
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


async def _get_groups_by_speciality(speciality_code: str, page: int, limit: int, request: Request, db) -> ShowGroupListWithHATEOAS:
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


async def _delete_group(group_name: str, request: Request, db) -> ShowGroupWithHATEOAS:
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


async def _update_group(body: UpdateGroup, request: Request, db) -> ShowGroupWithHATEOAS:
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

                if not await ensure_group_exists(group_dal, body.group_name):
                    raise HTTPException(status_code=404, detail=f"Группа {body.group_name} не найдена")

                if "group_advisor_id" in update_data and update_data["group_advisor_id"] is not None:
                    if not await ensure_teacher_exists(teacher_dal, update_data["group_advisor_id"]):
                        raise HTTPException(status_code=404, detail=f"Преподаватель с id {update_data['group_advisor_id']} не найден")
                if "speciality_code" in update_data and update_data["speciality_code"] is not None:
                    if not await ensure_speciality_exists(speciality_dal, update_data["speciality_code"]):
                        raise HTTPException(status_code=404, detail=f"Специальность с кодом {update_data['speciality_code']} не найдена")

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


@group_router.post("/create", response_model=ShowGroupWithHATEOAS, status_code=201)
async def create_group(body: CreateGroup, request: Request, db: AsyncSession = Depends(get_db)):
    return await _create_new_group(body, request, db)


@group_router.get("/search/by_group_name/{group_name}", response_model=ShowGroupWithHATEOAS, responses={404: {"description": "Группа не найдена"}})
async def get_group_by_name(group_name: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_group_by_name(group_name, request, db)


@group_router.get("/search/by_advisor/{advisor_id}", response_model=ShowGroupWithHATEOAS, responses={404: {"description": "Группа не найдена"}})
async def get_group_by_advisor(advisor_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_group_by_advisor(advisor_id, request, db)


@group_router.get("/search", response_model=ShowGroupListWithHATEOAS)
async def get_all_groups(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_all_groups(query_param.page, query_param.limit, request, db)


@group_router.get("/search/by_speciality/{speciality_code}", response_model=ShowGroupListWithHATEOAS, responses={404: {"description": "Группы не найдены"}})
async def get_groups_by_speciality(speciality_code: str, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_groups_by_speciality(speciality_code, query_param.page, query_param.limit, request, db)


@group_router.delete("/delete/{group_name}", response_model=ShowGroupWithHATEOAS, responses={404: {"description": "Группа не найдена"}})
async def delete_group(group_name: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await _delete_group(group_name, request, db)


@group_router.put("/update", response_model=ShowGroupWithHATEOAS, responses={404: {"description": "Группа не найдена"}})
async def update_group(body: UpdateGroup, request: Request, db: AsyncSession = Depends(get_db)):
    return await _update_group(body, request, db)


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



'''
==============================
CRUD operations for Session
==============================
'''

async def _create_new_session(body: CreateSession, request: Request, db) -> ShowSessionWithHATEOAS:
    async with db as session:
        async with session.begin():
            session_dal = SessionDAL(session)
            teacher_in_plan_dal = TeacherInPlanDAL(session)
            session_type_dal = SessionTypeDAL(session)
            cabinet_dal = CabinetDAL(session)
            try:
                if not await ensure_teacher_in_plan_exists(teacher_in_plan_dal, body.teacher_in_plan):
                    raise HTTPException(status_code=404, detail=f"Запись в расписании преподавателя с id {body.teacher_in_plan} не найдена")
                if not await ensure_session_type_exists(session_type_dal, body.session_type):
                    raise HTTPException(status_code=404, detail=f"Тип занятия {body.session_type} не найден")
                
                if body.cabinet_number is not None and body.building_number is not None:
                    cabinet_exists = await cabinet_dal.get_cabinet_by_number_and_building(body.building_number, body.cabinet_number)
                    if not cabinet_exists:
                        raise HTTPException(status_code=404, detail=f"Кабинет {body.cabinet_number} в здании {body.building_number} не найден")

                existing_session = await session_dal.get_session_by_composite_key(body.session_number, body.session_date, body.teacher_in_plan)
                if existing_session:
                    raise HTTPException(status_code=400, detail=f"Занятие с номером {body.session_number}, датой {body.session_date} и записью в расписании преподавателя {body.teacher_in_plan} уже существует")

                session_obj = await session_dal.create_session(
                    session_number=body.session_number,
                    session_date=body.session_date,
                    teacher_in_plan=body.teacher_in_plan,
                    session_type=body.session_type,
                    cabinet_number=body.cabinet_number,
                    building_number=body.building_number
                )
                session_number = session_obj.session_number
                session_date = session_obj.date 
                teacher_in_plan_id = session_obj.teacher_in_plan
                
                session_dict = {
                    "session_number": session_obj.session_number,
                    "session_date": session_obj.date,
                    "teacher_in_plan": session_obj.teacher_in_plan,
                    "session_type": session_obj.session_type,
                    "cabinet_number": session_obj.cabinet_number,
                    "building_number": session_obj.building_number,
                }
                session_pydantic = ShowSession.model_validate(session_dict)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/sessions/search/by_composite_key/{session_number}/{session_date}/{teacher_in_plan_id}',
                    "update": f'{api_base_url}/sessions/update',
                    "delete": f'{api_base_url}/sessions/delete/{session_number}/{session_date}/{teacher_in_plan_id}',
                    "sessions": f'{api_base_url}/sessions',
                    "plan": f'{api_base_url}/teachers_in_plans/search/by_id/{body.teacher_in_plan}',
                    "type": f'{api_base_url}/session-types/search/by_name/{body.session_type}',
                    "cabinet": f'{api_base_url}/cabinets/search/by_building_and_number/{body.building_number}/{body.cabinet_number}' if body.cabinet_number and body.building_number else None
                }
                hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                return ShowSessionWithHATEOAS(session=session_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при создании занятия: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_session_by_composite_key(session_number: int, session_date: date, teacher_in_plan: int, request: Request, db) -> ShowSessionWithHATEOAS:
    async with db as session:
        async with session.begin():
            session_dal = SessionDAL(session)
            try:
                session_obj = await session_dal.get_session_by_composite_key(session_number, session_date, teacher_in_plan)
                if not session_obj:
                    raise HTTPException(status_code=404, detail=f"Занятие с номером {session_number}, датой {session_date} и записью в расписании преподавателя {teacher_in_plan} не найдено")

                session_dict = {
                    "session_number": session_obj.session_number,
                    "session_date": session_obj.date,
                    "teacher_in_plan": session_obj.teacher_in_plan,
                    "session_type": session_obj.session_type,
                    "cabinet_number": session_obj.cabinet_number,
                    "building_number": session_obj.building_number,
                }
                session_pydantic = ShowSession.model_validate(session_dict)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/sessions/search/by_composite_key/{session_number}/{session_date}/{teacher_in_plan}',
                    "update": f'{api_base_url}/sessions/update',
                    "delete": f'{api_base_url}/sessions/delete/{session_number}/{session_date}/{teacher_in_plan}',
                    "sessions": f'{api_base_url}/sessions',
                    "plan": f'{api_base_url}/teachers_in_plans/search/by_id/{session_obj.teacher_in_plan}',
                    "type": f'{api_base_url}/session-types/search/by_name/{session_obj.session_type}',
                    "cabinet": f'{api_base_url}/cabinets/search/by_building_and_number/{session_obj.building_number}/{session_obj.cabinet_number}' if session_obj.cabinet_number and session_obj.building_number else None
                }
                hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                return ShowSessionWithHATEOAS(session=session_pydantic, links=hateoas_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Получение занятия {session_number} на {session_date} для плана {teacher_in_plan} отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_sessions_by_plan(teacher_in_plan_id: int, page: int, limit: int, request: Request, db) -> ShowSessionListWithHATEOAS:
    async with db as session:
        async with session.begin():
            teacher_in_plan_dal = TeacherInPlanDAL(session)
            session_dal = SessionDAL(session)
            try:
                if not await ensure_teacher_in_plan_exists(teacher_in_plan_dal, teacher_in_plan_id):
                    raise HTTPException(status_code=404, detail=f"Запись в расписании преподавателя с id {teacher_in_plan_id} не найдена")

                sessions = await session_dal.get_sessions_by_plan(teacher_in_plan_id, page, limit)
                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                sessions_with_hateoas = []
                for session_obj in sessions:
                    session_dict = {
                        "session_number": session_obj.session_number,
                        "session_date": session_obj.date,
                        "teacher_in_plan": session_obj.teacher_in_plan,
                        "session_type": session_obj.session_type,
                        "cabinet_number": session_obj.cabinet_number,
                        "building_number": session_obj.building_number,
                    }
                    session_pydantic = ShowSession.model_validate(session_dict)
                    session_number = session_obj.session_number
                    session_date = session_obj.date
                    plan_id = session_obj.teacher_in_plan
                    session_links = {
                        "self": f'{api_base_url}/sessions/search/by_composite_key/{session_number}/{session_date}/{plan_id}',
                        "update": f'{api_base_url}/sessions/update',
                        "delete": f'{api_base_url}/sessions/delete/{session_number}/{session_date}/{plan_id}',
                        "sessions": f'{api_base_url}/sessions',
                        "plan": f'{api_base_url}/teachers_in_plans/search/by_id/{plan_id}',
                        "type": f'{api_base_url}/session-types/search/by_name/{session_obj.session_type}',
                        "cabinet": f'{api_base_url}/cabinets/search/by_building_and_number/{session_obj.building_number}/{session_obj.cabinet_number}' if session_obj.cabinet_number and session_obj.building_number else None
                    }
                    session_links = {k: v for k, v in session_links.items() if v is not None}
                    session_with_links = ShowSessionWithHATEOAS(session=session_pydantic, links=session_links)
                    sessions_with_hateoas.append(session_with_links)

                collection_links = {
                    "self": f'{api_base_url}/sessions/search/by_plan/{teacher_in_plan_id}?page={page}&limit={limit}',
                    "create": f'{api_base_url}/sessions/create',
                    "plan": f'{api_base_url}/teachers_in_plans/search/by_id/{teacher_in_plan_id}'
                }
                collection_links = {k: v for k, v in collection_links.items() if v is not None}

                return ShowSessionListWithHATEOAS(sessions=sessions_with_hateoas, links=collection_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Получение занятий для плана {teacher_in_plan_id} отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_sessions_by_date(session_date: date, page: int, limit: int, request: Request, db) -> ShowSessionListWithHATEOAS:
    async with db as session:
        async with session.begin():
            session_dal = SessionDAL(session)
            try:
                sessions = await session_dal.get_sessions_by_date(session_date, page, limit)
                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                sessions_with_hateoas = []
                for session_obj in sessions:
                    session_dict = {
                        "session_number": session_obj.session_number,
                        "session_date": session_obj.date,
                        "teacher_in_plan": session_obj.teacher_in_plan,
                        "session_type": session_obj.session_type,
                        "cabinet_number": session_obj.cabinet_number,
                        "building_number": session_obj.building_number,
                    }
                    session_pydantic = ShowSession.model_validate(session_dict)
                    session_number = session_obj.session_number
                    plan_id = session_obj.teacher_in_plan
                    session_links = {
                        "self": f'{api_base_url}/sessions/search/by_composite_key/{session_number}/{session_date}/{plan_id}',
                        "update": f'{api_base_url}/sessions/update',
                        "delete": f'{api_base_url}/sessions/delete/{session_number}/{session_date}/{plan_id}',
                        "sessions": f'{api_base_url}/sessions',
                        "plan": f'{api_base_url}/teachers_in_plans/search/by_id/{plan_id}',
                        "type": f'{api_base_url}/session-types/search/by_name/{session_obj.session_type}',
                        "cabinet": f'{api_base_url}/cabinets/search/by_building_and_number/{session_obj.building_number}/{session_obj.cabinet_number}' if session_obj.cabinet_number and session_obj.building_number else None
                    }
                    session_links = {k: v for k, v in session_links.items() if v is not None}
                    session_with_links = ShowSessionWithHATEOAS(session=session_pydantic, links=session_links)
                    sessions_with_hateoas.append(session_with_links)

                collection_links = {
                    "self": f'{api_base_url}/sessions/search/by_date/{session_date}?page={page}&limit={limit}',
                    "create": f'{api_base_url}/sessions/create'
                }
                collection_links = {k: v for k, v in collection_links.items() if v is not None}

                return ShowSessionListWithHATEOAS(sessions=sessions_with_hateoas, links=collection_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Получение занятий на дату {session_date} отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_sessions_by_type(session_type: str, page: int, limit: int, request: Request, db) -> ShowSessionListWithHATEOAS:
    async with db as session:
        async with session.begin():
            session_type_dal = SessionTypeDAL(session)
            session_dal = SessionDAL(session)
            try:
                if not await ensure_session_type_exists(session_type_dal, session_type):
                    raise HTTPException(status_code=404, detail=f"Тип занятия {session_type} не найден")

                sessions = await session_dal.get_sessions_by_type(session_type, page, limit)
                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                sessions_with_hateoas = []
                for session_obj in sessions:
                    session_dict = {
                        "session_number": session_obj.session_number,
                        "session_date": session_obj.date,
                        "teacher_in_plan": session_obj.teacher_in_plan,
                        "session_type": session_obj.session_type,
                        "cabinet_number": session_obj.cabinet_number,
                        "building_number": session_obj.building_number,
                    }
                    session_pydantic = ShowSession.model_validate(session_dict)
                    session_number = session_obj.session_number
                    session_date = session_obj.date
                    plan_id = session_obj.teacher_in_plan
                    session_links = {
                        "self": f'{api_base_url}/sessions/search/by_composite_key/{session_number}/{session_date}/{plan_id}',
                        "update": f'{api_base_url}/sessions/update',
                        "delete": f'{api_base_url}/sessions/delete/{session_number}/{session_date}/{plan_id}',
                        "sessions": f'{api_base_url}/sessions',
                        "plan": f'{api_base_url}/teachers_in_plans/search/by_id/{plan_id}',
                        "type": f'{api_base_url}/session-types/search/by_name/{session_type}',
                        "cabinet": f'{api_base_url}/cabinets/search/by_building_and_number/{session_obj.building_number}/{session_obj.cabinet_number}' if session_obj.cabinet_number and session_obj.building_number else None
                    }
                    session_links = {k: v for k, v in session_links.items() if v is not None}
                    session_with_links = ShowSessionWithHATEOAS(session=session_pydantic, links=session_links)
                    sessions_with_hateoas.append(session_with_links)

                collection_links = {
                    "self": f'{api_base_url}/sessions/search/by_type/{session_type}?page={page}&limit={limit}',
                    "create": f'{api_base_url}/sessions/create',
                    "type": f'{api_base_url}/session-types/search/by_name/{session_type}'
                }
                collection_links = {k: v for k, v in collection_links.items() if v is not None}

                return ShowSessionListWithHATEOAS(sessions=sessions_with_hateoas, links=collection_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Получение занятий по типу {session_type} отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_sessions_by_cabinet(cabinet_number: int, building_number: int, page: int, limit: int, request: Request, db) -> ShowSessionListWithHATEOAS:
    async with db as session:
        async with session.begin():
            cabinet_dal = CabinetDAL(session)
            session_dal = SessionDAL(session)
            try:
                if not await ensure_cabinet_exists(cabinet_dal, building_number, cabinet_number):
                    raise HTTPException(status_code=404, detail=f"Кабинет {cabinet_number} в здании {building_number} не найден")

                sessions = await session_dal.get_sessions_by_cabinet(cabinet_number, building_number, page, limit)
                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                sessions_with_hateoas = []
                for session_obj in sessions:
                    session_dict = {
                        "session_number": session_obj.session_number,
                        "session_date": session_obj.date,
                        "teacher_in_plan": session_obj.teacher_in_plan,
                        "session_type": session_obj.session_type,
                        "cabinet_number": session_obj.cabinet_number,
                        "building_number": session_obj.building_number,
                    }
                    session_pydantic = ShowSession.model_validate(session_dict)
                    session_number = session_obj.session_number
                    session_date = session_obj.date
                    plan_id = session_obj.teacher_in_plan
                    session_links = {
                        "self": f'{api_base_url}/sessions/search/by_composite_key/{session_number}/{session_date}/{plan_id}',
                        "update": f'{api_base_url}/sessions/update',
                        "delete": f'{api_base_url}/sessions/delete/{session_number}/{session_date}/{plan_id}',
                        "sessions": f'{api_base_url}/sessions',
                        "plan": f'{api_base_url}/teachers_in_plans/search/by_id/{plan_id}',
                        "type": f'{api_base_url}/session-types/search/by_name/{session_obj.session_type}',
                        "cabinet": f'{api_base_url}/cabinets/search/by_building_and_number/{building_number}/{cabinet_number}'
                    }
                    session_with_links = ShowSessionWithHATEOAS(session=session_pydantic, links=session_links)
                    sessions_with_hateoas.append(session_with_links)

                collection_links = {
                    "self": f'{api_base_url}/sessions/search/by_cabinet/{building_number}/{cabinet_number}?page={page}&limit={limit}',
                    "create": f'{api_base_url}/sessions/create',
                    "cabinet": f'{api_base_url}/cabinets/search/by_building_and_number/{building_number}/{cabinet_number}'
                }
                collection_links = {k: v for k, v in collection_links.items() if v is not None}

                return ShowSessionListWithHATEOAS(sessions=sessions_with_hateoas, links=collection_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Получение занятий для кабинета {cabinet_number} в здании {building_number} отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_all_sessions(page: int, limit: int, request: Request, db) -> ShowSessionListWithHATEOAS:
    async with db as session:
        async with session.begin():
            session_dal = SessionDAL(session)
            try:
                sessions = await session_dal.get_all_sessions(page, limit)
                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                sessions_with_hateoas = []
                for session_obj in sessions:
                    session_dict = {
                        "session_number": session_obj.session_number,
                        "session_date": session_obj.date,
                        "teacher_in_plan": session_obj.teacher_in_plan,
                        "session_type": session_obj.session_type,
                        "cabinet_number": session_obj.cabinet_number,
                        "building_number": session_obj.building_number,
                    }
                    session_pydantic = ShowSession.model_validate(session_dict)
                    session_number = session_obj.session_number
                    session_date = session_obj.date
                    plan_id = session_obj.teacher_in_plan
                    session_links = {
                        "self": f'{api_base_url}/sessions/search/by_composite_key/{session_number}/{session_date}/{plan_id}',
                        "update": f'{api_base_url}/sessions/update',
                        "delete": f'{api_base_url}/sessions/delete/{session_number}/{session_date}/{plan_id}',
                        "sessions": f'{api_base_url}/sessions',
                        "plan": f'{api_base_url}/teachers_in_plans/search/by_id/{plan_id}',
                        "type": f'{api_base_url}/session-types/search/by_name/{session_obj.session_type}',
                        "cabinet": f'{api_base_url}/cabinets/search/by_building_and_number/{session_obj.building_number}/{session_obj.cabinet_number}' if session_obj.cabinet_number and session_obj.building_number else None
                    }
                    session_links = {k: v for k, v in session_links.items() if v is not None}
                    session_with_links = ShowSessionWithHATEOAS(session=session_pydantic, links=session_links)
                    sessions_with_hateoas.append(session_with_links)

                collection_links = {
                    "self": f'{api_base_url}/sessions/search?page={page}&limit={limit}',
                    "create": f'{api_base_url}/sessions/create'
                }
                collection_links = {k: v for k, v in collection_links.items() if v is not None}

                return ShowSessionListWithHATEOAS(sessions=sessions_with_hateoas, links=collection_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Получение занятий отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _delete_session(session_number: int, session_date: date, teacher_in_plan: int, request: Request, db) -> ShowSessionWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                session_dal = SessionDAL(session)
                session_obj = await session_dal.get_session_by_composite_key(session_number, session_date, teacher_in_plan)
                if not session_obj:
                    raise HTTPException(status_code=404, detail=f"Занятие с номером {session_number}, датой {session_date} и записью в расписании преподавателя {teacher_in_plan} не найдено")

                deleted_session_obj = await session_dal.delete_session(session_number, session_date, teacher_in_plan)
                
                if not deleted_session_obj:
                    raise HTTPException(status_code=404, detail=f"Занятие с номером {session_number}, датой {session_date} и записью в расписании преподавателя {teacher_in_plan} не найдено")

                session_dict = {
                    "session_number": deleted_session_obj.session_number,
                    "session_date": deleted_session_obj.date,
                    "teacher_in_plan": deleted_session_obj.teacher_in_plan,
                    "session_type": deleted_session_obj.session_type,
                    "cabinet_number": deleted_session_obj.cabinet_number,
                    "building_number": deleted_session_obj.building_number,
                }
                session_pydantic = ShowSession.model_validate(session_dict)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "sessions": f'{api_base_url}/sessions',
                    "create": f'{api_base_url}/sessions/create'
                }
                hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                return ShowSessionWithHATEOAS(session=session_pydantic, links=hateoas_links)

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Неожиданная ошибка при удалении занятия {session_number} на {session_date} для плана {teacher_in_plan}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении занятия.")


async def _update_session(body: UpdateSession, request: Request, db) -> ShowSessionWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["session_number", "session_date", "teacher_in_plan", "new_session_number", "new_session_date", "new_teacher_in_plan", "new_cabinet_number", "new_building_number"]}

                target_session_number = body.session_number
                target_session_date = body.session_date
                target_teacher_in_plan = body.teacher_in_plan
                if body.new_session_number is not None:
                    update_data["session_number"] = body.new_session_number
                    target_session_number = body.new_session_number
                if body.new_session_date is not None:
                    update_data["date"] = body.new_session_date 
                    target_session_date = body.new_session_date
                if body.new_teacher_in_plan is not None:
                    update_data["teacher_in_plan"] = body.new_teacher_in_plan
                    target_teacher_in_plan = body.new_teacher_in_plan
                    
                if body.new_cabinet_number is not None:
                    update_data["cabinet_number"] = body.new_cabinet_number
                if body.new_building_number is not None:
                    update_data["building_number"] = body.new_building_number

                if "session_type" in update_data:
                    session_type_dal = SessionTypeDAL(session)
                    if not await ensure_session_type_exists(session_type_dal, update_data["session_type"]):
                        raise HTTPException(status_code=404, detail=f"Тип занятия {update_data['session_type']} не найден")
                    
                if "cabinet_number" in update_data or "building_number" in update_data:
                    cabinet_number_to_check = update_data.get("cabinet_number")
                    building_number_to_check = update_data.get("building_number")
                    
                    if cabinet_number_to_check is not None and building_number_to_check is not None:
                        cabinet_dal = CabinetDAL(session)
                        
                        cabinet_exists = await cabinet_dal.get_cabinet_by_number_and_building(building_number_to_check, cabinet_number_to_check)
                        if not cabinet_exists:
                            raise HTTPException(status_code=404, detail=f"Кабинет {cabinet_number_to_check} в здании {building_number_to_check} не найден")

                session_dal = SessionDAL(session)

                session_obj = await session_dal.get_session_by_composite_key(body.session_number, body.session_date, body.teacher_in_plan)
                if not session_obj:
                    raise HTTPException(status_code=404, detail=f"Занятие с номером {body.session_number}, датой {body.session_date} и записью в расписании преподавателя {body.teacher_in_plan} не найдено")

                if (target_session_number, target_session_date, target_teacher_in_plan) != (body.session_number, body.session_date, body.teacher_in_plan):
                    existing_new_session = await session_dal.get_session_by_composite_key(target_session_number, target_session_date, target_teacher_in_plan)
                    if existing_new_session:
                        raise HTTPException(status_code=400, detail=f"Занятие с номером {target_session_number}, датой {target_session_date} и записью в расписании преподавателя {target_teacher_in_plan} уже существует")

                updated_session_obj = await session_dal.update_session(target_session_number=body.session_number, target_session_date=body.session_date, target_teacher_in_plan=body.teacher_in_plan, **update_data)
                if not updated_session_obj:
                    raise HTTPException(status_code=404, detail=f"Занятие с номером {body.session_number}, датой {body.session_date} и записью в расписании преподавателя {body.teacher_in_plan} не найдено")

                session_number = updated_session_obj.session_number
                session_date = updated_session_obj.date
                teacher_in_plan_id = updated_session_obj.teacher_in_plan
                
                session_dict = {
                    "session_number": updated_session_obj.session_number,
                    "session_date": updated_session_obj.date,
                    "teacher_in_plan": updated_session_obj.teacher_in_plan,
                    "session_type": updated_session_obj.session_type,
                    "cabinet_number": updated_session_obj.cabinet_number,
                    "building_number": updated_session_obj.building_number,
                }
                session_pydantic = ShowSession.model_validate(session_dict)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/sessions/search/by_composite_key/{session_number}/{session_date}/{teacher_in_plan_id}',
                    "update": f'{api_base_url}/sessions/update',
                    "delete": f'{api_base_url}/sessions/delete/{session_number}/{session_date}/{teacher_in_plan_id}',
                    "sessions": f'{api_base_url}/sessions',
                    "plan": f'{api_base_url}/teachers_in_plans/search/by_id/{updated_session_obj.teacher_in_plan}',
                    "type": f'{api_base_url}/session-types/search/by_name/{updated_session_obj.session_type}',
                    "cabinet": f'{api_base_url}/cabinets/search/by_building_and_number/{updated_session_obj.building_number}/{updated_session_obj.cabinet_number}' if updated_session_obj.cabinet_number and updated_session_obj.building_number else None
                }
                hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                return ShowSessionWithHATEOAS(session=session_pydantic, links=hateoas_links)

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.warning(f"Изменение данных о занятии отменено (Ошибка: {e})")
            raise e


@session_router.post("/create", response_model=ShowSessionWithHATEOAS, status_code=201)
async def create_session(body: CreateSession, request: Request, db: AsyncSession = Depends(get_db)):
    return await _create_new_session(body, request, db)


@session_router.get("/search/by_composite_key/{session_number}/{session_date}/{teacher_in_plan}", response_model=ShowSessionWithHATEOAS, responses={404: {"description": "Занятие не найдено"}})
async def get_session_by_composite_key(session_number: int, session_date: date, teacher_in_plan: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_session_by_composite_key(session_number, session_date, teacher_in_plan, request, db)


@session_router.get("/search/by_plan/{teacher_in_plan_id}", response_model=ShowSessionListWithHATEOAS, responses={404: {"description": "Занятия не найдены"}})
async def get_sessions_by_plan(teacher_in_plan_id: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_sessions_by_plan(teacher_in_plan_id, query_param.page, query_param.limit, request, db)


@session_router.get("/search/by_date/{session_date}", response_model=ShowSessionListWithHATEOAS, responses={404: {"description": "Занятия не найдены"}})
async def get_sessions_by_date(session_date: date, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_sessions_by_date(session_date, query_param.page, query_param.limit, request, db)


@session_router.get("/search/by_type/{session_type}", response_model=ShowSessionListWithHATEOAS, responses={404: {"description": "Занятия не найдены"}})
async def get_sessions_by_type(session_type: str, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_sessions_by_type(session_type, query_param.page, query_param.limit, request, db)


@session_router.get("/search/by_cabinet/{building_number}/{cabinet_number}", response_model=ShowSessionListWithHATEOAS, responses={404: {"description": "Занятия не найдены"}})
async def get_sessions_by_cabinet(building_number: int, cabinet_number: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_sessions_by_cabinet(cabinet_number, building_number, query_param.page, query_param.limit, request, db)


@session_router.get("/search", response_model=ShowSessionListWithHATEOAS)
async def get_all_sessions(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_all_sessions(query_param.page, query_param.limit, request, db)


@session_router.delete("/delete/{session_number}/{session_date}/{teacher_in_plan}", response_model=ShowSessionWithHATEOAS, responses={404: {"description": "Занятие не найдено"}})
async def delete_session(session_number: int, session_date: date, teacher_in_plan: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _delete_session(session_number, session_date, teacher_in_plan, request, db)


@session_router.put("/update", response_model=ShowSessionWithHATEOAS, responses={404: {"description": "Занятие не найдено"}})
async def update_session(body: UpdateSession, request: Request, db: AsyncSession = Depends(get_db)):
    return await _update_session(body, request, db)






category_router = APIRouter()

'''
===============
TeacherCategory
===============
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


session_type_router = APIRouter()

'''
==============================
CRUD operations for SessionType
==============================
'''

async def _create_new_session_type(body: CreateSessionType, request: Request, db) -> ShowSessionTypeWithHATEOAS:
    async with db as session:
        async with session.begin():
            session_type_dal = SessionTypeDAL(session)
            try:
                if not await ensure_session_type_unique(session_type_dal, body.name):
                    raise HTTPException(status_code=400, detail=f"Тип сессии с именем '{body.name}' уже существует")

                session_type = await session_type_dal.create_session_type(
                    name=body.name
                )
                session_type_name = session_type.name
                session_type_pydantic = ShowSessionType.model_validate(session_type, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/session-types/search/by_name/{session_type_name}',
                    "update": f'{api_base_url}/session-types/update',
                    "delete": f'{api_base_url}/session-types/delete/{session_type_name}',
                    "session_types": f'{api_base_url}/session-types',
                    "sessions": f'{api_base_url}/sessions/search/by_type/{session_type_name}'
                }

                return ShowSessionTypeWithHATEOAS(session_type=session_type_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при создании типа сессии '{body.name}': {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_session_type_by_name(name: str, request: Request, db) -> ShowSessionTypeWithHATEOAS:
    async with db as session:
        async with session.begin():
            session_type_dal = SessionTypeDAL(session)
            try:
                session_type = await session_type_dal.get_session_type(name)
                if not session_type:
                    raise HTTPException(status_code=404, detail=f"Тип сессии с именем '{name}' не найден")
                session_type_pydantic = ShowSessionType.model_validate(session_type, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/session-types/search/by_name/{name}',
                    "update": f'{api_base_url}/session-types/update',
                    "delete": f'{api_base_url}/session-types/delete/{name}',
                    "session_types": f'{api_base_url}/session-types',
                    "sessions": f'{api_base_url}/sessions/search/by_type/{name}'
                }

                return ShowSessionTypeWithHATEOAS(session_type=session_type_pydantic, links=hateoas_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Получение типа сессии отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_all_session_types(page: int, limit: int, request: Request, db) -> ShowSessionTypeListWithHATEOAS:
    async with db as session:
        async with session.begin():
            session_type_dal = SessionTypeDAL(session)
            try:
                session_types = await session_type_dal.get_all_session_types(page, limit)
                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                session_types_with_hateoas = []
                for session_type in session_types:
                    session_type_pydantic = ShowSessionType.model_validate(session_type, from_attributes=True)
                    session_type_name = session_type.name
                    session_type_links = {
                        "self": f'{api_base_url}/session-types/search/by_name/{session_type_name}',
                        "update": f'{api_base_url}/session-types/update',
                        "delete": f'{api_base_url}/session-types/delete/{session_type_name}',
                        "session_types": f'{api_base_url}/session-types',
                        "sessions": f'{api_base_url}/sessions/search/by_type/{session_type_name}'
                    }
                    session_type_with_links = ShowSessionTypeWithHATEOAS(session_type=session_type_pydantic, links=session_type_links)
                    session_types_with_hateoas.append(session_type_with_links)

                collection_links = {
                    "self": f'{api_base_url}/session-types/search?page={page}&limit={limit}',
                    "create": f'{api_base_url}/session-types/create'
                }
                collection_links = {k: v for k, v in collection_links.items() if v is not None}

                return ShowSessionTypeListWithHATEOAS(session_types=session_types_with_hateoas, links=collection_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Получение типов сессий отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _delete_session_type(name: str, request: Request, db) -> ShowSessionTypeWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                session_type_dal = SessionTypeDAL(session)
                if not await ensure_session_type_exists(session_type_dal, name):
                    raise HTTPException(status_code=404, detail=f"Тип сессии с именем '{name}' не найден")

                session_type = await session_type_dal.delete_session_type(name)
                if not session_type:
                    raise HTTPException(status_code=404, detail=f"Тип сессии с именем '{name}' не найден")

                session_type_pydantic = ShowSessionType.model_validate(session_type, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "session_types": f'{api_base_url}/session-types',
                    "create": f'{api_base_url}/session-types/create'
                }
                hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                return ShowSessionTypeWithHATEOAS(session_type=session_type_pydantic, links=hateoas_links)

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Неожиданная ошибка при удалении типа сессии '{name}': {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении типа сессии.")


async def _update_session_type(body: UpdateSessionType, request: Request, db) -> ShowSessionTypeWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                session_type_dal = SessionTypeDAL(session)

                if not await ensure_session_type_exists(session_type_dal, body.current_name):
                    raise HTTPException(status_code=404, detail=f"Тип сессии с именем '{body.current_name}' не найден")

                if body.new_name != body.current_name:
                    if not await ensure_session_type_unique(session_type_dal, body.new_name):
                        raise HTTPException(status_code=400, detail=f"Тип сессии с именем '{body.new_name}' уже существует")

                session_type = await session_type_dal.update_session_type(current_name=body.current_name, name=body.new_name)
                if not session_type:
                    raise HTTPException(status_code=404, detail=f"Тип сессии с именем '{body.current_name}' не найден")

                session_type_name = session_type.name
                session_type_pydantic = ShowSessionType.model_validate(session_type, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/session-types/search/by_name/{session_type_name}',
                    "update": f'{api_base_url}/session-types/update',
                    "delete": f'{api_base_url}/session-types/delete/{session_type_name}',
                    "session_types": f'{api_base_url}/session-types',
                    "sessions": f'{api_base_url}/sessions/search/by_type/{session_type_name}'
                }

                return ShowSessionTypeWithHATEOAS(session_type=session_type_pydantic, links=hateoas_links)

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.warning(f"Изменение данных о типе сессии отменено (Ошибка: {e})")
            raise e


@session_type_router.post("/create", response_model=ShowSessionTypeWithHATEOAS, status_code=201)
async def create_session_type(body: CreateSessionType, request: Request, db: AsyncSession = Depends(get_db)):
    return await _create_new_session_type(body, request, db)


@session_type_router.get("/search/by_name/{name}", response_model=ShowSessionTypeWithHATEOAS, responses={404: {"description": "Тип сессии не найден"}})
async def get_session_type_by_name(name: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_session_type_by_name(name, request, db)


@session_type_router.get("/search", response_model=ShowSessionTypeListWithHATEOAS)
async def get_all_session_types(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_all_session_types(query_param.page, query_param.limit, request, db)


@session_type_router.delete("/delete/{name}", response_model=ShowSessionTypeWithHATEOAS, responses={404: {"description": "Тип сессии не найден"}})
async def delete_session_type(name: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await _delete_session_type(name, request, db)


@session_type_router.put("/update", response_model=ShowSessionTypeWithHATEOAS, responses={404: {"description": "Тип сессии не найден"}})
async def update_session_type(body: UpdateSessionType, request: Request, db: AsyncSession = Depends(get_db)):
    return await _update_session_type(body, request, db)


semester_router = APIRouter()

'''
============================
CRUD operations for Semester
============================
'''

async def _create_new_semester(body: CreateSemester, request: Request, db) -> ShowSemesterWithHATEOAS:
    async with db as session:
        async with session.begin():
            plan_dal = PlanDAL(session)
            semester_dal = SemesterDAL(session)
            try:
                if not await ensure_plan_exists(plan_dal, body.plan_id):
                    raise HTTPException(status_code=404, detail=f"Учебный план с id {body.plan_id} не найден")
                if not await ensure_semester_unique(semester_dal, body.semester, body.plan_id):
                    raise HTTPException(status_code=400, detail=f"Семестр {body.semester} для плана {body.plan_id} уже существует")

                semester_obj = await semester_dal.create_semester(
                    semester=body.semester,
                    weeks=body.weeks,
                    practice_weeks=body.practice_weeks,
                    plan_id=body.plan_id
                )
                semester_number = semester_obj.semester
                plan_id = semester_obj.plan_id
                semester_pydantic = ShowSemester.model_validate(semester_obj, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/semesters/search/by_semester_and_plan/{semester_number}/{plan_id}',
                    "update": f'{api_base_url}/semesters/update',
                    "delete": f'{api_base_url}/semesters/delete/{semester_number}/{plan_id}',
                    "semesters": f'{api_base_url}/semesters',
                    "plan": f'{api_base_url}/plans/search/by_id/{plan_id}'
                }

                return ShowSemesterWithHATEOAS(semester=semester_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при создании семестра {body.semester} для плана {body.plan_id}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_semester_by_semester_and_plan(semester: int, plan_id: int, request: Request, db) -> ShowSemesterWithHATEOAS:
    async with db as session:
        async with session.begin():
            semester_dal = SemesterDAL(session)
            try:
                semester_obj = await semester_dal.get_semester_by_semester_and_plan(semester, plan_id)
                if not semester_obj:
                    raise HTTPException(status_code=404, detail=f"Семестр {semester} для плана {plan_id} не найден")
                semester_pydantic = ShowSemester.model_validate(semester_obj, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/semesters/search/by_semester_and_plan/{semester}/{plan_id}',
                    "update": f'{api_base_url}/semesters/update',
                    "delete": f'{api_base_url}/semesters/delete/{semester}/{plan_id}',
                    "semesters": f'{api_base_url}/semesters',
                    "plan": f'{api_base_url}/plans/search/by_id/{plan_id}'
                }

                return ShowSemesterWithHATEOAS(semester=semester_pydantic, links=hateoas_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Получение семестра {semester} для плана {plan_id} отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_all_semesters(page: int, limit: int, request: Request, db) -> ShowSemesterListWithHATEOAS:
    async with db as session:
        async with session.begin():
            semester_dal = SemesterDAL(session)
            try:
                semesters = await semester_dal.get_all_semesters(page, limit)
                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                semesters_with_hateoas = []
                for semester_obj in semesters:
                    semester_pydantic = ShowSemester.model_validate(semester_obj, from_attributes=True)
                    semester_number = semester_obj.semester
                    plan_id = semester_obj.plan_id
                    semester_links = {
                        "self": f'{api_base_url}/semesters/search/by_semester_and_plan/{semester_number}/{plan_id}',
                        "update": f'{api_base_url}/semesters/update',
                        "delete": f'{api_base_url}/semesters/delete/{semester_number}/{plan_id}',
                        "semesters": f'{api_base_url}/semesters',
                        "plan": f'{api_base_url}/plans/search/by_id/{plan_id}'
                    }
                    semester_with_links = ShowSemesterWithHATEOAS(semester=semester_pydantic, links=semester_links)
                    semesters_with_hateoas.append(semester_with_links)

                collection_links = {
                    "self": f'{api_base_url}/semesters/search?page={page}&limit={limit}',
                    "create": f'{api_base_url}/semesters/create'
                }
                collection_links = {k: v for k, v in collection_links.items() if v is not None}

                return ShowSemesterListWithHATEOAS(semesters=semesters_with_hateoas, links=collection_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Получение семестров отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _delete_semester(semester: int, plan_id: int, request: Request, db) -> ShowSemesterWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                semester_dal = SemesterDAL(session)
                if not await ensure_semester_exists(semester_dal, semester, plan_id):
                    raise HTTPException(status_code=404, detail=f"Семестр {semester} для плана {plan_id} не найден")

                semester_obj = await semester_dal.delete_semester(semester, plan_id)
                if not semester_obj:
                    raise HTTPException(status_code=404, detail=f"Семестр {semester} для плана {plan_id} не найден")

                semester_pydantic = ShowSemester.model_validate(semester_obj, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "semesters": f'{api_base_url}/semesters',
                    "create": f'{api_base_url}/semesters/create',
                    "plan": f'{api_base_url}/plans/search/by_id/{plan_id}'
                }
                hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                return ShowSemesterWithHATEOAS(semester=semester_pydantic, links=hateoas_links)

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Неожиданная ошибка при удалении семестра {semester} в плане {plan_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении семестра.")


async def _update_semester(body: UpdateSemester, request: Request, db) -> ShowSemesterWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["semester", "plan_id", "new_semester", "new_plan_id"]}
                target_semester = body.semester
                target_plan_id = body.plan_id
                if body.new_semester is not None or body.new_plan_id is not None:
                    if body.new_semester is not None:
                        update_data["semester"] = body.new_semester
                        target_semester = body.new_semester 
                    if body.new_plan_id is not None:
                        update_data["plan_id"] = body.new_plan_id
                        target_plan_id = body.new_plan_id 
                        
                    if (target_semester, target_plan_id) != (body.semester, body.plan_id):
                        semester_dal = SemesterDAL(session)
                        if not await ensure_semester_unique(semester_dal, target_semester, target_plan_id):
                            raise HTTPException(status_code=400, detail=f"Семестр {target_semester} для плана {target_plan_id} уже существует")

                semester_dal = SemesterDAL(session)

                if not await ensure_semester_exists(semester_dal, body.semester, body.plan_id):
                    raise HTTPException(status_code=404, detail=f"Семестр {body.semester} для плана {body.plan_id} не найден")

                if "plan_id" in update_data:
                    plan_id_to_check = update_data["plan_id"]
                    plan_dal = PlanDAL(session)
                    if not await ensure_plan_exists(plan_dal, plan_id_to_check):
                        raise HTTPException(status_code=404, detail=f"Учебный план с id {plan_id_to_check} не найден")

                semester_obj = await semester_dal.update_semester(target_semester=body.semester, target_plan_id=body.plan_id, **update_data)
                if not semester_obj:
                    raise HTTPException(status_code=404, detail=f"Семестр {body.semester} для плана {body.plan_id} не найден")

                semester_number = semester_obj.semester 
                plan_id = semester_obj.plan_id
                semester_pydantic = ShowSemester.model_validate(semester_obj, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/semesters/search/by_semester_and_plan/{semester_number}/{plan_id}',
                    "update": f'{api_base_url}/semesters/update',
                    "delete": f'{api_base_url}/semesters/delete/{semester_number}/{plan_id}',
                    "semesters": f'{api_base_url}/semesters',
                    "plan": f'{api_base_url}/plans/search/by_id/{plan_id}'
                }

                return ShowSemesterWithHATEOAS(semester=semester_pydantic, links=hateoas_links)

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.warning(f"Изменение данных о семестре отменено (Ошибка: {e})")
            raise e


@semester_router.post("/create", response_model=ShowSemesterWithHATEOAS, status_code=201)
async def create_semester(body: CreateSemester, request: Request, db: AsyncSession = Depends(get_db)):
    return await _create_new_semester(body, request, db)


@semester_router.get("/search/by_semester_and_plan/{semester}/{plan_id}", response_model=ShowSemesterWithHATEOAS, responses={404: {"description": "Семестр не найден"}})
async def get_semester_by_semester_and_plan(semester: int, plan_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_semester_by_semester_and_plan(semester, plan_id, request, db)


@semester_router.get("/search", response_model=ShowSemesterListWithHATEOAS)
async def get_all_semesters(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_all_semesters(query_param.page, query_param.limit, request, db)


@semester_router.delete("/delete/{semester}/{plan_id}", response_model=ShowSemesterWithHATEOAS, responses={404: {"description": "Семестр не найден"}})
async def delete_semester(semester: int, plan_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _delete_semester(semester, plan_id, request, db)


@semester_router.put("/update", response_model=ShowSemesterWithHATEOAS, responses={404: {"description": "Семестр не найден"}})
async def update_semester(body: UpdateSemester, request: Request, db: AsyncSession = Depends(get_db)):
    return await _update_semester(body, request, db)


plan_router = APIRouter()

'''
==============================
CRUD operations for Plan
==============================
'''

async def _create_new_plan(body: CreatePlan, request: Request, db) -> ShowPlanWithHATEOAS:
    async with db as session:
        async with session.begin():
            speciality_dal = SpecialityDAL(session)
            plan_dal = PlanDAL(session)
            try:
                if not await ensure_speciality_exists(speciality_dal, body.speciality_code):
                    raise HTTPException(status_code=404, detail=f"Специальность с кодом {body.speciality_code} не найдена")

                plan = await plan_dal.create_plan(
                    year=body.year,
                    speciality_code=body.speciality_code
                )
                plan_id = plan.id 
                plan_pydantic = ShowPlan.model_validate(plan, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/plans/search/by_id/{plan_id}',
                    "update": f'{api_base_url}/plans/update',
                    "delete": f'{api_base_url}/plans/delete/{plan_id}',
                    "plans": f'{api_base_url}/plans',
                    "speciality": f'{api_base_url}/specialities/search/by_speciality_code/{body.speciality_code}',
                    "chapters": f'{api_base_url}/chapters/search/by_plan/{plan_id}',
                    "semesters": f'{api_base_url}/semesters/search/by_plan/{plan_id}'
                }

                return ShowPlanWithHATEOAS(plan=plan_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при создании учебного плана для специальности {body.speciality_code} на {body.year} год: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_plan_by_id(plan_id: int, request: Request, db) -> ShowPlanWithHATEOAS:
    async with db as session:
        async with session.begin():
            plan_dal = PlanDAL(session)
            try:
                plan = await plan_dal.get_plan_by_id(plan_id)
                if not plan:
                    raise HTTPException(status_code=404, detail=f"Учебный план с id {plan_id} не найден")
                plan_pydantic = ShowPlan.model_validate(plan, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/plans/search/by_id/{plan_id}',
                    "update": f'{api_base_url}/plans/update',
                    "delete": f'{api_base_url}/plans/delete/{plan_id}',
                    "plans": f'{api_base_url}/plans',
                    "speciality": f'{api_base_url}/specialities/search/by_speciality_code/{plan.speciality_code}',
                    "chapters": f'{api_base_url}/chapters/search/by_plan/{plan_id}',
                    "semesters": f'{api_base_url}/semesters/search/by_plan/{plan_id}'
                }

                return ShowPlanWithHATEOAS(plan=plan_pydantic, links=hateoas_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Получение учебного плана {plan_id} отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_all_plans(page: int, limit: int, request: Request, db) -> ShowPlanListWithHATEOAS:
    async with db as session:
        async with session.begin():
            plan_dal = PlanDAL(session)
            try:
                plans = await plan_dal.get_all_plans(page, limit)
                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                plans_with_hateoas = []
                for plan in plans:
                    plan_pydantic = ShowPlan.model_validate(plan, from_attributes=True)
                    plan_id = plan.id
                    plan_links = {
                        "self": f'{api_base_url}/plans/search/by_id/{plan_id}',
                        "update": f'{api_base_url}/plans/update',
                        "delete": f'{api_base_url}/plans/delete/{plan_id}',
                        "plans": f'{api_base_url}/plans',
                        "speciality": f'{api_base_url}/specialities/search/by_speciality_code/{plan.speciality_code}',
                        "chapters": f'{api_base_url}/chapters/search/by_plan/{plan_id}',
                        "semesters": f'{api_base_url}/semesters/search/by_plan/{plan_id}'
                    }
                    plan_with_links = ShowPlanWithHATEOAS(plan=plan_pydantic, links=plan_links)
                    plans_with_hateoas.append(plan_with_links)

                collection_links = {
                    "self": f'{api_base_url}/plans/search?page={page}&limit={limit}',
                    "create": f'{api_base_url}/plans/create'
                }
                collection_links = {k: v for k, v in collection_links.items() if v is not None}

                return ShowPlanListWithHATEOAS(plans=plans_with_hateoas, links=collection_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Получение учебных планов отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _delete_plan(plan_id: int, request: Request, db) -> ShowPlanWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                plan_dal = PlanDAL(session)
                
                if not await ensure_plan_exists(plan_dal, plan_id):
                    raise HTTPException(status_code=404, detail=f"Учебный план с id {plan_id} не найден")

                plan = await plan_dal.delete_plan(plan_id)

                if not plan:
                    raise HTTPException(status_code=404, detail=f"Учебный план с id {plan_id} не найден")

                plan_pydantic = ShowPlan.model_validate(plan, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "plans": f'{api_base_url}/plans',
                    "create": f'{api_base_url}/plans/create'
                }
                hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                return ShowPlanWithHATEOAS(plan=plan_pydantic, links=hateoas_links)

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Неожиданная ошибка при удалении учебного плана {plan_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении учебного плана.")


async def _update_plan(body: UpdatePlan, request: Request, db) -> ShowPlanWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                
                update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["plan_id"]}
                
                if "speciality_code" in update_data:
                    speciality_code_to_check = update_data["speciality_code"]
                    speciality_dal = SpecialityDAL(session)
                    if not await ensure_speciality_exists(speciality_dal, speciality_code_to_check):
                        raise HTTPException(status_code=404, detail=f"Специальность с кодом {speciality_code_to_check} не найдена")

                plan_dal = PlanDAL(session)

                if not await ensure_plan_exists(plan_dal, body.plan_id):
                    raise HTTPException(status_code=404, detail=f"Учебный план с id {body.plan_id} не найден")

                plan = await plan_dal.update_plan(target_id=body.plan_id, **update_data)
                if not plan:
                    raise HTTPException(status_code=404, detail=f"Учебный план с id {body.plan_id} не найден")

                plan_id = plan.id 
                plan_pydantic = ShowPlan.model_validate(plan, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/plans/search/by_id/{plan_id}',
                    "update": f'{api_base_url}/plans/update',
                    "delete": f'{api_base_url}/plans/delete/{plan_id}',
                    "plans": f'{api_base_url}/plans',
                    "speciality": f'{api_base_url}/specialities/search/by_speciality_code/{plan.speciality_code}',
                    "chapters": f'{api_base_url}/chapters/search/by_plan/{plan_id}',
                    "semesters": f'{api_base_url}/semesters/search/by_plan/{plan_id}'
                }

                return ShowPlanWithHATEOAS(plan=plan_pydantic, links=hateoas_links)

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.warning(f"Изменение данных о учебном плане отменено (Ошибка: {e})")
            raise e


@plan_router.post("/create", response_model=ShowPlanWithHATEOAS, status_code=201)
async def create_plan(body: CreatePlan, request: Request, db: AsyncSession = Depends(get_db)):
    return await _create_new_plan(body, request, db)


@plan_router.get("/search/by_id/{plan_id}", response_model=ShowPlanWithHATEOAS, responses={404: {"description": "Учебный план не найден"}})
async def get_plan_by_id(plan_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_plan_by_id(plan_id, request, db)


@plan_router.get("/search", response_model=ShowPlanListWithHATEOAS)
async def get_all_plans(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_all_plans(query_param.page, query_param.limit, request, db)


@plan_router.delete("/delete/{plan_id}", response_model=ShowPlanWithHATEOAS, responses={404: {"description": "Учебный план не найден"}})
async def delete_plan(plan_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _delete_plan(plan_id, request, db)


@plan_router.put("/update", response_model=ShowPlanWithHATEOAS, responses={404: {"description": "Учебный план не найден"}})
async def update_plan(body: UpdatePlan, request: Request, db: AsyncSession = Depends(get_db)):
    return await _update_plan(body, request, db)


chapter_router = APIRouter()

'''
==============================
CRUD operations for Chapter
==============================
'''

async def _create_new_chapter(body: CreateChapter, request: Request, db) -> ShowChapterWithHATEOAS:
    async with db as session:
        async with session.begin():
            plan_dal = PlanDAL(session)
            chapter_dal = ChapterDAL(session)
            try:
                if not await ensure_plan_exists(plan_dal, body.plan_id):
                    raise HTTPException(status_code=404, detail=f"Учебный план с id {body.plan_id} не найден")

                chapter = await chapter_dal.create_chapter(
                    code=body.code,
                    name=body.name,
                    plan_id=body.plan_id
                )
                chapter_id = chapter.id
                chapter_pydantic = ShowChapter.model_validate(chapter, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/chapters/search/by_id/{chapter_id}',
                    "update": f'{api_base_url}/chapters/update',
                    "delete": f'{api_base_url}/chapters/delete/{chapter_id}',
                    "chapters": f'{api_base_url}/chapters',
                    "plan": f'{api_base_url}/plans/search/by_id/{body.plan_id}',
                    "cycles": f'{api_base_url}/cycles/search/by_chapter/{chapter_id}'
                }

                return ShowChapterWithHATEOAS(chapter=chapter_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при создании главы '{body.name}' в плане {body.plan_id}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_chapter_by_id(chapter_id: int, request: Request, db) -> ShowChapterWithHATEOAS:
    async with db as session:
        async with session.begin():
            chapter_dal = ChapterDAL(session)
            try:
                chapter = await chapter_dal.get_chapter_by_id(chapter_id)
                if not chapter:
                    raise HTTPException(status_code=404, detail=f"Раздел с id {chapter_id} не найден")
                chapter_pydantic = ShowChapter.model_validate(chapter, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/chapters/search/by_id/{chapter_id}',
                    "update": f'{api_base_url}/chapters/update',
                    "delete": f'{api_base_url}/chapters/delete/{chapter_id}',
                    "chapters": f'{api_base_url}/chapters',
                    "plan": f'{api_base_url}/plans/search/by_id/{chapter.plan_id}',
                    "cycles": f'{api_base_url}/cycles/search/by_chapter/{chapter_id}'
                }

                return ShowChapterWithHATEOAS(chapter=chapter_pydantic, links=hateoas_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Получение главы {chapter_id} отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_chapters_by_plan(plan_id: int, page: int, limit: int, request: Request, db) -> ShowChapterListWithHATEOAS:
    async with db as session:
        async with session.begin():
            plan_dal = PlanDAL(session)
            chapter_dal = ChapterDAL(session)
            try:
                if not await ensure_plan_exists(plan_dal, plan_id):
                    raise HTTPException(status_code=404, detail=f"Учебный план с id {plan_id} не найден")

                chapters = await chapter_dal.get_chapters_by_plan(plan_id, page, limit)
                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                chapters_with_hateoas = []
                for chapter in chapters:
                    chapter_pydantic = ShowChapter.model_validate(chapter, from_attributes=True)
                    chapter_id = chapter.id
                    chapter_links = {
                        "self": f'{api_base_url}/chapters/search/by_id/{chapter_id}',
                        "update": f'{api_base_url}/chapters/update',
                        "delete": f'{api_base_url}/chapters/delete/{chapter_id}',
                        "chapters": f'{api_base_url}/chapters',
                        "plan": f'{api_base_url}/plans/search/by_id/{plan_id}',
                        "cycles": f'{api_base_url}/cycles/search/by_chapter/{chapter_id}'
                    }
                    chapter_with_links = ShowChapterWithHATEOAS(chapter=chapter_pydantic, links=chapter_links)
                    chapters_with_hateoas.append(chapter_with_links)

                collection_links = {
                    "self": f'{api_base_url}/chapters/search/by_plan/{plan_id}?page={page}&limit={limit}',
                    "create": f'{api_base_url}/chapters/create',
                    "plan": f'{api_base_url}/plans/search/by_id/{plan_id}'
                }
                collection_links = {k: v for k, v in collection_links.items() if v is not None}

                return ShowChapterListWithHATEOAS(chapters=chapters_with_hateoas, links=collection_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Получение глав для плана {plan_id} отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_all_chapters(page: int, limit: int, request: Request, db) -> ShowChapterListWithHATEOAS:
    async with db as session:
        async with session.begin():
            chapter_dal = ChapterDAL(session)
            try:
                chapters = await chapter_dal.get_all_chapters(page, limit)
                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                chapters_with_hateoas = []
                for chapter in chapters:
                    chapter_pydantic = ShowChapter.model_validate(chapter, from_attributes=True)
                    chapter_id = chapter.id
                    chapter_links = {
                        "self": f'{api_base_url}/chapters/search/by_id/{chapter_id}',
                        "update": f'{api_base_url}/chapters/update',
                        "delete": f'{api_base_url}/chapters/delete/{chapter_id}',
                        "chapters": f'{api_base_url}/chapters',
                        "plan": f'{api_base_url}/plans/search/by_id/{chapter.plan_id}',
                        "cycles": f'{api_base_url}/cycles/search/by_chapter/{chapter_id}'
                    }
                    chapter_with_links = ShowChapterWithHATEOAS(chapter=chapter_pydantic, links=chapter_links)
                    chapters_with_hateoas.append(chapter_with_links)

                collection_links = {
                    "self": f'{api_base_url}/chapters/search?page={page}&limit={limit}',
                    "create": f'{api_base_url}/chapters/create'
                }
                collection_links = {k: v for k, v in collection_links.items() if v is not None}

                return ShowChapterListWithHATEOAS(chapters=chapters_with_hateoas, links=collection_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Получение глав отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _delete_chapter(chapter_id: int, request: Request, db) -> ShowChapterWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                chapter_dal = ChapterDAL(session)
                if not await ensure_chapter_exists(chapter_dal, chapter_id):
                    raise HTTPException(status_code=404, detail=f"Раздел с id {chapter_id} не найден")

                chapter = await chapter_dal.delete_chapter(chapter_id)
                if not chapter:
                    raise HTTPException(status_code=404, detail=f"Раздел с id {chapter_id} не найден")

                chapter_pydantic = ShowChapter.model_validate(chapter, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "chapters": f'{api_base_url}/chapters',
                    "create": f'{api_base_url}/chapters/create',
                    "plan": f'{api_base_url}/plans/search/by_id/{chapter.plan_id}'
                }
                hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                return ShowChapterWithHATEOAS(chapter=chapter_pydantic, links=hateoas_links)

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Неожиданная ошибка при удалении главы {chapter_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении главы.")


async def _update_chapter(body: UpdateChapter, request: Request, db) -> ShowChapterWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["chapter_id"]}
                if "plan_id" in update_data:
                    plan_id_to_check = update_data["plan_id"]
                    plan_dal = PlanDAL(session)
                    if not await ensure_plan_exists(plan_dal, plan_id_to_check):
                        raise HTTPException(status_code=404, detail=f"Учебный план с id {plan_id_to_check} не найден")

                chapter_dal = ChapterDAL(session)

                if not await ensure_chapter_exists(chapter_dal, body.chapter_id):
                    raise HTTPException(status_code=404, detail=f"Раздел с id {body.chapter_id} не найден")

                chapter = await chapter_dal.update_chapter(target_id=body.chapter_id, **update_data)
                if not chapter:
                    raise HTTPException(status_code=404, detail=f"Раздел с id {body.chapter_id} не найден")

                chapter_id = chapter.id
                chapter_pydantic = ShowChapter.model_validate(chapter, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/chapters/search/by_id/{chapter_id}',
                    "update": f'{api_base_url}/chapters/update',
                    "delete": f'{api_base_url}/chapters/delete/{chapter_id}',
                    "chapters": f'{api_base_url}/chapters',
                    "plan": f'{api_base_url}/plans/search/by_id/{chapter.plan_id}',
                    "cycles": f'{api_base_url}/cycles/search/by_chapter/{chapter_id}'
                }

                return ShowChapterWithHATEOAS(chapter=chapter_pydantic, links=hateoas_links)

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.warning(f"Изменение данных о главе отменено (Ошибка: {e})")
            raise e


@chapter_router.post("/create", response_model=ShowChapterWithHATEOAS, status_code=201)
async def create_chapter(body: CreateChapter, request: Request, db: AsyncSession = Depends(get_db)):
    return await _create_new_chapter(body, request, db)


@chapter_router.get("/search/by_id/{chapter_id}", response_model=ShowChapterWithHATEOAS, responses={404: {"description": "Раздел не найден"}})
async def get_chapter_by_id(chapter_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_chapter_by_id(chapter_id, request, db)


@chapter_router.get("/search/by_plan/{plan_id}", response_model=ShowChapterListWithHATEOAS, responses={404: {"description": "Главы не найдены"}})
async def get_chapters_by_plan(plan_id: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_chapters_by_plan(plan_id, query_param.page, query_param.limit, request, db)


@chapter_router.get("/search", response_model=ShowChapterListWithHATEOAS)
async def get_all_chapters(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_all_chapters(query_param.page, query_param.limit, request, db)


@chapter_router.delete("/delete/{chapter_id}", response_model=ShowChapterWithHATEOAS, responses={404: {"description": "Раздел не найден"}})
async def delete_chapter(chapter_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _delete_chapter(chapter_id, request, db)


@chapter_router.put("/update", response_model=ShowChapterWithHATEOAS, responses={404: {"description": "Раздел не найден"}})
async def update_chapter(body: UpdateChapter, request: Request, db: AsyncSession = Depends(get_db)):
    return await _update_chapter(body, request, db)


cycle_router = APIRouter()

'''
==============================
CRUD operations for Cycle
==============================
'''

async def _create_new_cycle(body: CreateCycle, request: Request, db) -> ShowCycleWithHATEOAS:
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


async def _get_cycle_by_id(cycle_id: int, request: Request, db) -> ShowCycleWithHATEOAS:
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


async def _get_cycles_by_chapter(chapter_in_plan_id: int, page: int, limit: int, request: Request, db) -> ShowCycleListWithHATEOAS:
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


async def _get_all_cycles(page: int, limit: int, request: Request, db) -> ShowCycleListWithHATEOAS:
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


async def _delete_cycle(cycle_id: int, request: Request, db) -> ShowCycleWithHATEOAS:
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


async def _update_cycle(body: UpdateCycle, request: Request, db) -> ShowCycleWithHATEOAS:
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


@cycle_router.post("/create", response_model=ShowCycleWithHATEOAS, status_code=201)
async def create_cycle(body: CreateCycle, request: Request, db: AsyncSession = Depends(get_db)):
    return await _create_new_cycle(body, request, db)


@cycle_router.get("/search/by_id/{cycle_id}", response_model=ShowCycleWithHATEOAS, responses={404: {"description": "Цикл не найден"}})
async def get_cycle_by_id(cycle_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_cycle_by_id(cycle_id, request, db)


@cycle_router.get("/search/by_chapter/{chapter_in_plan_id}", response_model=ShowCycleListWithHATEOAS, responses={404: {"description": "Циклы не найдены"}})
async def get_cycles_by_chapter(chapter_in_plan_id: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_cycles_by_chapter(chapter_in_plan_id, query_param.page, query_param.limit, request, db)


@cycle_router.get("/search", response_model=ShowCycleListWithHATEOAS)
async def get_all_cycles(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_all_cycles(query_param.page, query_param.limit, request, db)


@cycle_router.delete("/delete/{cycle_id}", response_model=ShowCycleWithHATEOAS, responses={404: {"description": "Цикл не найден"}})
async def delete_cycle(cycle_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _delete_cycle(cycle_id, request, db)


@cycle_router.put("/update", response_model=ShowCycleWithHATEOAS, responses={404: {"description": "Цикл не найден"}})
async def update_cycle(body: UpdateCycle, request: Request, db: AsyncSession = Depends(get_db)):
    return await _update_cycle(body, request, db)


module_router = APIRouter()

'''
==============================
CRUD operations for Module
==============================
'''

async def _create_new_module(body: CreateModule, request: Request, db) -> ShowModuleWithHATEOAS:
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


async def _get_module_by_id(module_id: int, request: Request, db) -> ShowModuleWithHATEOAS:
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


async def _get_modules_by_cycle(cycle_in_chapter_id: int, page: int, limit: int, request: Request, db) -> ShowModuleListWithHATEOAS:
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


async def _get_all_modules(page: int, limit: int, request: Request, db) -> ShowModuleListWithHATEOAS:
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


async def _delete_module(module_id: int, request: Request, db) -> ShowModuleWithHATEOAS:
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


async def _update_module(body: UpdateModule, request: Request, db) -> ShowModuleWithHATEOAS:
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


@module_router.post("/create", response_model=ShowModuleWithHATEOAS, status_code=201)
async def create_module(body: CreateModule, request: Request, db: AsyncSession = Depends(get_db)):
    return await _create_new_module(body, request, db)


@module_router.get("/search/by_id/{module_id}", response_model=ShowModuleWithHATEOAS, responses={404: {"description": "Модуль не найден"}})
async def get_module_by_id(module_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_module_by_id(module_id, request, db)


@module_router.get("/search/by_cycle/{cycle_in_chapter_id}", response_model=ShowModuleListWithHATEOAS, responses={404: {"description": "Модули не найдены"}})
async def get_modules_by_cycle(cycle_in_chapter_id: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_modules_by_cycle(cycle_in_chapter_id, query_param.page, query_param.limit, request, db)


@module_router.get("/search", response_model=ShowModuleListWithHATEOAS)
async def get_all_modules(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_all_modules(query_param.page, query_param.limit, request, db)


@module_router.delete("/delete/{module_id}", response_model=ShowModuleWithHATEOAS, responses={404: {"description": "Модуль не найден"}})
async def delete_module(module_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _delete_module(module_id, request, db)


@module_router.put("/update", response_model=ShowModuleWithHATEOAS, responses={404: {"description": "Модуль не найден"}})
async def update_module(body: UpdateModule, request: Request, db: AsyncSession = Depends(get_db)):
    return await _update_module(body, request, db)


subject_in_cycle_router = APIRouter()

'''
==============================
CRUD operations for SubjectsInCycle
==============================
'''

async def _create_new_subject_in_cycle(body: CreateSubjectsInCycle, request: Request, db) -> ShowSubjectsInCycleWithHATEOAS:
    async with db as session:
        async with session.begin():
            cycle_dal = CycleDAL(session)
            module_dal = ModuleDAL(session)
            subject_in_cycle_dal = SubjectsInCycleDAL(session)
            try:
                if not await ensure_cycle_exists(cycle_dal, body.cycle_in_chapter_id):
                    raise HTTPException(status_code=404, detail=f"Цикл с id {body.cycle_in_chapter_id} не найден")

                if body.module_in_cycle_id is not None:
                    if not await ensure_module_exists(module_dal, body.module_in_cycle_id):
                        raise HTTPException(status_code=404, detail=f"Модуль с id {body.module_in_cycle_id} не найден")
                    
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


async def _get_subject_in_cycle_by_id(subject_in_cycle_id: int, request: Request, db) -> ShowSubjectsInCycleWithHATEOAS:
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


async def _get_subjects_in_cycle_by_cycle(cycle_in_chapter_id: int, page: int, limit: int, request: Request, db) -> ShowSubjectsInCycleListWithHATEOAS:
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


async def _get_subjects_in_cycle_by_module(module_in_cycle_id: int, page: int, limit: int, request: Request, db) -> ShowSubjectsInCycleListWithHATEOAS:
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


async def _get_all_subjects_in_cycles(page: int, limit: int, request: Request, db) -> ShowSubjectsInCycleListWithHATEOAS:
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


async def _delete_subject_in_cycle(subject_in_cycle_id: int, request: Request, db) -> ShowSubjectsInCycleWithHATEOAS:
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


async def _update_subject_in_cycle(body: UpdateSubjectsInCycle, request: Request, db) -> ShowSubjectsInCycleWithHATEOAS:
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


@subject_in_cycle_router.post("/create", response_model=ShowSubjectsInCycleWithHATEOAS, status_code=201)
async def create_subject_in_cycle(body: CreateSubjectsInCycle, request: Request, db: AsyncSession = Depends(get_db)):
    return await _create_new_subject_in_cycle(body, request, db)


@subject_in_cycle_router.get("/search/by_id/{subject_in_cycle_id}", response_model=ShowSubjectsInCycleWithHATEOAS, responses={404: {"description": "Предмет в цикле не найден"}})
async def get_subject_in_cycle_by_id(subject_in_cycle_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_subject_in_cycle_by_id(subject_in_cycle_id, request, db)


@subject_in_cycle_router.get("/search/by_cycle/{cycle_in_chapter_id}", response_model=ShowSubjectsInCycleListWithHATEOAS, responses={404: {"description": "Предметы в цикле не найдены"}})
async def get_subjects_in_cycle_by_cycle(cycle_in_chapter_id: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_subjects_in_cycle_by_cycle(cycle_in_chapter_id, query_param.page, query_param.limit, request, db)


@subject_in_cycle_router.get("/search/by_module/{module_in_cycle_id}", response_model=ShowSubjectsInCycleListWithHATEOAS, responses={404: {"description": "Предметы в цикле не найдены"}})
async def get_subjects_in_cycle_by_module(module_in_cycle_id: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_subjects_in_cycle_by_module(module_in_cycle_id, query_param.page, query_param.limit, request, db)


@subject_in_cycle_router.get("/search", response_model=ShowSubjectsInCycleListWithHATEOAS)
async def get_all_subjects_in_cycles(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_all_subjects_in_cycles(query_param.page, query_param.limit, request, db)


@subject_in_cycle_router.delete("/delete/{subject_in_cycle_id}", response_model=ShowSubjectsInCycleWithHATEOAS, responses={404: {"description": "Предмет в цикле не найден"}})
async def delete_subject_in_cycle(subject_in_cycle_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _delete_subject_in_cycle(subject_in_cycle_id, request, db)


@subject_in_cycle_router.put("/update", response_model=ShowSubjectsInCycleWithHATEOAS, responses={404: {"description": "Предмет в цикле не найден"}})
async def update_subject_in_cycle(body: UpdateSubjectsInCycle, request: Request, db: AsyncSession = Depends(get_db)):
    return await _update_subject_in_cycle(body, request, db)


subject_in_cycle_hours_router = APIRouter()

'''
==============================
CRUD operations for SubjectsInCycleHours
==============================
'''

async def _create_new_subject_in_cycle_hours(body: CreateSubjectsInCycleHours, request: Request, db) -> ShowSubjectsInCycleHoursWithHATEOAS:
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


async def _get_subject_in_cycle_hours_by_id(hours_id: int, request: Request, db) -> ShowSubjectsInCycleHoursWithHATEOAS:
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


async def _get_subjects_in_cycle_hours_by_subject_in_cycle(subject_in_cycle_id: int, page: int, limit: int, request: Request, db) -> ShowSubjectsInCycleHoursListWithHATEOAS:
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
            

async def _get_subjects_in_cycle_hours_by_subject_and_semester(subject_in_cycle_id: int, semester: int, request: Request, db) -> ShowSubjectsInCycleHoursListWithHATEOAS:
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


async def _get_subjects_in_cycle_hours_by_semester(semester: int, page: int, limit: int, request: Request, db) -> ShowSubjectsInCycleHoursListWithHATEOAS:
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


async def _get_all_subjects_in_cycle_hours(page: int, limit: int, request: Request, db) -> ShowSubjectsInCycleHoursListWithHATEOAS:
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


async def _delete_subject_in_cycle_hours(hours_id: int, request: Request, db) -> ShowSubjectsInCycleHoursWithHATEOAS:
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


async def _update_subject_in_cycle_hours(body: UpdateSubjectsInCycleHours, request: Request, db) -> ShowSubjectsInCycleHoursWithHATEOAS:
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


@subject_in_cycle_hours_router.post("/create", response_model=ShowSubjectsInCycleHoursWithHATEOAS, status_code=201)
async def create_subject_in_cycle_hours(body: CreateSubjectsInCycleHours, request: Request, db: AsyncSession = Depends(get_db)):
    return await _create_new_subject_in_cycle_hours(body, request, db)


@subject_in_cycle_hours_router.get("/search/by_id/{hours_id}", response_model=ShowSubjectsInCycleHoursWithHATEOAS, responses={404: {"description": "Запись о часах для предмета не найдена"}})
async def get_subject_in_cycle_hours_by_id(hours_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_subject_in_cycle_hours_by_id(hours_id, request, db)


@subject_in_cycle_hours_router.get("/search/by_subject_in_cycle/{subject_in_cycle_id}", response_model=ShowSubjectsInCycleHoursListWithHATEOAS, responses={404: {"description": "Записи о часах для предмета не найдены"}})
async def get_subjects_in_cycle_hours_by_subject_in_cycle(subject_in_cycle_id: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_subjects_in_cycle_hours_by_subject_in_cycle(subject_in_cycle_id, query_param.page, query_param.limit, request, db)


@subject_in_cycle_hours_router.get("/search/by_subject_and_semester/{subject_in_cycle_id}/{semester}", response_model=ShowSubjectsInCycleHoursListWithHATEOAS, responses={404: {"description": "Записи о часах для предмета в цикле по семестру не найдены"}})
async def get_subjects_in_cycle_hours_by_subject_and_semester(subject_in_cycle_id: int, semester: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_subjects_in_cycle_hours_by_subject_and_semester(subject_in_cycle_id, semester, request, db)


@subject_in_cycle_hours_router.get("/search/by_semester/{semester}", response_model=ShowSubjectsInCycleHoursListWithHATEOAS, responses={404: {"description": "Записи о часах для семестра не найдены"}})
async def get_subjects_in_cycle_hours_by_semester(semester: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_subjects_in_cycle_hours_by_semester(semester, query_param.page, query_param.limit, request, db)


@subject_in_cycle_hours_router.get("/search", response_model=ShowSubjectsInCycleHoursListWithHATEOAS)
async def get_all_subjects_in_cycle_hours(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_all_subjects_in_cycle_hours(query_param.page, query_param.limit, request, db)


@subject_in_cycle_hours_router.delete("/delete/{hours_id}", response_model=ShowSubjectsInCycleHoursWithHATEOAS, responses={404: {"description": "Запись о часах для предмета не найдена"}})
async def delete_subject_in_cycle_hours(hours_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _delete_subject_in_cycle_hours(hours_id, request, db)


@subject_in_cycle_hours_router.put("/update", response_model=ShowSubjectsInCycleHoursWithHATEOAS, responses={404: {"description": "Запись о часах для предмета не найдена"}})
async def update_subject_in_cycle_hours(body: UpdateSubjectsInCycleHours, request: Request, db: AsyncSession = Depends(get_db)):
    return await _update_subject_in_cycle_hours(body, request, db)


certification_router = APIRouter()

'''
==============================
CRUD operations for Certification
==============================
'''

async def _create_new_certification(body: CreateCertification, request: Request, db) -> ShowCertificationWithHATEOAS:
    async with db as session:
        async with session.begin():
            subject_in_cycle_hours_dal = SubjectsInCycleHoursDAL(session)
            certification_dal = CertificationDAL(session)
            try:
                if not await ensure_subject_in_cycle_hours_exists(subject_in_cycle_hours_dal, body.id):
                    raise HTTPException(status_code=404, detail=f"Запись о часах для предмета в цикле с id {body.id} не найдена")

                certification = await certification_dal.create_certification(
                    id=body.id,
                    credit=body.credit,
                    differentiated_credit=body.differentiated_credit,
                    course_project=body.course_project,
                    course_work=body.course_work,
                    control_work=body.control_work,
                    other_form=body.other_form
                )
                certification_id = certification.id
                certification_pydantic = ShowCertification.model_validate(certification, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/certifications/search/by_id/{certification_id}',
                    "update": f'{api_base_url}/certifications/update',
                    "delete": f'{api_base_url}/certifications/delete/{certification_id}',
                    "certifications": f'{api_base_url}/certifications',
                    "subjects_in_cycle_hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_id/{certification_id}'
                }

                return ShowCertificationWithHATEOAS(certification=certification_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при создании сертификации для id {body.id}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_certification_by_id(certification_id: int, request: Request, db) -> ShowCertificationWithHATEOAS:
    async with db as session:
        async with session.begin():
            certification_dal = CertificationDAL(session)
            try:
                certification = await certification_dal.get_certification_by_id(certification_id)
                if not certification:
                    raise HTTPException(status_code=404, detail=f"Сертификация с id {certification_id} не найдена")
                certification_pydantic = ShowCertification.model_validate(certification, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/certifications/search/by_id/{certification_id}',
                    "update": f'{api_base_url}/certifications/update',
                    "delete": f'{api_base_url}/certifications/delete/{certification_id}',
                    "certifications": f'{api_base_url}/certifications',
                    "subjects_in_cycle_hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_id/{certification_id}'
                }

                return ShowCertificationWithHATEOAS(certification=certification_pydantic, links=hateoas_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Получение сертификации {certification_id} отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_all_certifications(page: int, limit: int, request: Request, db) -> ShowCertificationListWithHATEOAS:
    async with db as session:
        async with session.begin():
            certification_dal = CertificationDAL(session)
            try:
                certifications = await certification_dal.get_all_certifications(page, limit)
                if certifications is None:
                    certifications = []

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                certifications_with_hateoas = []
                for certification in certifications:
                    certification_pydantic = ShowCertification.model_validate(certification, from_attributes=True)
                    certification_id = certification.id
                    certification_links = {
                        "self": f'{api_base_url}/certifications/search/by_id/{certification_id}',
                        "update": f'{api_base_url}/certifications/update',
                        "delete": f'{api_base_url}/certifications/delete/{certification_id}',
                        "certifications": f'{api_base_url}/certifications',
                        "subjects_in_cycle_hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_id/{certification_id}'
                    }
                    certification_with_links = ShowCertificationWithHATEOAS(certification=certification_pydantic, links=certification_links)
                    certifications_with_hateoas.append(certification_with_links)

                collection_links = {
                    "self": f'{api_base_url}/certifications/search?page={page}&limit={limit}',
                    "create": f'{api_base_url}/certifications/create'
                }
                collection_links = {k: v for k, v in collection_links.items() if v is not None}

                return ShowCertificationListWithHATEOAS(certifications=certifications_with_hateoas, links=collection_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Получение сертификаций отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _delete_certification(certification_id: int, request: Request, db) -> ShowCertificationWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                certification_dal = CertificationDAL(session)
                
                if not await ensure_certification_exists(certification_dal, certification_id):
                    raise HTTPException(status_code=404, detail=f"Сертификация с id {certification_id} не найдена")

                certification = await certification_dal.delete_certification(certification_id)
                
                if not certification:
                    raise HTTPException(status_code=404, detail=f"Сертификация с id {certification_id} не найдена")

                certification_pydantic = ShowCertification.model_validate(certification, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "certifications": f'{api_base_url}/certifications',
                    "create": f'{api_base_url}/certifications/create',
                    "subjects_in_cycle_hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_id/{certification_id}'
                }
                hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                return ShowCertificationWithHATEOAS(certification=certification_pydantic, links=hateoas_links)

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Неожиданная ошибка при удалении сертификации {certification_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении сертификации.")


async def _update_certification(body: UpdateCertification, request: Request, db) -> ShowCertificationWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["certification_id"]}

                certification_dal = CertificationDAL(session)

                if not await ensure_certification_exists(certification_dal, body.certification_id):
                    raise HTTPException(status_code=404, detail=f"Сертификация с id {body.certification_id} не найдена")

                certification = await certification_dal.update_certification(target_id=body.certification_id, **update_data)
                if not certification:
                    raise HTTPException(status_code=404, detail=f"Сертификация с id {body.certification_id} не найдена")

                certification_id = certification.id
                certification_pydantic = ShowCertification.model_validate(certification, from_attributes=True)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/certifications/search/by_id/{certification_id}',
                    "update": f'{api_base_url}/certifications/update',
                    "delete": f'{api_base_url}/certifications/delete/{certification_id}',
                    "certifications": f'{api_base_url}/certifications',
                    "subjects_in_cycle_hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_id/{certification_id}'
                }

                return ShowCertificationWithHATEOAS(certification=certification_pydantic, links=hateoas_links)

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.warning(f"Изменение данных о сертификации отменено (Ошибка: {e})")
            raise e


@certification_router.post("/create", response_model=ShowCertificationWithHATEOAS, status_code=201)
async def create_certification(body: CreateCertification, request: Request, db: AsyncSession = Depends(get_db)):
    return await _create_new_certification(body, request, db)


@certification_router.get("/search/by_id/{certification_id}", response_model=ShowCertificationWithHATEOAS, responses={404: {"description": "Сертификация не найдена"}})
async def get_certification_by_id(certification_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_certification_by_id(certification_id, request, db)


@certification_router.get("/search", response_model=ShowCertificationListWithHATEOAS)
async def get_all_certifications(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_all_certifications(query_param.page, query_param.limit, request, db)


@certification_router.delete("/delete/{certification_id}", response_model=ShowCertificationWithHATEOAS, responses={404: {"description": "Сертификация не найдена"}})
async def delete_certification(certification_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _delete_certification(certification_id, request, db)


@certification_router.put("/update", response_model=ShowCertificationWithHATEOAS, responses={404: {"description": "Сертификация не найдена"}})
async def update_certification(body: UpdateCertification, request: Request, db: AsyncSession = Depends(get_db)):
    return await _update_certification(body, request, db)


teacher_in_plan_router = APIRouter()

'''
==============================
CRUD operations for TeacherInPlan
==============================
'''

async def _create_new_teacher_in_plan(body: CreateTeacherInPlan, request: Request, db) -> ShowTeacherInPlanWithHATEOAS:
    async with db as session:
        async with session.begin():
            subjects_in_cycle_hours_dal = SubjectsInCycleHoursDAL(session)
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


async def _get_teacher_in_plan_by_id(teacher_in_plan_id: int, request: Request, db) -> ShowTeacherInPlanWithHATEOAS:
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


async def _get_teachers_in_plans_by_teacher(teacher_id: int, page: int, limit: int, request: Request, db) -> ShowTeacherInPlanListWithHATEOAS:
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


async def _get_teachers_in_plans_by_group(group_name: str, page: int, limit: int, request: Request, db) -> ShowTeacherInPlanListWithHATEOAS:
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


async def _get_teachers_in_plans_by_subject_hours(subject_hours_id: int, page: int, limit: int, request: Request, db) -> ShowTeacherInPlanListWithHATEOAS:
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


async def _get_teachers_in_plans_by_session_type(session_type: str, page: int, limit: int, request: Request, db) -> ShowTeacherInPlanListWithHATEOAS:
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


async def _get_all_teachers_in_plans(page: int, limit: int, request: Request, db) -> ShowTeacherInPlanListWithHATEOAS:
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


async def _delete_teacher_in_plan(teacher_in_plan_id: int, request: Request, db) -> ShowTeacherInPlanWithHATEOAS:
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


async def _update_teacher_in_plan(body: UpdateTeacherInPlan, request: Request, db) -> ShowTeacherInPlanWithHATEOAS:
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


@teacher_in_plan_router.post("/create", response_model=ShowTeacherInPlanWithHATEOAS, status_code=201)
async def create_teacher_in_plan(body: CreateTeacherInPlan, request: Request, db: AsyncSession = Depends(get_db)):
    return await _create_new_teacher_in_plan(body, request, db)


@teacher_in_plan_router.get("/search/by_id/{teacher_in_plan_id}", response_model=ShowTeacherInPlanWithHATEOAS, responses={404: {"description": "Запись в расписании преподавателя не найдена"}})
async def get_teacher_in_plan_by_id(teacher_in_plan_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_teacher_in_plan_by_id(teacher_in_plan_id, request, db)


@teacher_in_plan_router.get("/search/by_teacher/{teacher_id}", response_model=ShowTeacherInPlanListWithHATEOAS, responses={404: {"description": "Записи в расписании преподавателя не найдены"}})
async def get_teachers_in_plans_by_teacher(teacher_id: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_teachers_in_plans_by_teacher(teacher_id, query_param.page, query_param.limit, request, db)


@teacher_in_plan_router.get("/search/by_group/{group_name}", response_model=ShowTeacherInPlanListWithHATEOAS, responses={404: {"description": "Записи в расписании преподавателя не найдены"}})
async def get_teachers_in_plans_by_group(group_name: str, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_teachers_in_plans_by_group(group_name, query_param.page, query_param.limit, request, db)


@teacher_in_plan_router.get("/search/by_subject_hours/{subject_hours_id}", response_model=ShowTeacherInPlanListWithHATEOAS, responses={404: {"description": "Записи в расписании преподавателя не найдены"}})
async def get_teachers_in_plans_by_subject_hours(subject_hours_id: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_teachers_in_plans_by_subject_hours(subject_hours_id, query_param.page, query_param.limit, request, db)


@teacher_in_plan_router.get("/search/by_session_type/{session_type}", response_model=ShowTeacherInPlanListWithHATEOAS, responses={404: {"description": "Записи в расписании преподавателя не найдены"}})
async def get_teachers_in_plans_by_session_type(session_type: str, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_teachers_in_plans_by_session_type(session_type, query_param.page, query_param.limit, request, db)


@teacher_in_plan_router.get("/search", response_model=ShowTeacherInPlanListWithHATEOAS)
async def get_all_teachers_in_plans(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_all_teachers_in_plans(query_param.page, query_param.limit, request, db)


@teacher_in_plan_router.delete("/delete/{teacher_in_plan_id}", response_model=ShowTeacherInPlanWithHATEOAS, responses={404: {"description": "Запись в расписании преподавателя не найдена"}})
async def delete_teacher_in_plan(teacher_in_plan_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _delete_teacher_in_plan(teacher_in_plan_id, request, db)


@teacher_in_plan_router.put("/update", response_model=ShowTeacherInPlanWithHATEOAS, responses={404: {"description": "Запись в расписании преподавателя не найдена"}})
async def update_teacher_in_plan(body: UpdateTeacherInPlan, request: Request, db: AsyncSession = Depends(get_db)):
    return await _update_teacher_in_plan(body, request, db)


teacher_building_router = APIRouter()

'''
==============================
CRUD operations for TeacherBuilding
==============================
'''

async def _create_new_teacher_building(body: CreateTeacherBuilding, request: Request, db) -> ShowTeacherBuildingWithHATEOAS:
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


async def _get_teacher_building_by_id(teacher_building_id: int, request: Request, db) -> ShowTeacherBuildingWithHATEOAS:
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


async def _get_teachers_buildings_by_teacher(teacher_id: int, page: int, limit: int, request: Request, db) -> ShowTeacherBuildingListWithHATEOAS:
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


async def _get_teachers_buildings_by_building(building_number: int, page: int, limit: int, request: Request, db) -> ShowTeacherBuildingListWithHATEOAS:
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


async def _get_all_teachers_buildings(page: int, limit: int, request: Request, db) -> ShowTeacherBuildingListWithHATEOAS:
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


async def _delete_teacher_building(teacher_building_id: int, request: Request, db) -> ShowTeacherBuildingWithHATEOAS:
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


async def _update_teacher_building(body: UpdateTeacherBuilding, request: Request, db) -> ShowTeacherBuildingWithHATEOAS:
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


@teacher_building_router.post("/create", response_model=ShowTeacherBuildingWithHATEOAS, status_code=201)
async def create_teacher_building(body: CreateTeacherBuilding, request: Request, db: AsyncSession = Depends(get_db)):
    return await _create_new_teacher_building(body, request, db)


@teacher_building_router.get("/search/by_id/{teacher_building_id}", response_model=ShowTeacherBuildingWithHATEOAS, responses={404: {"description": "Связь преподавателя и здания не найдена"}})
async def get_teacher_building_by_id(teacher_building_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_teacher_building_by_id(teacher_building_id, request, db)


@teacher_building_router.get("/search/by_teacher/{teacher_id}", response_model=ShowTeacherBuildingListWithHATEOAS, responses={404: {"description": "Связи преподавателя и зданий не найдены"}})
async def get_teachers_buildings_by_teacher(teacher_id: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_teachers_buildings_by_teacher(teacher_id, query_param.page, query_param.limit, request, db)


@teacher_building_router.get("/search/by_building/{building_number}", response_model=ShowTeacherBuildingListWithHATEOAS, responses={404: {"description": "Связи преподавателей и здания не найдены"}})
async def get_teachers_buildings_by_building(building_number: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_teachers_buildings_by_building(building_number, query_param.page, query_param.limit, request, db)


@teacher_building_router.get("/search", response_model=ShowTeacherBuildingListWithHATEOAS)
async def get_all_teachers_buildings(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_all_teachers_buildings(query_param.page, query_param.limit, request, db)


@teacher_building_router.delete("/delete/{teacher_building_id}", response_model=ShowTeacherBuildingWithHATEOAS, responses={404: {"description": "Связь преподавателя и здания не найдена"}})
async def delete_teacher_building(teacher_building_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _delete_teacher_building(teacher_building_id, request, db)


@teacher_building_router.put("/update", response_model=ShowTeacherBuildingWithHATEOAS, responses={404: {"description": "Связь преподавателя и здания не найдена"}})
async def update_teacher_building(body: UpdateTeacherBuilding, request: Request, db: AsyncSession = Depends(get_db)):
    return await _update_teacher_building(body, request, db)


stream_router = APIRouter()

'''
==============================
CRUD operations for Stream
==============================
'''

async def _create_new_stream(body: CreateStream, request: Request, db) -> ShowStreamWithHATEOAS:
    async with db as session:
        async with session.begin():
            group_dal = GroupDAL(session)
            subject_in_cycle_dal = SubjectsInCycleDAL(session)
            stream_dal = StreamDAL(session)
            try:
                if not await ensure_group_exists(group_dal, body.group_name):
                    raise HTTPException(status_code=404, detail=f"Группа с названием {body.group_name} не найдена")
                if not await ensure_subject_in_cycle_exists(subject_in_cycle_dal, body.subject_id):
                    raise HTTPException(status_code=404, detail=f"Предмет в цикле с id {body.subject_id} не найден")

                if not await ensure_stream_unique(stream_dal, body.stream_id, body.group_name, body.subject_id):
                    raise HTTPException(status_code=400, detail=f"Поток с id {body.stream_id}, группой {body.group_name} и предметом {body.subject_id} уже существует")

                stream = await stream_dal.create_stream(
                    stream_id=body.stream_id,
                    group_name=body.group_name,
                    subject_id=body.subject_id
                )
                stream_id = stream.stream_id
                group_name = stream.group_name
                subject_id = stream.subject_id
                
                stream_dict = {
                    "stream_id": stream.stream_id,
                    "group_name": stream.group_name,
                    "subject_id": stream.subject_id,
                }
                stream_pydantic = ShowStream.model_validate(stream_dict)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/streams/search/by_composite_key/{stream_id}/{group_name}/{subject_id}',
                    "update": f'{api_base_url}/streams/update',
                    "delete": f'{api_base_url}/streams/delete/{stream_id}/{group_name}/{subject_id}',
                    "streams": f'{api_base_url}/streams',
                    "group": f'{api_base_url}/groups/search/by_group_name/{group_name}',
                    "subject": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_id}',
                    "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}' 
                }

                return ShowStreamWithHATEOAS(stream=stream_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при создании потока: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_stream_by_composite_key(stream_id: int, group_name: str, subject_id: int, request: Request, db) -> ShowStreamWithHATEOAS:
    async with db as session:
        async with session.begin():
            stream_dal = StreamDAL(session)
            try:
                stream = await stream_dal.get_stream_by_composite_key(stream_id, group_name, subject_id)
                if not stream:
                    raise HTTPException(status_code=404, detail=f"Поток с id {stream_id}, группой {group_name} и предметом {subject_id} не найден")

                stream_dict = {
                    "stream_id": stream.stream_id,
                    "group_name": stream.group_name,
                    "subject_id": stream.subject_id,
                }
                stream_pydantic = ShowStream.model_validate(stream_dict)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/streams/search/by_composite_key/{stream_id}/{group_name}/{subject_id}',
                    "update": f'{api_base_url}/streams/update',
                    "delete": f'{api_base_url}/streams/delete/{stream_id}/{group_name}/{subject_id}',
                    "streams": f'{api_base_url}/streams',
                    "group": f'{api_base_url}/groups/search/by_group_name/{group_name}',
                    "subject": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_id}',
                    "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}'
                }

                return ShowStreamWithHATEOAS(stream=stream_pydantic, links=hateoas_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Получение потока {stream_id} для группы {group_name} и предмета {subject_id} отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_streams_by_group(group_name: str, page: int, limit: int, request: Request, db) -> ShowStreamListWithHATEOAS:
    async with db as session:
        async with session.begin():
            group_dal = GroupDAL(session)
            stream_dal = StreamDAL(session)
            try:
                if not await ensure_group_exists(group_dal, group_name):
                    raise HTTPException(status_code=404, detail=f"Группа с названием {group_name} не найдена")

                streams = await stream_dal.get_streams_by_group(group_name, page, limit)
                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                streams_with_hateoas = []
                for stream in streams:
                    stream_dict = {
                        "stream_id": stream.stream_id,
                        "group_name": stream.group_name,
                        "subject_id": stream.subject_id,
                    }
                    stream_pydantic = ShowStream.model_validate(stream_dict)
                    stream_id = stream.stream_id
                    subject_id = stream.subject_id
                    stream_links = {
                        "self": f'{api_base_url}/streams/search/by_composite_key/{stream_id}/{group_name}/{subject_id}',
                        "update": f'{api_base_url}/streams/update',
                        "delete": f'{api_base_url}/streams/delete/{stream_id}/{group_name}/{subject_id}',
                        "streams": f'{api_base_url}/streams',
                        "group": f'{api_base_url}/groups/search/by_group_name/{group_name}',
                        "subject": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_id}',
                        "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}'
                    }
                    stream_with_links = ShowStreamWithHATEOAS(stream=stream_pydantic, links=stream_links)
                    streams_with_hateoas.append(stream_with_links)

                collection_links = {
                    "self": f'{api_base_url}/streams/search/by_group/{group_name}?page={page}&limit={limit}',
                    "create": f'{api_base_url}/streams/create',
                    "group": f'{api_base_url}/groups/search/by_group_name/{group_name}'
                }
                collection_links = {k: v for k, v in collection_links.items() if v is not None}

                return ShowStreamListWithHATEOAS(streams=streams_with_hateoas, links=collection_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Получение потоков для группы {group_name} отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_streams_by_subject(subject_id: int, page: int, limit: int, request: Request, db) -> ShowStreamListWithHATEOAS:
    async with db as session:
        async with session.begin():
            subject_in_cycle_dal = SubjectsInCycleDAL(session)
            stream_dal = StreamDAL(session)
            try:
                if not await ensure_subject_in_cycle_exists(subject_in_cycle_dal, subject_id):
                    raise HTTPException(status_code=404, detail=f"Предмет в цикле с id {subject_id} не найден")

                streams = await stream_dal.get_streams_by_subject(subject_id, page, limit)
                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                streams_with_hateoas = []
                for stream in streams:
                    stream_dict = {
                        "stream_id": stream.stream_id,
                        "group_name": stream.group_name,
                        "subject_id": stream.subject_id,
                    }
                    stream_pydantic = ShowStream.model_validate(stream_dict)
                    stream_id = stream.stream_id
                    group_name = stream.group_name
                    stream_links = {
                        "self": f'{api_base_url}/streams/search/by_composite_key/{stream_id}/{group_name}/{subject_id}',
                        "update": f'{api_base_url}/streams/update',
                        "delete": f'{api_base_url}/streams/delete/{stream_id}/{group_name}/{subject_id}',
                        "streams": f'{api_base_url}/streams',
                        "group": f'{api_base_url}/groups/search/by_group_name/{group_name}',
                        "subject": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_id}',
                        "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}'
                    }
                    stream_with_links = ShowStreamWithHATEOAS(stream=stream_pydantic, links=stream_links)
                    streams_with_hateoas.append(stream_with_links)

                collection_links = {
                    "self": f'{api_base_url}/streams/search/by_subject/{subject_id}?page={page}&limit={limit}',
                    "create": f'{api_base_url}/streams/create',
                    "subject": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_id}'
                }
                collection_links = {k: v for k, v in collection_links.items() if v is not None}

                return ShowStreamListWithHATEOAS(streams=streams_with_hateoas, links=collection_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Получение потоков для предмета в цикле {subject_id} отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_all_streams(page: int, limit: int, request: Request, db) -> ShowStreamListWithHATEOAS:
    async with db as session:
        async with session.begin():
            stream_dal = StreamDAL(session)
            try:
                streams = await stream_dal.get_all_streams(page, limit)
                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                streams_with_hateoas = []
                for stream in streams:
                    stream_dict = {
                        "stream_id": stream.stream_id,
                        "group_name": stream.group_name,
                        "subject_id": stream.subject_id,
                    }
                    stream_pydantic = ShowStream.model_validate(stream_dict)
                    stream_id = stream.stream_id
                    group_name = stream.group_name
                    subject_id = stream.subject_id
                    stream_links = {
                        "self": f'{api_base_url}/streams/search/by_composite_key/{stream_id}/{group_name}/{subject_id}',
                        "update": f'{api_base_url}/streams/update',
                        "delete": f'{api_base_url}/streams/delete/{stream_id}/{group_name}/{subject_id}',
                        "streams": f'{api_base_url}/streams',
                        "group": f'{api_base_url}/groups/search/by_group_name/{group_name}',
                        "subject": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_id}',
                        "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}'
                    }
                    stream_with_links = ShowStreamWithHATEOAS(stream=stream_pydantic, links=stream_links)
                    streams_with_hateoas.append(stream_with_links)

                collection_links = {
                    "self": f'{api_base_url}/streams/search?page={page}&limit={limit}',
                    "create": f'{api_base_url}/streams/create'
                }
                collection_links = {k: v for k, v in collection_links.items() if v is not None}

                return ShowStreamListWithHATEOAS(streams=streams_with_hateoas, links=collection_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Получение потоков отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _delete_stream(stream_id: int, group_name: str, subject_id: int, request: Request, db) -> ShowStreamWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                stream_dal = StreamDAL(session)

                stream = await stream_dal.get_stream_by_composite_key(stream_id, group_name, subject_id)
                if not stream:
                    raise HTTPException(status_code=404, detail=f"Поток с id {stream_id}, группой {group_name} и предметом {subject_id} не найден")

                deleted_stream = await stream_dal.delete_stream(stream_id, group_name, subject_id)
                
                if not deleted_stream:
                    raise HTTPException(status_code=404, detail=f"Поток с id {stream_id}, группой {group_name} и предметом {subject_id} не найден")

                stream_dict = {
                    "stream_id": deleted_stream.stream_id,
                    "group_name": deleted_stream.group_name,
                    "subject_id": deleted_stream.subject_id,
                }
                stream_pydantic = ShowStream.model_validate(stream_dict)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "streams": f'{api_base_url}/streams',
                    "create": f'{api_base_url}/streams/create'
                }
                hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                return ShowStreamWithHATEOAS(stream=stream_pydantic, links=hateoas_links)

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Неожиданная ошибка при удалении потока {stream_id} для группы {group_name} и предмета {subject_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении потока.")


async def _update_stream(body: UpdateStream, request: Request, db) -> ShowStreamWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["stream_id", "group_name", "subject_id", "new_stream_id", "new_group_name", "new_subject_id"]}

                target_stream_id = body.stream_id
                target_group_name = body.group_name
                target_subject_id = body.subject_id
                if body.new_stream_id is not None:
                    update_data["stream_id"] = body.new_stream_id
                    target_stream_id = body.new_stream_id
                if body.new_group_name is not None:
                    update_data["group_name"] = body.new_group_name
                    target_group_name = body.new_group_name
                if body.new_subject_id is not None:
                    update_data["subject_id"] = body.new_subject_id
                    target_subject_id = body.new_subject_id

                if "group_name" in update_data:
                    group_dal = GroupDAL(session)
                    if not await ensure_group_exists(group_dal, update_data["group_name"]):
                        raise HTTPException(status_code=404, detail=f"Группа с названием {update_data['group_name']} не найдена")
                if "subject_id" in update_data:
                    subject_in_cycle_dal = SubjectsInCycleDAL(session)
                    if not await ensure_subject_in_cycle_exists(subject_in_cycle_dal, update_data["subject_id"]):
                        raise HTTPException(status_code=404, detail=f"Предмет в цикле с id {update_data['subject_id']} не найден")

                stream_dal = StreamDAL(session)

                stream = await stream_dal.get_stream_by_composite_key(body.stream_id, body.group_name, body.subject_id)
                if not stream:
                    raise HTTPException(status_code=404, detail=f"Поток с id {body.stream_id}, группой {body.group_name} и предметом {body.subject_id} не найден")

                if (target_stream_id, target_group_name, target_subject_id) != (body.stream_id, body.group_name, body.subject_id):
                    if not await ensure_stream_unique(stream_dal, target_stream_id, target_group_name, target_subject_id):
                        raise HTTPException(status_code=400, detail=f"Поток с id {target_stream_id}, группой {target_group_name} и предметом {target_subject_id} уже существует")

                updated_stream = await stream_dal.update_stream(target_stream_id=body.stream_id, target_group_name=body.group_name, target_subject_id=body.subject_id, **update_data)
                if not updated_stream:
                    raise HTTPException(status_code=404, detail=f"Поток с id {body.stream_id}, группой {body.group_name} и предметом {body.subject_id} не найден")

                stream_id = updated_stream.stream_id
                group_name = updated_stream.group_name
                subject_id = updated_stream.subject_id
                
                stream_dict = {
                    "stream_id": updated_stream.stream_id,
                    "group_name": updated_stream.group_name,
                    "subject_id": updated_stream.subject_id,
                }
                stream_pydantic = ShowStream.model_validate(stream_dict)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = ''
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/streams/search/by_composite_key/{stream_id}/{group_name}/{subject_id}',
                    "update": f'{api_base_url}/streams/update',
                    "delete": f'{api_base_url}/streams/delete/{stream_id}/{group_name}/{subject_id}',
                    "streams": f'{api_base_url}/streams',
                    "group": f'{api_base_url}/groups/search/by_group_name/{group_name}',
                    "subject": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_id}',
                    "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}'
                }

                return ShowStreamWithHATEOAS(stream=stream_pydantic, links=hateoas_links)

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.warning(f"Изменение данных о потоке отменено (Ошибка: {e})")
            raise e


@stream_router.post("/create", response_model=ShowStreamWithHATEOAS, status_code=201)
async def create_stream(body: CreateStream, request: Request, db: AsyncSession = Depends(get_db)):
    return await _create_new_stream(body, request, db)


@stream_router.get("/search/by_composite_key/{stream_id}/{group_name}/{subject_id}", response_model=ShowStreamWithHATEOAS, responses={404: {"description": "Поток не найден"}})
async def get_stream_by_composite_key(stream_id: int, group_name: str, subject_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_stream_by_composite_key(stream_id, group_name, subject_id, request, db)


@stream_router.get("/search/by_group/{group_name}", response_model=ShowStreamListWithHATEOAS, responses={404: {"description": "Потоки не найдены"}})
async def get_streams_by_group(group_name: str, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_streams_by_group(group_name, query_param.page, query_param.limit, request, db)


@stream_router.get("/search/by_subject/{subject_id}", response_model=ShowStreamListWithHATEOAS, responses={404: {"description": "Потоки не найдены"}})
async def get_streams_by_subject(subject_id: int, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_streams_by_subject(subject_id, query_param.page, query_param.limit, request, db)


@stream_router.get("/search", response_model=ShowStreamListWithHATEOAS)
async def get_all_streams(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_all_streams(query_param.page, query_param.limit, request, db)


@stream_router.delete("/delete/{stream_id}/{group_name}/{subject_id}", response_model=ShowStreamWithHATEOAS, responses={404: {"description": "Поток не найден"}})
async def delete_stream(stream_id: int, group_name: str, subject_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _delete_stream(stream_id, group_name, subject_id, request, db)


@stream_router.put("/update", response_model=ShowStreamWithHATEOAS, responses={404: {"description": "Поток не найден"}})
async def update_stream(body: UpdateStream, request: Request, db: AsyncSession = Depends(get_db)):
    return await _update_stream(body, request, db)