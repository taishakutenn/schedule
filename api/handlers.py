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
from api.services_helpers import ensure_building_exists, ensure_cabinet_unique, ensure_group_unique, ensure_speciality_exists, ensure_teacher_exists, ensure_group_exists, ensure_subject_exists, ensure_curriculum_unique, ensure_subject_unique, ensure_employment_unique, ensure_request_unique, ensure_session_unique, ensure_cabinet_exists
from db.dals import TeacherDAL, BuildingDAL, CabinetDAL, SpecialityDAL, GroupDAL, CurriculumDAL, SubjectDAL, EmployTeacherDAL, TeacherRequestDAL, SessionDAL
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


'''
===========================
CRUD operations for Teacher
===========================
'''


async def _create_new_teacher(body: CreateTeacher, request: Request, db) -> ShowTeacherWithHATEOAS:
    async with db as session:
        async with session.begin():
            teacher_dal = TeacherDAL(session)

            try:
                teacher = await teacher_dal.create_teacher(
                    name=body.name,
                    surname=body.surname,
                    phone_number=body.phone_number,
                    email=str(body.email),
                    fathername=body.fathername
                )

                teacher_id = teacher.id
                teacher_pydantic = ShowTeacher.model_validate(teacher)

                # Add HATEOAS
                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/teachers/search/by_id/{teacher_id}',
                    "update": f'{api_base_url}/teachers/update/{teacher_id}',
                    "delete": f'{api_base_url}/teachers/delete/{teacher_id}',
                    "teachers": f'{api_base_url}/teachers',
                    "group": f'{api_base_url}/groups/search/by_teacher/{teacher_id}',
                    "sessions": f'{api_base_url}/sessions/search/by_teacher/{teacher_id}',
                    "employments": f'{api_base_url}/employments/search/by_teacher/{teacher_id}',
                    "requests": f'{api_base_url}/requests/search/by_teacher/{teacher_id}'
                }

                return ShowTeacherWithHATEOAS(teacher=teacher_pydantic, links=hateoas_links)
            
            except IntegrityError as e:
                await session.rollback()
                error_msg = str(e.orig).lower()
                if "email" in error_msg and 'already_exists' in error_msg:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Преподаватель с таким email уже существует.")
                elif "phone_number" in error_msg and 'already_exists' in error_msg:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Преподаватель с таким номером телефона уже существует.")
                else:
                    logger.error(f"Ошибка целостности БД при создании преподавателя: {e}")
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Невозможно создать преподавателя из-за конфликта данных.")
            
            except HTTPException:
                raise

            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при создании преподавателя: {e}", exc_info=True)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка сервера.")
    

async def _get_teacher_by_id(teacher_id, request: Request, db) -> ShowTeacherWithHATEOAS:
    async with db as session:
        async with session.begin():
            teacher_dal = TeacherDAL(session)
            try: 
                teacher = await teacher_dal.get_teacher_by_id(teacher_id)

                # if teacher doesn't exist
                if not teacher:
                    raise HTTPException(status_code=404, detail=f"Преподаватель с id: {teacher_id} не найден")
                
                teacher_pydantic = ShowTeacher.model_validate(teacher)

                # Add HATEOAS
                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/teachers/search/by_id/{teacher_id}',
                    "update": f'{api_base_url}/teachers/update/{teacher_id}',
                    "delete": f'{api_base_url}/teachers/delete/{teacher_id}',
                    "teachers": f'{api_base_url}/teachers',
                    "group": f'{api_base_url}/groups/search/by_teacher/{teacher_id}',
                    "sessions": f'{api_base_url}/sessions/search/by_teacher/{teacher_id}',
                    "employments": f'{api_base_url}/employments/search/by_teacher/{teacher_id}',
                    "requests": f'{api_base_url}/requests/search/by_teacher/{teacher_id}'
                }

                return ShowTeacherWithHATEOAS(teacher=teacher_pydantic, links=hateoas_links)
            
            except HTTPException:
                raise

            except Exception as e:
                logger.warning(f"Получение преподавателя отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_teacher_by_name_and_surname(name, surname, request: Request, db) -> ShowTeacherWithHATEOAS:
    async with db as session:
        async with session.begin():
            teacher_dal = TeacherDAL(session)
            try:
                teacher = await teacher_dal.get_teacher_by_name_surname(name, surname)

                # if teacher exist
                if not teacher:
                    raise HTTPException(status_code=404, detail=f"Преподаватель {name, surname} не найден")

                teacher_pydantic = ShowTeacher.model_validate(teacher)
                teacher_id = teacher.id

                # Add HATEOAS
                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/teachers/search/{teacher_id}',
                    "update": f'{api_base_url}/teachers/update/{teacher_id}',
                    "delete": f'{api_base_url}/teachers/delete/{teacher_id}',
                    "teachers": f'{api_base_url}/teachers',
                    "group": f'{api_base_url}/groups/search/by_teacher/{teacher_id}',
                    "sessions": f'{api_base_url}/sessions/search/by_teacher/{teacher_id}',
                    "employments": f'{api_base_url}/employments/search/by_teacher/{teacher_id}',
                    "requests": f'{api_base_url}/requests/search/by_teacher/{teacher_id}'
                }

                return ShowTeacherWithHATEOAS(teacher=teacher_pydantic, links=hateoas_links)
            
            except HTTPException:
                raise

            except Exception as e:
                logger.warning(f"Получение преподавателя отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_all_teachers(page: int, limit: int, request: Request, db) -> ShowTeacherListWithHATEOAS:
    async with db as session:
        async with session.begin():
            teacher_dal = TeacherDAL(session)
            try:
                teachers = await teacher_dal.get_all_teachers(page, limit)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                teachers_with_hateoas = []
                for teacher in teachers:
                    teacher_pydantic = ShowTeacher.model_validate(teacher)

                    # add HATEOAS
                    teacher_id = teacher.id
                    teacher_links = {
                        "self": f'{api_base_url}/teachers/search/by_id/{teacher_id}',
                        "update": f'{api_base_url}/teachers/update/{teacher_id}',
                        "delete": f'{api_base_url}/teachers/delete/{teacher_id}',
                        "group": f'{api_base_url}/groups/search/by_teacher/{teacher_id}',
                        "sessions": f'{api_base_url}/sessions/search/by_teacher/{teacher_id}',
                        "employments": f'{api_base_url}/employments/search/by_teacher/{teacher_id}',
                        "requests": f'{api_base_url}/requests/search/by_teacher/{teacher_id}'
                    }

                    teacher_with_links = ShowTeacherWithHATEOAS(
                        teacher=teacher_pydantic,
                        links=teacher_links
                    )
                    teachers_with_hateoas.append(teacher_with_links)

                collection_links = {
                    "self": f'{api_base_url}/teachers?page={page}&limit={limit}',
                    "create": f'{api_base_url}/teachers/create'
                }
                collection_links = {k: v for k, v in collection_links.items() if v is not None}

                return ShowTeacherListWithHATEOAS(
                    teachers=teachers_with_hateoas,
                    links=collection_links
                )
            
            except HTTPException:
                raise

            except Exception as e:
                logger.warning(f"Получение преподавателей отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")
            

async def _get_all_teachers(page: int, limit: int, group_name, request: Request, db) -> ShowTeacherListWithHATEOAS:
    async with db as session:
        async with session.begin():
            teacher_dal = TeacherDAL(session)
            try:
                teachers = await teacher_dal.get_all_teachers_by_group(page, limit, group_name)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                teachers_with_hateoas = []
                for teacher in teachers:
                    teacher_pydantic = ShowTeacher.model_validate(teacher)

                    # add HATEOAS
                    teacher_id = teacher.id
                    teacher_links = {
                        "self": f'{api_base_url}/teachers/search/by_id/{teacher_id}',
                        "update": f'{api_base_url}/teachers/update/{teacher_id}',
                        "delete": f'{api_base_url}/teachers/delete/{teacher_id}',
                        "group": f'{api_base_url}/groups/search/by_teacher/{teacher_id}',
                        "sessions": f'{api_base_url}/sessions/search/by_teacher/{teacher_id}',
                        "employments": f'{api_base_url}/employments/search/by_teacher/{teacher_id}',
                        "requests": f'{api_base_url}/requests/search/by_teacher/{teacher_id}'
                    }

                    teacher_with_links = ShowTeacherWithHATEOAS(
                        teacher=teacher_pydantic,
                        links=teacher_links
                    )
                    teachers_with_hateoas.append(teacher_with_links)

                collection_links = {
                    "self": f'{api_base_url}/teachers?page={page}&limit={limit}',
                    "create": f'{api_base_url}/teachers/create'
                }
                collection_links = {k: v for k, v in collection_links.items() if v is not None}

                return ShowTeacherListWithHATEOAS(
                    teachers=teachers_with_hateoas,
                    links=collection_links
                )
            
            except HTTPException:
                raise

            except Exception as e:
                logger.warning(f"Получение преподавателей отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _delete_teacher(teacher_id: int, request: Request, db) -> ShowTeacherWithHATEOAS:
    """
    Use the async with, because it will automatically close the session with the database if an error occurs
    And apply the changes
    """
    async with db as session:
        try:
            async with session.begin():
                teacher_dal = TeacherDAL(session)
                teacher = await teacher_dal.delete_teacher(teacher_id)

                if not teacher:
                    raise HTTPException(status_code=404, detail=f"Преподаватель с id: {teacher_id} не найден")
                
                teacher_pydantic = ShowTeacher.model_validate(teacher)

                # add HATEOAS
                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/teachers/search/by_id/{teacher_id}',
                    "teachers": f'{api_base_url}/teachers/search',
                    "create": f'{api_base_url}/teachers/create',
                    "group": f'{api_base_url}/groups/search/by_teacher/{teacher_id}',
                    "sessions": f'{api_base_url}/sessions/search/by_teacher/{teacher_id}',
                    "employments": f'{api_base_url}/employments/search/by_teacher/{teacher_id}',
                    "requests": f'{api_base_url}/requests/search/by_teacher/{teacher_id}'
                }

                return ShowTeacherWithHATEOAS(teacher=teacher_pydantic, links=hateoas_links)

        except HTTPException:
            raise

        except Exception as e:
            await session.rollback()
            logger.error(f"Неожиданная ошибка при удалении преподавателя {teacher_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Внутренняя ошибка сервера при удалении преподавателя."
            )


async def _update_teacher(body: UpdateTeacher, request:Request, db) -> ShowTeacherWithHATEOAS:
    """Use it for the same reasons as for the delete operation"""
    async with db as session:
        try:
            async with session.begin():
                # exclusion of None-fields from the transmitted data
                update_data = {
                    key: value for key, value in body.dict().items() 
                    if value is not None and key != "teacher_id"
                }

                # change data
                teacher_dal = TeacherDAL(session)
                teacher = await teacher_dal.update_teacher(
                    id=body.teacher_id,
                    **update_data
                )

                if not teacher:
                    raise HTTPException(status_code=404, detail=f"Преподаватель с id: {body.teacher_id} не найден")

                
                teacher_id = body.teacher_id 
                teacher_pydantic = ShowTeacher.model_validate(teacher)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/teachers/search/by_id/{teacher_id}',
                    "delete": f'{api_base_url}/teachers/delete/{teacher_id}',
                    "teachers": f'{api_base_url}/teachers/search',
                    "group": f'{api_base_url}/groups/search/by_teacher/{teacher_id}',
                    "sessions": f'{api_base_url}/sessions/search/by_teacher/{teacher_id}',
                    "employments": f'{api_base_url}/employments/search/by_teacher/{teacher_id}',
                    "requests": f'{api_base_url}/requests/search/by_teacher/{teacher_id}'
                }

                return ShowTeacherWithHATEOAS(teacher=teacher_pydantic, links=hateoas_links)
            
        except HTTPException:
            await session.rollback()
            raise   

        except Exception as e:
            await session.rollback()
            logger.error(f"Неожиданная ошибка при обновлении преподавателя {body.teacher_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Внутренняя ошибка сервера при обновлении преподавателя."
            )


@teacher_router.post("/create", response_model=ShowTeacherWithHATEOAS, status_code=201) # 201 Created standard code
async def create_teacher(body: CreateTeacher, request: Request, db: AsyncSession = Depends(get_db)):
    return await _create_new_teacher(body, request, db)


@teacher_router.get("/search/by_id/{teacher_id}", response_model=ShowTeacherWithHATEOAS,
                    responses={404: {"description": "Преподаватель не найден"}})
async def get_teacher_by_id(teacher_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_teacher_by_id(teacher_id, request, db)


@teacher_router.get("/search/by_humanity", response_model=ShowTeacherWithHATEOAS,
                    responses={404: {"description": "Преподаватель не найден"}})
async def get_teacher_by_name_and_surname(name: str, surname: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_teacher_by_name_and_surname(name, surname, request, db)


@teacher_router.get("/search", response_model=ShowTeacherListWithHATEOAS, responses={404: {"description": "Преподаватели не найдены"}})
async def get_all_teachers(request: Request, query_param: Annotated[QueryParams, Depends()], db: AsyncSession = Depends(get_db)):
    """
    query_param set via Annotated so that fastapi understands
    that the pydantic model QueryParam refers to the query parameters,
    we specify this as the second argument for Annotated.
    Wherever there will be pagination and the number of elements on the page,
    it is better to use this pydantic model, so as not to manually enter these parameters each time.
    Link to documentation: https://fastapi.tiangolo.com/ru/tutorial/query-param-models/
    """
    return await _get_all_teachers(query_param.page, query_param.limit, request, db)


@teacher_router.put("/delete/{teacher_id}", response_model=ShowTeacherWithHATEOAS,
                    responses={404: {"description": "Преподаватель не найден"}})
async def delete_teacher(teacher_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _delete_teacher(teacher_id, request, db)


@teacher_router.put("/update", response_model=ShowTeacherWithHATEOAS, responses={404: {"description": "Преподаватель не найден"}})
async def update_teacher(body: UpdateTeacher, request: Request, db: AsyncSession = Depends(get_db)):
    return await _update_teacher(body, request, db)


'''
============================
CRUD operations for Building
============================
'''


async def _create_new_building(body: CreateBuilding, request: Request, db) -> ShowBuildingWithHATEOAS:
    async with db as session:
        async with session.begin():
            building_dal = BuildingDAL(session)
            try: 
                building = await building_dal.create_building(
                    building_number=body.building_number,
                    city=body.city,
                    building_address=body.building_address
                )

                building_number = building.building_number
                building_pydantic = ShowBuilding.model_validate(building)

                # Add HATEOAS
                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/buildings/search/by_number/{building_number}',
                    "update": f'{api_base_url}/buildings/update/{building_number}',
                    "delete": f'{api_base_url}/buildings/delete/{building_number}',
                    "buildings": f'{api_base_url}/buildings/search',
                    "cabinets": f'{api_base_url}/cabinets/search/by_building/{building_number}'
                }

                return ShowBuildingWithHATEOAS(building=building_pydantic, links=hateoas_links)
            
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности БД при создании здания: {e}", exc_info=True)
                raise HTTPException(
                    status_code=400, 
                    detail="Невозможно создать здание из-за конфликта данных."
                )
            
            except HTTPException:
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

                # if building exist
                if not building:
                    raise HTTPException(status_code=404, detail=f"Здание с номером: {building_number} не найдено")

                building_pydantic = ShowBuilding.model_validate(building)

                # Add HATEOAS
                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/buildings/search/by_number/{building_number}',
                    "update": f'{api_base_url}/buildings/update/{building_number}',
                    "delete": f'{api_base_url}/buildings/delete/{building_number}',
                    "buildings": f'{api_base_url}/buildings/search',
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

                # if building exist
                if not building:
                    raise HTTPException(status_code=404, detail=f"Здание по адресу: {address} не найдено")
                
                building_number = building.building_number
                building_pydantic = ShowBuilding.model_validate(building)

                # Add HATEOAS
                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/buildings/search/by_number/{building_number}',
                    "update": f'{api_base_url}/buildings/update/{building_number}',
                    "delete": f'{api_base_url}/buildings/delete/{building_number}',
                    "buildings": f'{api_base_url}/buildings/search',
                    "cabinets": f'{api_base_url}/cabinets/search/by_building/{building_number}'
                }

                return ShowBuildingWithHATEOAS(building=building_pydantic, links=hateoas_links)
                
            except HTTPException:
                raise

            except Exception as e:
                logger.warning(f"Получение здания отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_all_buildings(page: int, limit: int, request: Request, db) -> ShowBuildingWithHATEOAS:
    async with db as session:
        async with session.begin():
            building_dal = BuildingDAL(session)

            try:
                buildings = await building_dal.get_all_buildings(page, limit)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                buildings_with_hateoas = []
                for building in buildings:
                    building_pydantic = ShowBuilding.model_validate(building)

                    # add HATEOAS
                    building_number = building.building_number
                    building_links = {
                        "self": f'{api_base_url}/buildings/search/by_number/{building_number}',
                        "update": f'{api_base_url}/buildings/update/{building_number}',
                        "delete": f'{api_base_url}/buildings/delete/{building_number}',
                        "buildings": f'{api_base_url}/buildings/search',
                        "cabinets": f'{api_base_url}/cabinets/search/by_building/{building_number}'
                    }

                    building_with_links = ShowBuildingWithHATEOAS(
                        building=building_pydantic,
                        links=building_links
                    )
                    buildings_with_hateoas.append(building_with_links)

                collection_links = {
                    "self": f'{api_base_url}/building?page={page}&limit={limit}',
                    "create": f'{api_base_url}/buildings/create'
                }
                collection_links = {k: v for k, v in collection_links.items() if v is not None}

                return ShowBuildingListWithHATEOAS(
                    buildings=buildings_with_hateoas,
                    links=collection_links
                )
            
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
                building = await building_dal.delete_building(building_number)

                if not building:
                    raise HTTPException(status_code=404, detail=f"Здание с номером: {building_number} не найдено")
                
                building_pydantic = ShowBuilding.model_validate(building)

                # Add HATEOAS
                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/buildings/search/by_number/{building_number}',
                    "buildings": f'{api_base_url}/buildings/search',
                    "create": f'{api_base_url}/buildings/create',
                    "cabinets": f'{api_base_url}/cabinets/search/by_building/{building_number}'
                }

                return ShowBuildingWithHATEOAS(building=building_pydantic, links=hateoas_links)

        except HTTPException:
            await session.rollback()
            raise

        except Exception as e:
            await session.rollback()
            logger.error(f"Неожиданная ошибка при удалении здания {building_number}: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Внутренняя ошибка сервера при удалении здания."
            )


async def _update_building(body: UpdateBuilding, request: Request, db) -> ShowBuildingWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                # exclusion of None-fields from the transmitted data
                update_data = {
                    key: value for key, value in body.dict().items() if value is not None and key != "building_number"
                }

                # Rename field new_building_data to building_data
                if "new_building_number" in update_data:
                    update_data["building_number"] = update_data.pop("new_building_number")

                # change data
                building_dal = BuildingDAL(session)
                building = await building_dal.update_building(
                    target_number=body.building_number,
                    **update_data
                )

                if not building:
                    raise HTTPException(status_code=404, detail=f"Здание с номером: {body.building_number} не найдено")
                
                building_number = building.building_number
                building_pydantic = ShowBuilding.model_validate(building)

                # Add HATEOAS
                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/buildings/search/by_number/{building_number}',
                    "update": f'{api_base_url}/buildings/update/{building_number}',
                    "delete": f'{api_base_url}/buildings/delete/{building_number}',
                    "buildings": f'{api_base_url}/buildings/search',
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


@building_router.get("/search/by_number/{building_number}", response_model=ShowBuildingWithHATEOAS,
                     responses={404: {"description": "Здание не найдено"}})
async def get_building_by_number(building_number: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_building_by_number(building_number, request, db)


@building_router.get("/search/by_address/{building_address}", response_model=ShowBuildingWithHATEOAS,
                     responses={404: {"description": "Здание не найдено"}})
async def get_building_by_address(address: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_building_by_address(address, request, db)


@building_router.get("/search", response_model=ShowBuildingListWithHATEOAS)
async def get_all_buildings(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_all_buildings(query_param.page, query_param.limit, request, db)


@building_router.put("/delete/{building_number}", response_model=ShowBuildingWithHATEOAS,
                     responses={404: {"description": "Здание не найдено"}})
async def delete_building(building_number: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _delete_building(building_number, request, db)


@building_router.put("/update", response_model=ShowBuildingWithHATEOAS, 
                    responses={404: {"description": "Здание не найдено"}})
async def update_building(body: UpdateBuilding, request: Request, db: AsyncSession = Depends(get_db)):
    return await _update_building(body, request, db)


'''
===========================
CRUD operations for Cabinet
===========================
'''


async def _create_cabinet(body: CreateCabinet, request: Request, db) -> ShowCabinetWithHATEOAS:
    async with db as session:
        async with session.begin():
            building_dal = BuildingDAL(session)
            cabinet_dal = CabinetDAL(session)
            
            try: 
                # Check that the building exists
                # Check that the cabinet is unique
                # By using helpers
                if not await ensure_building_exists(building_dal, body.building_number):
                    raise HTTPException(
                        status_code=404,
                        detail=f"Здание с номером {body.building_number} не найдено"
                    )

                if not await ensure_cabinet_unique(cabinet_dal, body.building_number, body.cabinet_number):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Кабинет {body.cabinet_number} уже существует в здании {body.building_number}"
                    )

                # Create cabinet
                cabinet = await cabinet_dal.create_cabinet(
                    cabinet_number=body.cabinet_number,
                    building_number=body.building_number,
                    capacity=body.capacity,
                    cabinet_state=body.cabinet_state
                )

                cabinet_number = cabinet.cabinet_number
                building_number = cabinet.building_number
                cabinet_pydantic = ShowCabinet.model_validate(cabinet)

                # add HATEOAS
                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/cabinets/search/by_building_and_number/{building_number}/{cabinet_number}',
                    "update": f'{api_base_url}/cabinets/update/{building_number}/{cabinet_number}',
                    "delete": f'{api_base_url}/cabinets/delete/{building_number}/{cabinet_number}',
                    "cabinets": f'{api_base_url}/cabinets',
                    "building": f'{api_base_url}/buildings/search/by_number/{building_number}'
                }

                return ShowCabinetWithHATEOAS(cabinet=cabinet_pydantic, links=hateoas_links)
            
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при создании кабинета: {e}", exc_info=True)
                raise HTTPException(status_code=400, detail="Кабинет с таким номером уже существует.")
            
            except HTTPException:
                await session.rollback()
                raise

            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при создании кабинета: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")        


async def _get_all_cabinets(page: int, limit: int, request: Request, db) -> ShowBuildingListWithHATEOAS:
    async with db as session:
        async with session.begin():
            cabinet_dal = CabinetDAL(session)
            try:
                cabinets = await cabinet_dal.get_all_cabinets(page, limit)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                cabinets_with_hateoas = []
                for cabinet in cabinets:
                    cabinet_pydantic = ShowCabinet.model_validate(cabinet)

                    # add HATEOAS
                    cabinet_number = cabinet.cabinet_number
                    building_number = cabinet.building_number
                    cabinet_links = {
                        "self": f'{api_base_url}/cabinets/search/by_building_and_number/{building_number}/{cabinet_number}',
                        "update": f'{api_base_url}/cabinets/update/{building_number}/{cabinet_number}',
                        "delete": f'{api_base_url}/cabinets/delete/{building_number}/{cabinet_number}',
                        "cabinets": f'{api_base_url}/cabinets',
                        "building": f'{api_base_url}/buildings/search/by_number/{building_number}'
                    }

                    cabinet_with_links = ShowCabinetWithHATEOAS(
                        cabinet=cabinet_pydantic,
                        links=cabinet_links
                    )
                    cabinets_with_hateoas.append(cabinet_with_links)

                collection_links = {
                    "self": f'{api_base_url}/cabinets?page={page}&limit={limit}',
                    "create": f'{api_base_url}/cabinets/create'
                }
                collection_links = {k: v for k, v in collection_links.items() if v is not None}

                return ShowCabinetListWithHATEOAS(
                    cabinets=cabinets_with_hateoas,
                    links=collection_links
                )
            
            except HTTPException:
                raise

            except Exception as e:
                logger.warning(f"Получение кабинета отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_cabinets_by_building(building_number: int, page: int, limit: int, request: Request, db) -> ShowCabinetListWithHATEOAS:
    async with db as session:
        async with session.begin():
            cabinet_dal = CabinetDAL(session)

            try:
                cabinets = await cabinet_dal.get_cabinets_by_building(building_number, page, limit)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                cabinets_with_hateoas = []
                for cabinet in cabinets:
                    cabinet_pydantic = ShowCabinet.model_validate(cabinet)

                    # add HATEOAS
                    cabinet_number = cabinet.cabinet_number
                    cabinet_links = {
                        "self": f'{api_base_url}/cabinets/search/by_building_and_number/{building_number}/{cabinet_number}',
                        "update": f'{api_base_url}/cabinets/update/{building_number}/{cabinet_number}',
                        "delete": f'{api_base_url}/cabinets/delete/{building_number}/{cabinet_number}',
                        "cabinets": f'{api_base_url}/cabinets',
                        "building": f'{api_base_url}/buildings/search/by_number/{building_number}'
                    }

                    cabinet_with_links = ShowCabinetWithHATEOAS(
                        cabinet=cabinet_pydantic,
                        links=cabinet_links
                    )
                    cabinets_with_hateoas.append(cabinet_with_links)

                collection_links = {
                    "self": f'{api_base_url}/cabinets?page={page}&limit={limit}',
                    "create": f'{api_base_url}/cabinets/create'
                }
                collection_links = {k: v for k, v in collection_links.items() if v is not None}

                return ShowCabinetListWithHATEOAS(
                    cabinets=cabinets_with_hateoas,
                    links=collection_links
                )
            
            except HTTPException:
                raise

            except Exception as e:
                logger.warning(f"Получение кабинета отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_cabinet_by_building_and_number(building_number: int, cabinet_number: int, request: Request, db) -> ShowCabinetWithHATEOAS:
    async with db as session:
        async with session.begin():
            cabinet_dal = CabinetDAL(session)

            try:
                cabinet = await cabinet_dal.get_cabinet_by_number_and_building(building_number, cabinet_number)

                if not cabinet:
                    raise HTTPException(status_code=404,
                                        detail=f"Кабинет с номером: {cabinet_number} в здании с номером: {building_number} - не найден")
                
                cabinet_number = cabinet.cabinet_number
                building_number = cabinet.building_number
                cabinet_pydantic = ShowCabinet.model_validate(cabinet)

                # add HATEOAS
                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/cabinets/search/by_building_and_number/{building_number}/{cabinet_number}',
                    "update": f'{api_base_url}/cabinets/update/{building_number}/{cabinet_number}',
                    "delete": f'{api_base_url}/cabinets/delete/{building_number}/{cabinet_number}',
                    "cabinets": f'{api_base_url}/cabinets',
                    "building": f'{api_base_url}/buildings/search/by_number/{building_number}'
                }

                return ShowCabinetWithHATEOAS(cabinet=cabinet_pydantic, links=hateoas_links)
            
            except HTTPException:
                raise

            except Exception as e:
                logger.warning(f"Получение кабинета отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _delete_cabinet(building_number: int, cabinet_number: int, request: Request, db) -> ShowCabinetWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                cabinet_dal = CabinetDAL(session)
                cabinet = await cabinet_dal.delete_cabinet(building_number, cabinet_number)

                if not cabinet:
                    raise HTTPException(status_code=404,
                                        detail=f"Кабинет с номером: {cabinet_number} в здании {building_number} не может быть удалён, т.к. не найден")

                cabinet_pydantic = ShowCabinet.model_validate(cabinet)

                # add HATEOAS
                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/cabinets/search/by_building_and_number/{building_number}/{cabinet_number}',
                    "cabinets": f'{api_base_url}/cabinets',
                    "create": f'{api_base_url}/cabinets/create',
                    "building": f'{api_base_url}/buildings/search/by_number/{building_number}'
                }

                return ShowCabinetWithHATEOAS(cabinet=cabinet_pydantic, links=hateoas_links)
        
        except HTTPException:
            await session.rollback()
            raise

        except Exception as e:
            await session.rollback()
            logger.warning(f"Получение кабинета отменено (Ошибка: {e})")
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _update_cabinet(body: UpdateCabinet, request: Request, db) -> ShowCabinetWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                # exclusion of None-fields from the transmitted data
                update_data = {
                    key: value for key, value in body.dict().items() if
                    value is not None and key not in ["building_number", "cabinet_number"]
                }

                # Create cabinet dal
                cabinet_dal = CabinetDAL(session)

                # Rename the fields new_cabinet_number and new_building_number to cabinet_number and building_number
                # And check the transferred data, we can change the parameters of the cabinet by using helpers
                if "new_building_number" in update_data:
                    update_data["building_number"] = update_data.pop("new_building_number")
                    if not await ensure_building_exists(BuildingDAL(session), update_data["building_number"]):
                        raise HTTPException(
                            status_code=404,
                            detail=f"Здание с номером {body.building_number} не найдено"
                        )

                if "new_cabinet_number" in update_data:
                    update_data["cabinet_number"] = update_data.pop("new_cabinet_number")
                    if not await ensure_cabinet_unique(cabinet_dal,
                                                       update_data.get("building_number", body.building_number),
                                                       update_data["cabinet_number"]):
                        raise HTTPException(
                            status_code=400,
                            detail=f"Кабинет {body.cabinet_number} уже существует в здании {body.building_number}"
                        )

                # Change data
                updated_cabinet = await cabinet_dal.update_cabinet(body.building_number, body.cabinet_number, **update_data)

                if not updated_cabinet:
                    raise HTTPException(status_code=404, detail="Кабинет не был обновлён")
                
                cabinet_number = updated_cabinet.cabinet_number
                building_number = updated_cabinet.building_number
                cabinet_pydantic = ShowCabinet.model_validate(updated_cabinet)

                # add HATEOAS
                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/cabinets/search/by_building_and_number/{building_number}/{cabinet_number}',
                    "update": f'{api_base_url}/cabinets/update/{building_number}/{cabinet_number}',
                    "delete": f'{api_base_url}/cabinets/delete/{building_number}/{cabinet_number}',
                    "cabinets": f'{api_base_url}/cabinets',
                    "building": f'{api_base_url}/buildings/search/by_number/{building_number}'
                }

                return ShowCabinetWithHATEOAS(cabinet=cabinet_pydantic, links=hateoas_links)
            
        except HTTPException:
            await session.rollback()
            raise   

        except Exception as e:
            await session.rollback()
            logger.error(f"Неожиданная ошибка при обновлении кабинета {cabinet_number}: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Внутренняя ошибка сервера при обновлении кабинета."
            )


@cabinet_router.post("/create", response_model=ShowCabinetWithHATEOAS)
async def create_cabinet(body: CreateCabinet, request: Request, db: AsyncSession = Depends(get_db)):
    return await _create_cabinet(body, request, db)


@cabinet_router.get("/search", response_model=ShowCabinetListWithHATEOAS, responses={404: {"description": "Кабинеты не найдены"}})
async def get_all_cabinets(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_all_cabinets(query_param.page, query_param.limit, request, db)


@cabinet_router.get("/search/by_building/{building_number}", response_model=ShowCabinetListWithHATEOAS,
                    responses={404: {"description": "Кабинеты не найдены"}})
async def get_cabinets_by_building(building_number: int,
                                   query_param: Annotated[QueryParams, Depends()],
                                   request: Request,
                                   db: AsyncSession = Depends(get_db)):
    return await _get_cabinets_by_building(building_number, query_param.page, query_param.limit, request, db)


@cabinet_router.get("/search/by_building_and_number", response_model=ShowCabinetWithHATEOAS,
                    responses={404: {"description": "Кабинет не найден"}})
async def get_cabinet_by_building_and_number(building_number: int,
                                             cabinet_number: int,
                                             request: Request,
                                             db: AsyncSession = Depends(get_db)):
    return await _get_cabinet_by_building_and_number(building_number, cabinet_number, request, db)


@cabinet_router.put("/delete/{building_number}/{cabinet_number}", response_model=ShowCabinetWithHATEOAS,
                    responses={404: {"description": "Не удаётся удалить кабинет"}})
async def delete_cabinet(building_number: int, cabinet_number: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _delete_cabinet(building_number, cabinet_number, request, db)


@cabinet_router.put("/update", response_model=ShowCabinetWithHATEOAS,
                    responses={404: {"description": "Кабинет не найден или нет возможности изменить его параметры"}})
async def update_cabinet(body: UpdateCabinet, request: Request, db: AsyncSession = Depends(get_db)):
    return await _update_cabinet(body, request, db)


'''
==============================
CRUD operations for Speciality
==============================
'''


async def _create_speciality(body: CreateSpeciality, request: Request, db) -> ShowSpecialityWithHATEOAS:
    async with db as session:
        async with session.begin():
            speciality_dal = SpecialityDAL(session)

            try:
                speciality = await speciality_dal.create_speciality(speciality_code=body.speciality_code)

                speciality_code = speciality.speciality_code
                speciality_pydantic = ShowSpeciality.model_validate(speciality)

                # Add HATEOAS
                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/specialities/search/by_speciality_code/{speciality_code}',
                    "update": f'{api_base_url}/specialities/update/{speciality_code}',
                    "delete": f'{api_base_url}/specialities/delete/{speciality_code}',
                    "specialities": f'{api_base_url}/specialities',
                    "groups": f'{api_base_url}/groups/search/by_speciality/{speciality_code}'
                }

                return ShowSpecialityWithHATEOAS(speciality=speciality_pydantic, links=hateoas_links)

            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности БД при создании специальности: {e}")
                raise HTTPException(status_code=400, detail="Невозможно создать специальность из-за конфликта данных.")
                     
            except HTTPException:
                await session.rollback()
                raise

            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при создании специальности: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")
        


async def _get_all_specialties(page: int, limit: int, request: Request, db) -> ShowSpecialityListWithHATEOAS:
    async with db as session:
        async with session.begin():
            speciality_dal = SpecialityDAL(session)

            try:
                specialities = await speciality_dal.get_all_specialties(page, limit)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                specialities_with_hateoas = []
                for speciality in specialities:
                    speciality_pydantic = ShowSpeciality.model_validate(speciality)

                    # add HATEOAS
                    speciality_code = speciality.speciality_code
                    speciality_links = {
                        "self": f'{api_base_url}/specialities/search/by_speciality_code/{speciality_code}',
                        "update": f'{api_base_url}/specialities/update/{speciality_code}',
                        "delete": f'{api_base_url}/specialities/delete/{speciality_code}',
                        "groups": f'{api_base_url}/groups/search/by_speciality/{speciality_code}'
                }

                    speciality_with_links = ShowSpecialityWithHATEOAS(
                        speciality=speciality_pydantic,
                        links=speciality_links
                    )
                    specialities_with_hateoas.append(speciality_with_links)

                collection_links = {
                    "self": f'{api_base_url}/specialities?page={page}&limit={limit}',
                    "create": f'{api_base_url}/specialities/create'
                }
                collection_links = {k: v for k, v in collection_links.items() if v is not None}

                return ShowSpecialityListWithHATEOAS(
                    speciality=specialities_with_hateoas,
                    links=collection_links
                )
            
            except HTTPException:
                raise

            except Exception as e:
                logger.warning(f"Получение специальностей отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _get_speciality(speciality_code: str, request: Request, db) -> ShowSpecialityWithHATEOAS:
    async with db as session:
        async with session.begin():
            speciality_dal = SpecialityDAL(session)

            try:
                speciality = await speciality_dal.get_speciality(speciality_code)

                # if speciality doesn't exist
                if not speciality:
                    raise HTTPException(status_code=404, detail=f"Специальность с кодом: {speciality_code} не найдена")

                speciality_pydantic = ShowSpeciality.model_validate(speciality)

                # Add HATEOAS
                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/specialities/search/by_speciality_code/{speciality_code}',
                    "update": f'{api_base_url}/specialities/update/{speciality_code}',
                    "delete": f'{api_base_url}/specialities/delete/{speciality_code}',
                    "specialities": f'{api_base_url}/specialities',
                    "groups": f'{api_base_url}/groups/search/by_speciality/{speciality_code}'
                }

                return ShowSpecialityWithHATEOAS(speciality=speciality_pydantic, links=hateoas_links)
            
            except HTTPException:
                raise

            except Exception as e:
                logger.warning(f"Получение специальности отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


async def _delete_speciality(speciality_code: str, request: Request, db) -> ShowSpecialityWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                speciality_dal = SpecialityDAL(session)
                speciality = await speciality_dal.delete_speciality(speciality_code)

                if not speciality:
                    raise HTTPException(status_code=404,
                                        detail=f"Специальность с кодом: {speciality_code} не может быть удалена, т.к. не найдена")

                speciality_pydantic = ShowSpeciality.model_validate(speciality)

                # Add HATEOAS
                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/specialities/search/by_speciality_code/{speciality_code}',
                    "specialities": f'{api_base_url}/specialities',
                    "create": f'{api_base_url}/specialities/create',
                    "groups": f'{api_base_url}/groups/search/by_speciality/{speciality_code}'
                }

                return ShowSpecialityWithHATEOAS(speciality=speciality_pydantic, links=hateoas_links)
            
        except HTTPException:
            await session.rollback()
            raise

        except Exception as e:
            await session.rollback()
            logger.warning(f"Неожиданная ошибка при удалении специальности {speciality_code}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении специальности.")


async def _update_speciality(body: UpdateSpeciality, request: Request, db) -> ShowSpecialityWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                # exclusion of None-fields from the transmitted data
                update_data = {
                    key: value for key, value in body.dict().items() if
                    value is not None and key != "speciality_code"
                }

                speciality_dal = SpecialityDAL(session)

                # Rename field new_speciality_code to speciality_code
                if "new_speciality_code" in update_data:
                    update_data["speciality_code"] = update_data.pop("new_speciality_code")

                # Change data
                speciality = await speciality_dal.update_speciality(
                    target_code=body.speciality_code, 
                    **update_data
                    )

                if not speciality:
                    raise HTTPException(status_code=404, detail="Специальность не была обновлена")
                
                speciality_code = body.speciality_code
                speciality_pydantic = ShowSpeciality.model_validate(speciality)

                # Add HATEOAS
                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/specialities/search/by_speciality_code/{speciality_code}',
                    "update": f'{api_base_url}/specialities/update/{speciality_code}',
                    "delete": f'{api_base_url}/specialities/delete/{speciality_code}',
                    "specialities": f'{api_base_url}/specialities',
                    "groups": f'{api_base_url}/groups/search/by_speciality/{speciality_code}'
                }

                return ShowSpecialityWithHATEOAS(speciality=speciality_pydantic, links=hateoas_links)

        except HTTPException:
            await session.rollback()
            raise   

        except Exception as e:
            await session.rollback()
            logger.error(f"Неожиданная ошибка при обновлении специальности {body.speciality_code}: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Внутренняя ошибка сервера при обновлении специальности."
            )


@speciality_router.post("/create", response_model=ShowSpecialityWithHATEOAS, status_code=201)
async def create_speciality(body: CreateSpeciality, request: Request, db: AsyncSession = Depends(get_db)):
    return await _create_speciality(body, request, db)


@speciality_router.get("/search", response_model=ShowSpecialityListWithHATEOAS, responses={404: {"description": "Специальность не найдена"}})
async def get_all_specialities(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_all_specialties(query_param.page, query_param.limit, request, db)


@speciality_router.get("/search/by_speciality_code", response_model=ShowSpecialityWithHATEOAS,
                    responses={404: {"description": "Специальность не найдена"}})
async def get_speciality_by_code(speciality_code: str, db: AsyncSession = Depends(get_db)):
    return await _get_speciality(speciality_code, db)


@speciality_router.put("/delete/{speciality_code}", response_model=ShowSpecialityWithHATEOAS,
                    responses={404: {"description": "Не удаётся удалить специальность"}})
async def delete_speciality(speciality_code: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await _delete_speciality(speciality_code, request, db)


@speciality_router.put("/update", response_model=ShowSpecialityWithHATEOAS,
                    responses={404: {"description": "Специальность не найдена или нет возможности изменить её параметры"}})
async def update_speciality(body: UpdateSpeciality, request: Request, db: AsyncSession = Depends(get_db)):
    return await _update_speciality(body, request, db)


'''
=========================
CRUD operations for Group
=========================
'''


async def _create_new_group(body: CreateGroup, request: Request, db) -> ShowGroupWithHATEOAS:
    async with db as session:
        async with session.begin():
            group_dal = GroupDAL(session)
            teacher_dal = TeacherDAL(session)
            speciality_dal = SpecialityDAL(session)

            try:
                # Check that the teacher and speciality exists
                # Check that the group is unique
                # By using helpers
                if body.speciality_code != None and not await ensure_speciality_exists(speciality_dal, body.speciality_code):
                    raise HTTPException(
                        status_code=404,
                        detail=f"Специальность с кодом {body.speciality_code} не найдена"
                    )
                
                if body.group_advisor_id != None and not await ensure_teacher_exists(teacher_dal, body.group_advisor_id):
                    raise HTTPException(
                        status_code=404,
                        detail=f"Учитель с id {body.group_advisor_id} не найден"
                    )

                if not await ensure_group_unique(group_dal, body.group_name):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Группа {body.group_name} уже существует"
                    )

                group = await group_dal.create_group(
                    group_name=body.group_name,
                    speciality_code=body.speciality_code,
                    quantity_students=body.quantity_students,
                    group_advisor_id=body.group_advisor_id
                )

                group_name = group.group_name
                group_pydantic = ShowGroup.model_validate(group)

                # Add HATEOAS
                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/groups/search/by_group-name/{group_name}',
                    "update": f'{api_base_url}/groups/update/{group_name}',
                    "delete": f'{api_base_url}/groups/delete/{group_name}',
                    "groups": f'{api_base_url}/groups',
                    "advisor": f'{api_base_url}/teachers/search/by_group/{group_name}' if group.group_advisor_id else None,
                    "speciality": f'{api_base_url}/specialities/search/by_speciality_code/{group.speciality_code}' if group.speciality_code else None,
                    "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}',
                    "curriculums": f'{api_base_url}/curriculums/search/by_group/{group_name}',
                    "requests": f'{api_base_url}/requests/search/by_group/{group_name}'
                }
                hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                return ShowGroupWithHATEOAS(group=group_pydantic, links=hateoas_links)
            
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности БД при создании группы: {e}")
                raise HTTPException(status_code=400, detail="Невозможно создать группу из-за конфликта данных.")
                     
            except HTTPException:
                await session.rollback()
                raise
                     
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при создании группы: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")
        


async def _get_group_by_name(group_name: str, request: Request, db) -> ShowGroupWithHATEOAS:
    async with db as session:
        async with db as session:
            group_dal = GroupDAL(session)
            try:
                group = await group_dal.get_group(group_name)

                # if group doesn't exist
                if not group:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Группа с названием: {group_name} не найдена"
                    )

                group_pydantic = ShowGroup.model_validate(group)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/groups/search/by_group-name/{group_name}',
                    "update": f'{api_base_url}/groups/update/{group_name}',
                    "delete": f'{api_base_url}/groups/delete/{group_name}',
                    "groups": f'{api_base_url}/groups',
                    "advisor": f'{api_base_url}/teachers/search/{group.group_advisor_id}' if group.group_advisor_id else None,
                    "speciality": f'{api_base_url}/specialities/search/{group.speciality_code}' if group.speciality_code else None,
                    "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}',
                    "curriculums": f'{api_base_url}/curriculums/search/by_group/{group_name}',
                    "requests": f'{api_base_url}/requests/search/by_group/{group_name}'
                }
                hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                return ShowGroupWithHATEOAS(group=group_pydantic, links=hateoas_links)

            except HTTPException:
                raise

            except Exception as e:
                logger.error(f"Неожиданная ошибка при получении группы {group_name}: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail="Внутренняя ошибка сервера при получении группы."
                )
        

async def _get_group_by_advisor(advisor_id: int, request: Request, db) -> ShowGroupWithHATEOAS:
    async with db as session:
        async with session.begin(): 
            group_dal = GroupDAL(session)

            try:
                group = await group_dal.get_group_by_advisor_id(advisor_id)

                # if group doesn't exist
                if not group:
                    raise HTTPException(status_code=404, detail=f"Группа с преподавателем: {advisor_id} не найдена")

                group_pydantic = ShowGroup.model_validate(group)
                group_name = group.group_name

                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/groups/search/by_group-name/{group_name}',
                    "update": f'{api_base_url}/groups/update/{group_name}',
                    "delete": f'{api_base_url}/groups/delete/{group_name}',
                    "groups": f'{api_base_url}/groups',
                    "advisor": f'{api_base_url}/teachers/search/{group.group_advisor_id}' if group.group_advisor_id else None,
                    "speciality": f'{api_base_url}/specialities/search/{group.speciality_code}' if group.speciality_code else None,
                    "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}',
                    "curriculums": f'{api_base_url}/curriculums/search/by_group/{group_name}',
                    "requests": f'{api_base_url}/requests/search/by_group/{group_name}'
                }
                hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                return ShowGroupWithHATEOAS(group=group_pydantic, links=hateoas_links)

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Неожиданная ошибка при получении группы {group_name}: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail="Внутренняя ошибка сервера при получении группы."
                )
        

async def _get_all_groups(page: int, limit: int, request: Request, db) -> ShowGroupListWithHATEOAS:
    async with db as session:
        async with session.begin():
            group_dal = GroupDAL(session)

            try:
                groups = await group_dal.get_all_groups(page, limit)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                groups_with_hateoas = []
                for group in groups:
                    group_pydantic = ShowGroup.model_validate(group)

                    # add HATEOAS
                    group_name = group.group_name
                    group_links = {
                        "self": f'{api_base_url}/groups/search/by_group-name/{group_name}',
                        "update": f'{api_base_url}/groups/update/{group_name}',
                        "delete": f'{api_base_url}/groups/delete/{group_name}',
                        "advisor": f'{api_base_url}/teachers/search/{group.group_advisor_id}' if group.group_advisor_id else None,
                        "speciality": f'{api_base_url}/specialities/search/{group.speciality_code}' if group.speciality_code else None,
                        "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}',
                        "curriculums": f'{api_base_url}/curriculums/search/by_group/{group_name}',
                        "requests": f'{api_base_url}/requests/search/by_group/{group_name}'
                    }
                    group_links = {k: v for k, v in group_links.items() if v is not None}

                    group_with_links = ShowGroupWithHATEOAS(
                        group=group_pydantic,
                        links=group_links
                    )
                    groups_with_hateoas.append(group_with_links)

                collection_links = {
                    "self": f'{api_base_url}/groups?page={page}&limit={limit}',
                    "create": f'{api_base_url}/groups/create'
                }
                collection_links = {k: v for k, v in collection_links.items() if v is not None}

                return ShowGroupListWithHATEOAS(
                    groups=groups_with_hateoas,
                    links=collection_links
                )
            
            except HTTPException:
                raise

            except Exception as e:
                logger.warning(f"Получение групп отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")
        

async def _get_all_groups_by_speciality(speciality_code: str, page: int, limit: int, request: Request, db) -> ShowGroupListWithHATEOAS:
    async with db as session:
        async with session.begin():
            group_dal = GroupDAL(session)
            speciality_dal = SpecialityDAL(session)

            if not await ensure_speciality_exists(speciality_dal, speciality_code):
                raise HTTPException(
                    status_code=404,
                    detail=f"Специальность с кодом {speciality_code} не найдена"
                )
            
            try:
                groups = await group_dal.get_all_groups_by_speciality(speciality_code, page, limit)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                groups_with_hateoas = []
                for group in groups:
                    group_pydantic = ShowGroup.model_validate(group)

                    # add HATEOAS
                    group_name = group.group_name
                    group_links = {
                        "self": f'{api_base_url}/groups/search/by_group-name/{group_name}',
                        "update": f'{api_base_url}/groups/update/{group_name}',
                        "delete": f'{api_base_url}/groups/delete/{group_name}',
                        "advisor": f'{api_base_url}/teachers/search/{group.group_advisor_id}' if group.group_advisor_id else None,
                        "speciality": f'{api_base_url}/specialities/search/{group.speciality_code}' if group.speciality_code else None,
                        "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}',
                        "curriculums": f'{api_base_url}/curriculums/search/by_group/{group_name}',
                        "requests": f'{api_base_url}/requests/search/by_group/{group_name}'
                    }
                    group_links = {k: v for k, v in group_links.items() if v is not None}

                    group_with_links = ShowGroupWithHATEOAS(
                        group=group_pydantic,
                        links=group_links
                    )
                    groups_with_hateoas.append(group_with_links)

                collection_links = {
                    "self": f'{api_base_url}/groups?page={page}&limit={limit}',
                    "create": f'{api_base_url}/groups/create'
                }
                collection_links = {k: v for k, v in collection_links.items() if v is not None}

                return ShowGroupListWithHATEOAS(
                    groups=groups_with_hateoas,
                    links=collection_links
                )
            
            except HTTPException:
                raise

            except Exception as e:
                logger.warning(f"Получение групп отменено (Ошибка: {e})")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")

                

async def _delete_group(group_name: str, request: Request, db) -> ShowGroupWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                group_dal = GroupDAL(session)
                group = await group_dal.delete_group(group_name)

                if not group:
                    raise HTTPException(status_code=404, detail=f"Группа с названием: {group_name} не найдена")

                group_pydantic = ShowGroup.model_validate(group)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/groups/search/by_group-name/{group_name}',
                    "update": f'{api_base_url}/groups/update/{group_name}',
                    "delete": f'{api_base_url}/groups/delete/{group_name}',
                    "groups": f'{api_base_url}/groups',
                    "advisor": f'{api_base_url}/teachers/search/{group.group_advisor_id}' if group.group_advisor_id else None,
                    "speciality": f'{api_base_url}/specialities/search/{group.speciality_code}' if group.speciality_code else None,
                    "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}',
                    "curriculums": f'{api_base_url}/curriculums/search/by_group/{group_name}',
                    "requests": f'{api_base_url}/requests/search/by_group/{group_name}'
                }
                hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                return ShowGroupWithHATEOAS(group=group_pydantic, links=hateoas_links)
        
        except HTTPException:
            await session.rollback()
            raise

        except Exception as e:
            await session.rollback()
            logger.error(f"Неожиданная ошибка при удалении группы {group_name}: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Внутренняя ошибка сервера при удалении группы."
            )


async def _update_group(body: UpdateGroup, request: Request, db) -> ShowGroupWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                # exclusion of None-fields from the transmitted data
                update_data = {
                    key: value for key, value in body.dict().items() 
                    if value is not None and key != "group_name"
                }

                group_dal = GroupDAL(session)
                teacher_dal = TeacherDAL(session)
                speciality_dal = SpecialityDAL(session)

                # Rename field new_speciality_code to speciality_code
                if "new_group_name" in update_data:
                    update_data["group_name"] = update_data.pop("new_group_name")

                if body.speciality_code != None and not await ensure_speciality_exists(speciality_dal, body.speciality_code):
                    raise HTTPException(
                        status_code=404,
                        detail=f"Специальность с кодом {body.speciality_code} не найдена"
                    )
                
                if body.group_advisor_id != None and not await ensure_teacher_exists(teacher_dal, body.group_advisor_id):
                    raise HTTPException(
                        status_code=404,
                        detail=f"Учитель с id {body.group_advisor_id} не найден"
                    )

                if not await ensure_group_unique(group_dal, body.new_group_name):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Группа {body.new_group_name} уже существует"
                    )

                group = await group_dal.update_group(
                    target_group=body.group_name,
                    **update_data
                )

                group_pydantic = ShowGroup.model_validate(group)
                group_name = group.group_name

                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/groups/search/by_group-name/{group_name}',
                    "delete": f'{api_base_url}/groups/delete/{group_name}',
                    "groups": f'{api_base_url}/groups',
                    "advisor": f'{api_base_url}/teachers/search/{group.group_advisor_id}' if group.group_advisor_id else None,
                    "speciality": f'{api_base_url}/specialities/search/{group.speciality_code}' if group.speciality_code else None,
                    "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}',
                    "curriculums": f'{api_base_url}/curriculums/search/by_group/{group_name}',
                    "requests": f'{api_base_url}/requests/search/by_group/{group_name}'
                }
                hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                return ShowGroupWithHATEOAS(group=group_pydantic, links=hateoas_links)
            
        except HTTPException:
            await session.rollback()
            raise   

        except Exception as e:
            await session.rollback()
            logger.error(f"Неожиданная ошибка при обновлении группы {body.group_name}: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Внутренняя ошибка сервера при обновлении группы."
            )


@group_router.post("/create", response_model=ShowGroupWithHATEOAS, status_code=201)
async def create_group(body: CreateGroup, request: Request, db: AsyncSession = Depends(get_db)):
    return await _create_new_group(body, request, db)


@group_router.get("/search/by_group_name/{group_name}", response_model=ShowGroupWithHATEOAS,
                    responses={404: {"description": "Группа не найдена"}})
async def get_group_by_name(group_name: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_group_by_name(group_name, request, db)


@group_router.get("/search/by_advisor/{advisor_id}", response_model=ShowGroupWithHATEOAS,
                    responses={404: {"description": "Группа не найдена"}})
async def get_group_by_advisor(advisor_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_group_by_advisor(advisor_id, request, db)


@group_router.get("/search", response_model=ShowGroupListWithHATEOAS, 
                  responses={404: {"description": "Группы не найдены"}})
async def get_all_groups(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_all_groups(query_param.page, request, query_param.limit, db)


@group_router.get("/search/by_speciality/{speciality_code}", response_model=ShowGroupListWithHATEOAS, 
                  responses={404: {"description": "Группы не найдены"}})
async def get_all_groups_by_speciality(speciality_code: str, query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_all_groups_by_speciality(speciality_code, query_param.page, query_param.limit, request, db)


@group_router.put("/delete/{group_name}", response_model=ShowGroupWithHATEOAS,
                    responses={404: {"description": "Группа не найдена"}})
async def delete_group(group_name: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await _delete_group(group_name, request, db)


@group_router.put("/update", response_model=ShowGroupWithHATEOAS, 
                  responses={404: {"description": "Группа не найдена"}})
async def update_group(body: UpdateGroup, request: Request, db: AsyncSession = Depends(get_db)):
    return await _update_group(body, request, db)


'''
==============================
CRUD operations for Curriculum
==============================
'''


async def _create_new_curriculum(body: CreateCurriculum, request: Request, db) -> ShowCurriculumWithHATEOAS:
    async with db as session:
        async with session.begin():
            group_dal = GroupDAL(session)
            subject_dal = SubjectDAL(session)
            curriculum_dal = CurriculumDAL(session)

            try:
                # Check that the group and subject exists
                # Check that the curriculum is unique
                # By using helpers
                if body.group_name != None and not await ensure_group_exists(group_dal, body.group_name):
                    raise HTTPException(
                        status_code=404,
                        detail=f"Группа с названием {body.group_name} не найдена"
                    )
                
                if body.subject_code != None and not await ensure_subject_exists(subject_dal, body.subject_code):
                    raise HTTPException(
                        status_code=404,
                        detail=f"Предмет с кодом {body.subject_code} не найден"
                    )

                if not await ensure_curriculum_unique(curriculum_dal, body.semester_number, body.group_name, body.subject_code):
                    raise HTTPException(
                        status_code=400,
                        detail=f"План для предмета {body.subject_code} в группе {body.group_name} на семестр {body.semester_number} уже существует"
                    )

                curriculum = await curriculum_dal.create_curriculum(
                    semester_number=body.semester_number,
                    group_name=body.group_name,
                    subject_code=body.subject_code,
                    lectures_hours=body.lectures_hours,
                    laboratory_hours=body.laboratory_hours,
                    practical_hours=body.practical_hours
                )

                curriculum_pydantic = ShowCurriculum.model_validate(curriculum)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                semester_number = curriculum.semester_number
                group_name = curriculum.group_name
                subject_code = curriculum.subject_code

                hateoas_links = {
                    "self": f'{api_base_url}/curriculums/search/{semester_number}/{group_name}/{subject_code}',
                    "update": f'{api_base_url}/curriculums/update/{semester_number}/{group_name}/{subject_code}',
                    "delete": f'{api_base_url}/curriculums/delete/{semester_number}/{group_name}/{subject_code}',
                    "curriculums": f'{api_base_url}/curriculums',
                    "group": f'{api_base_url}/groups/search/by_group_name/{group_name}',
                    "subject": f'{api_base_url}/subjects/search/by_code/{subject_code}'
                }

                return ShowCurriculumWithHATEOAS(curriculum=curriculum_pydantic, links=hateoas_links)

            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности БД при создании учебного плана: {e}", exc_info=True)
                raise HTTPException(
                    status_code=400, 
                    detail="Невозможно создать учебный план из-за конфликта данных."
                )
            
            except HTTPException:
                await session.rollback()
                raise

            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при создании учебного плана: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500, 
                    detail="Внутренняя ошибка сервера при создании учебного плана."
                )
            


async def _get_curriculum(semester_number: int, group_name: str, subject_code: str, request: Request, db) -> ShowCurriculumWithHATEOAS:
    async with db as session:
        curriculum_dal = CurriculumDAL(session)
        try:
            curriculum = await curriculum_dal.get_curriculum(semester_number, group_name, subject_code)

            # if curriculum doesn't exist
            if not curriculum:
                raise HTTPException(
                    status_code=404,
                    detail=f"План для предмета: {subject_code} в группе: {group_name} на семестр: {semester_number} не найден"
                )

            curriculum_pydantic = ShowCurriculum.model_validate(curriculum)

            base_url = str(request.base_url).rstrip('/')
            api_prefix = '/schedule'
            api_base_url = f'{base_url}{api_prefix}'

            hateoas_links = {
                "self": f'{api_base_url}/curriculums/search/{semester_number}/{group_name}/{subject_code}',
                "update": f'{api_base_url}/curriculums/update/{semester_number}/{group_name}/{subject_code}',
                "delete": f'{api_base_url}/curriculums/delete/{semester_number}/{group_name}/{subject_code}',
                "curriculums": f'{api_base_url}/curriculums',
                "group": f'{api_base_url}/groups/search/by_group_name/{group_name}',
                "subject": f'{api_base_url}/subjects/search/by_code/{subject_code}'
            }

            return ShowCurriculumWithHATEOAS(curriculum=curriculum_pydantic, links=hateoas_links)

        except HTTPException:
            raise

        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении учебного плана ({semester_number}, {group_name}, {subject_code}): {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Внутренняя ошибка сервера при получении учебного плана."
            )


async def _get_all_curriculums(page: int, limit: int, request: Request, db) -> ShowCurriculumListWithHATEOAS: # <-- Изменен тип возврата и добавлен request
    """
    Получает страницу списка учебных планов с HATEOAS-ссылками.
    """
    async with db as session:
        async with session.begin():
            curriculum_dal = CurriculumDAL(session)
            try:
                curriculums_orm_list = await curriculum_dal.get_all_curriculums(page, limit)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                curriculums_with_hateoas = []
                for curriculum_orm in curriculums_orm_list:
                    curriculum_pydantic = ShowCurriculum.model_validate(curriculum_orm)

                    semester_number = curriculum_orm.semester_number
                    group_name = curriculum_orm.group_name
                    subject_code = curriculum_orm.subject_code

                    curriculum_links = {
                        "self": f'{api_base_url}/curriculums/search/{semester_number}/{group_name}/{subject_code}',
                        "update": f'{api_base_url}/curriculums/update/{semester_number}/{group_name}/{subject_code}',
                        "delete": f'{api_base_url}/curriculums/delete/{semester_number}/{group_name}/{subject_code}',
                        "group": f'{api_base_url}/groups/search/by_group_name/{group_name}',
                        "subject": f'{api_base_url}/subjects/search/by_code/{subject_code}',
                    }

                    curriculum_with_links = ShowCurriculumWithHATEOAS( 
                        curriculum=curriculum_pydantic,
                        links=curriculum_links
                    )
                    curriculums_with_hateoas.append(curriculum_with_links)

                collection_links = {
                    "self": f'{api_base_url}/curriculums?page={page}&limit={limit}',
                    "create": f'{api_base_url}/curriculums',
                }

                return ShowCurriculumListWithHATEOAS( 
                    curriculums=curriculums_with_hateoas,
                    links=collection_links
                )

            except Exception as e:
                logger.error(f"Неожиданная ошибка при получении списка учебных планов (страница {page}, лимит {limit}): {e}", exc_info=True)
                raise


async def _get_all_curriculums_by_group(group_name: str, page: int, limit: int, request: Request, db) -> ShowCurriculumListWithHATEOAS:
    async with db as session:
        async with session.begin():
            curriculum_dal = CurriculumDAL(session)
            try:
                curriculums_orm_list = await curriculum_dal.get_all_curriculums_by_group(group_name, page, limit)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule'
                api_base_url = f'{base_url}{api_prefix}'

                curriculums_with_hateoas = []
                for curriculum_orm in curriculums_orm_list:
                    curriculum_pydantic = ShowCurriculum.model_validate(curriculum_orm)

                    semester_number = curriculum_orm.semester_number
                    group_name_from_obj = curriculum_orm.group_name 
                    subject_code = curriculum_orm.subject_code

                    curriculum_links = {
                        "self": f'{api_base_url}/curriculums/search/{semester_number}/{group_name_from_obj}/{subject_code}',
                        "update": f'{api_base_url}/curriculums/update/{semester_number}/{group_name_from_obj}/{subject_code}',
                        "delete": f'{api_base_url}/curriculums/delete/{semester_number}/{group_name_from_obj}/{subject_code}',
                        "group": f'{api_base_url}/groups/search/by_group_name/{group_name_from_obj}',
                        "subject": f'{api_base_url}/subjects/search/by_code/{subject_code}',
                    }

                    curriculum_with_links = ShowCurriculumWithHATEOAS( 
                        curriculum=curriculum_pydantic,
                        links=curriculum_links
                    )
                    curriculums_with_hateoas.append(curriculum_with_links)

                collection_links = {
                    "self": f'{api_base_url}/curriculums/search/by_group/{group_name}?page={page}&limit={limit}',
                    "create": f'{api_base_url}/curriculums',
                    "group": f'{api_base_url}/groups/search/by_group_name/{group_name}', 
                }

                return ShowCurriculumListWithHATEOAS( 
                    curriculums=curriculums_with_hateoas,
                    links=collection_links
                )

            except Exception as e:
                logger.error(f"Неожиданная ошибка при получении списка учебных планов для группы '{group_name}' (страница {page}, лимит {limit}): {e}", exc_info=True)
                raise 


async def _delete_curriculum(semester_number: int, group_name: str, subject_code: str, request: Request, db) -> ShowCurriculumWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                curriculum_dal = CurriculumDAL(session)
                curriculum = await curriculum_dal.delete_curriculum(semester_number, group_name, subject_code)

                if not curriculum:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"План для предмета: {subject_code} в группе: {group_name} на семестр: {semester_number} не найден"
                    )

                curriculum_pydantic = ShowCurriculum.model_validate(curriculum)

                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule' 
                api_base_url = f'{base_url}{api_prefix}'

                hateoas_links = {
                    "self": f'{api_base_url}/curriculums/search/{semester_number}/{group_name}/{subject_code}',
                    "curriculums": f'{api_base_url}/curriculums',
                    "create": f'{api_base_url}/curriculums',
                    "group": f'{api_base_url}/groups/search/by_group_name/{group_name}',
                    "subject": f'{api_base_url}/subjects/search/by_code/{subject_code}'
                }

                return ShowCurriculumWithHATEOAS(curriculum=curriculum_pydantic, links=hateoas_links)

        except HTTPException:
            await session.rollback()
            raise

        except Exception as e:
            await session.rollback()
            logger.error(f"Неожиданная ошибка при удалении учебного плана ({semester_number}, {group_name}, {subject_code}): {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Внутренняя ошибка сервера при удалении учебного плана."
            )


async def _update_curriculum(body: UpdateCurriculum, request: Request, db) -> ShowCurriculumWithHATEOAS:
    async with db as session:
        try:
            async with session.begin():
                update_data = {
                    key: value for key, value in body.dict().items()
                    if value is not None and key not in ["semester_number", "group_name", "subject_code"]
                }

                group_dal = GroupDAL(session)
                subject_dal = SubjectDAL(session)
                curriculum_dal = CurriculumDAL(session)

                if "new_group_name" in update_data and not await ensure_group_exists(group_dal, update_data["new_group_name"]):
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Группа с названием {update_data['new_group_name']} не найдена"
                    )

                if "new_subject_code" in update_data and not await ensure_subject_exists(subject_dal, update_data["new_subject_code"]):
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Предмет с кодом {update_data['new_subject_code']} не найден"
                    )
                
                if "new_semester_number" in update_data:
                    update_data["semester_number"] = update_data.pop("new_semester_number")
                if "new_group_name" in update_data:
                    update_data["group_name"] = update_data.pop("new_group_name")
                if "new_subject_code" in update_data:
                    update_data["subject_code"] = update_data.pop("new_subject_code")

                new_semester_number = update_data.get("semester_number", body.semester_number)
                new_group_name = update_data.get("group_name", body.group_name)
                new_subject_code = update_data.get("subject_code", body.subject_code)

                if not (
                    new_semester_number == body.semester_number and
                    new_group_name == body.group_name and
                    new_subject_code == body.subject_code
                ):
                    if not await ensure_curriculum_unique(curriculum_dal, new_semester_number, new_group_name, new_subject_code):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"План для предмета {new_subject_code} в группе {new_group_name} на семестр {new_semester_number} уже существует"
                        )

                curriculum = await curriculum_dal.update_curriculum(
                    tg_semester_number=body.semester_number,
                    tg_group_name=body.group_name,
                    tg_subject_code=body.subject_code,
                    **update_data
                )

                curriculum_pydantic = ShowCurriculum.model_validate(curriculum) 

                base_url = str(request.base_url).rstrip('/')
                api_prefix = '/schedule' 
                api_base_url = f'{base_url}{api_prefix}'

                final_semester_number = curriculum.semester_number
                final_group_name = curriculum.group_name
                final_subject_code = curriculum.subject_code

                hateoas_links = {
                    "self": f'{api_base_url}/curriculums/search/{final_semester_number}/{final_group_name}/{final_subject_code}',
                    "update": f'{api_base_url}/curriculums/update/{final_semester_number}/{final_group_name}/{final_subject_code}',
                    "delete": f'{api_base_url}/curriculums/delete/{final_semester_number}/{final_group_name}/{final_subject_code}',
                    "curriculums": f'{api_base_url}/curriculums',
                    "group": f'{api_base_url}/groups/search/by_group_name/{final_group_name}',
                    "subject": f'{api_base_url}/subjects/search/by_code/{final_subject_code}'
                }

                return ShowCurriculumWithHATEOAS(curriculum=curriculum_pydantic, links=hateoas_links)

        except IntegrityError as e:
            await session.rollback()
            logger.error(f"Ошибка целостности БД при обновлении учебного плана ({body.semester_number}, {body.group_name}, {body.subject_code}): {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Невозможно обновить учебный план из-за конфликта данных (например, нарушение внешнего ключа или уникальности)."
            )
        
        except HTTPException:
            await session.rollback()
            raise

        except Exception as e:
            await session.rollback()
            logger.error(f"Неожиданная ошибка при обновлении учебного плана ({body.semester_number}, {body.group_name}, {body.subject_code}): {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Внутренняя ошибка сервера при обновлении учебного плана."
            )


@curriculum_router.post("/", response_model=ShowCurriculumWithHATEOAS, status_code=status.HTTP_201_CREATED) 
async def create_curriculum(body: CreateCurriculum, request: Request, db: AsyncSession = Depends(get_db)): 
    return await _create_new_curriculum(body, request, db)


@curriculum_router.get("/{semester_number}/{group_name}/{subject_code}", response_model=ShowCurriculumWithHATEOAS,
                    responses={404: {"description": "План не найден"}})
async def get_curriculum(semester_number: int, group_name: str, subject_code: str, request: Request, db: AsyncSession = Depends(get_db)): 
    return await _get_curriculum(semester_number, group_name, subject_code, request, db) 


@curriculum_router.get("/", response_model=ShowCurriculumListWithHATEOAS, responses={404: {"description": "Планы не найдены"}}) 
async def get_all_curriculums(request: Request, query_param: Annotated[QueryParams, Depends()], db: AsyncSession = Depends(get_db)): 
    return await _get_all_curriculums(query_param.page, query_param.limit, request, db) 


@curriculum_router.get("/search/by_group/{group_name}", response_model=ShowCurriculumListWithHATEOAS, responses={404: {"description": "Планы не найдены"}})
async def get_all_curriculums_by_group(group_name: str, request: Request, query_param: Annotated[QueryParams, Depends()], db: AsyncSession = Depends(get_db)):
    return await _get_all_curriculums_by_group(group_name, query_param.page, query_param.limit, request, db) 


@curriculum_router.delete("/{semester_number}/{group_name}/{subject_code}", response_model=ShowCurriculumWithHATEOAS,
                    responses={404: {"description": "План не найден"}})
async def delete_curriculum(semester_number: int, group_name: str, subject_code: str, request: Request, db: AsyncSession = Depends(get_db)): 
    return await _delete_curriculum(semester_number, group_name, subject_code, request, db)


@curriculum_router.put("/update", response_model=ShowCurriculumWithHATEOAS, responses={404: {"description": "План не найден"}})
async def update_curriculum(body: UpdateCurriculum, request: Request, db: AsyncSession = Depends(get_db)):
    return await _update_curriculum(body, request, db)


'''
===========================
CRUD operations for Subject
===========================
'''


async def _create_new_subject(body: CreateSubject, db) -> ShowSubject:
    async with db as session:
        async with session.begin():
            subject_dal = SubjectDAL(session)

            # Check that the subject is unique
            # By using helpers
            if not await ensure_subject_unique(subject_dal, body.subject_code):
                raise HTTPException(
                    status_code=400,
                    detail=f"Предмет {body.subject_code} уже существует"
                )

            subject = await subject_dal.create_subject(
                subject_code=body.subject_code,
                name=body.name
            )
            return ShowSubject.from_orm(subject)


async def _get_subject(subject_code: str, db) -> ShowSubject:
    async with db as session:
        async with session.begin(): 
            subject_dal = SubjectDAL(session)
            subject = await subject_dal.get_subject(subject_code)

            # if curriculum doesn't exist
            if not subject:
                raise HTTPException(status_code=404, detail=f"Предмет {subject_code} не найден")

            return ShowSubject.from_orm(subject) 


async def _get_all_subjects(page: int, limit: int, db) -> list[ShowSubject]:
    async with db as session:
        async with session.begin():
            subject_dal = SubjectDAL(session)
            subjects = await subject_dal.get_all_subjects(page, limit)

            return [ShowSubject.from_orm(subject) for subject in subjects]


async def _get_all_subjects_by_name(name: str, page: int, limit: int, db) -> list[ShowSubject]:
    async with db as session:
        async with session.begin():
            subject_dal = SubjectDAL(session)
            subjects = await subject_dal.get_subjects_by_name(name, page, limit)

            return [ShowSubject.from_orm(subject) for subject in subjects]
        

async def _delete_subject(subject_code: str, db) -> ShowSubject:
    async with db as session:
        try:
            async with session.begin():
                subject_dal = SubjectDAL(session)
                subject = await subject_dal.delete_subject(subject_code)

                if not subject:
                    raise HTTPException(status_code=404, detail=f"План: {subject_code} не найден")

            return ShowSubject.from_orm(subject)

        except Exception as e:
            logger.warning(f"Удаление предмета отменено (Ошибка: {e})")
            raise


async def _update_subject(body: UpdateSubject, db) -> ShowSubject:
    async with db as session:
        try:
            async with session.begin():
                # exclusion of None-fields from the transmitted data
                update_data = {
                    key: value for key, value in body.dict().items() 
                    if value is not None and key not in ["subject_code"]
                }

                subject_dal = SubjectDAL(session)

                if not await ensure_subject_unique(subject_dal, body.new_subject_code):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Предмет: {body.new_subject_code} уже существует"
                    )
                
                # Rename field new_subject_code to subject_code
                if "new_subject_code" in update_data:
                    update_data["subject_code"] = update_data.pop("new_subject_code")

                subject = await subject_dal.update_subject(
                    tg_subject_code = body.subject_code,
                    **update_data
                )

                # save changed data
                await session.commit()

                if not subject:
                    raise HTTPException(status_code=404, detail=f"Предмет: {body.subject_code} не найден")

            return ShowSubject.from_orm(subject)

        except Exception as e:
            await session.rollback()
            logger.warning(f"Изменение данных о предмете отменено (Ошибка: {e})")
            raise


@subject_router.post("/create", response_model=ShowSubject)
async def create_subject(body: CreateSubject, db: AsyncSession = Depends(get_db)):
    return await _create_new_subject(body, db)


@subject_router.get("/search/by_code/{subject_code}", response_model=ShowSubject,
                    responses={404: {"description": "Предмет не найден"}})
async def get_subject(subject_code: str, db: AsyncSession = Depends(get_db)):
    return await _get_subject(subject_code, db)


@subject_router.get("/search", response_model=list[ShowSubject], responses={404: {"description": "Предметы не найдены"}})
async def get_all_subjects(query_param: Annotated[QueryParams, Depends()], db: AsyncSession = Depends(get_db)):
    return await _get_all_subjects(query_param.page, query_param.limit, db)


@subject_router.get("/search/by_name/{name}", response_model=list[ShowSubject], responses={404: {"description": "Предметы не найдены"}})
async def get_all_subjects(name: str, query_param: Annotated[QueryParams, Depends()], db: AsyncSession = Depends(get_db)):
    return await _get_all_subjects_by_name(name, query_param.page, query_param.limit, db)


@subject_router.put("/delete/{subject_code}", response_model=ShowSubject,
                    responses={404: {"description": "Предмет не найден"}})
async def delete_subject(subject_code: str, db: AsyncSession = Depends(get_db)):
    return await _delete_subject(subject_code, db)


@subject_router.put("/update", response_model=ShowSubject, responses={404: {"description": "Предмет не найден"}})
async def update_subject(body: UpdateSubject, db: AsyncSession = Depends(get_db)):
    return await _update_subject(body, db)


'''
=====================================
CRUD operations for EmploymentTeacher
=====================================
'''


async def _create_new_employment(body: CreateEmployment, db) -> ShowEmployment:
    async with db as session:
        async with session.begin():
            employment_dal = EmployTeacherDAL(session)
            teacher_dal = TeacherDAL(session)

            # Check that the employment is unique
            # By using helpers
            if not await ensure_teacher_exists(teacher_dal, body.teacher_id):
                raise HTTPException(
                    status_code=400,
                    detail=f"Учитель: {body.teacher_id} не существует"
                )
            if not await ensure_employment_unique(employment_dal, body.date_start_period, body.date_end_period, body.teacher_id):
                raise HTTPException(
                    status_code=400,
                    detail=f"График преподавателя {body.teacher_id} начиная с {body.date_start_period} и заканчивая {body.date_end_period} уже существует"
                )

            employment = await employment_dal.create_employTeacher(
                date_start_period=body.date_start_period,
                date_end_period=body.date_end_period,
                teacher_id=body.teacher_id,
                monday=body.monday,
                tuesday=body.tuesday,
                wednesday=body.wednesday,
                thursday=body.thursday,
                friday=body.friday,
                saturday=body.saturday
            )
            return ShowEmployment.from_orm(employment)


async def _get_employment(date_start_period: date, date_end_period: date, teacher_id: int, db) -> ShowEmployment:
    async with db as session:
        async with session.begin(): 
            employment_dal = EmployTeacherDAL(session)
            employment = await employment_dal.get_employTeacher(date_start_period, date_end_period, teacher_id)

            # if curriculum doesn't exist
            if not employment:
                raise HTTPException(status_code=404, detail=f"График преподавателя {teacher_id} начиная с {date_start_period} и заканчивая {date_end_period} не найден")

            return ShowEmployment.from_orm(employment) 


async def _get_all_employments(page: int, limit: int, db) -> list[ShowEmployment]:
    async with db as session:
        async with session.begin():
            employment_dal = EmployTeacherDAL(session)
            employments = await employment_dal.get_all_employTeacher(page, limit)

            return [ShowEmployment.from_orm(employment) for employment in employments]


async def _get_all_employments_by_date(date_start_period: date, date_end_period: date, 
                                        page: int, limit: int, db) -> list[ShowEmployment]:
    async with db as session:
        async with session.begin():
            employment_dal = EmployTeacherDAL(session)
            employments = await employment_dal.get_all_employTeacher_by_date(date_start_period, date_end_period, page, limit)

            return [ShowEmployment.from_orm(employment) for employment in employments]
        

async def _delete_employment(date_start_period: date, date_end_period: date, teacher_id: int, db) -> ShowEmployment:
    async with db as session:
        try:
            async with session.begin():
                employment_dal = EmployTeacherDAL(session)
                employment = await employment_dal.delete_employTeacher(date_start_period, date_end_period, teacher_id)

                if not employment:
                    raise HTTPException(status_code=404, detail=f"График преподавателя {teacher_id} начиная с {date_start_period} и заканчивая {date_end_period} не найден")

            return ShowEmployment.from_orm(employment)

        except Exception as e:
            logger.warning(f"Удаление графика отменено (Ошибка: {e})")
            raise


async def _update_employment(body: UpdateEmployment, db) -> ShowEmployment:
    async with db as session:
        try:
            async with session.begin():
                # exclusion of None-fields from the transmitted data
                update_data = {
                    key: value for key, value in body.dict().items() 
                    if value is not None and key not in ["date_start_period", "date_end_period", "teacher_id"]
                }

                employment_dal = EmployTeacherDAL(session)
                teacher_dal = TeacherDAL(session)

                # Check that the employment is unique
                # By using helpers
                if not await ensure_teacher_exists(teacher_dal, body.new_teacher_id):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Учитель: {body.new_teacher_id} не существует"
                    )
                if not await ensure_employment_unique(employment_dal, body.new_date_start_period, body.new_date_end_period, body.new_teacher_id):
                    raise HTTPException(
                        status_code=400,
                        detail=f"График преподавателя {body.new_teacher_id} начиная с {body.new_date_start_period} и заканчивая {body.new_date_end_period} уже существует"
                    )
                
                # Rename field new_date_start_period to date_start_period
                if "new_date_start_period" in update_data:
                    update_data["date_start_period"] = update_data.pop("new_date_start_period")
                # Rename field new_date_end_period to date_end_period
                if "new_subject_code" in update_data:
                    update_data["date_end_period"] = update_data.pop("new_date_end_period")
                # Rename field new_teacher_id to teacher_id
                if "new_teacher_id" in update_data:
                    update_data["teacher_id"] = update_data.pop("new_teacher_id")

                employment = await employment_dal.update_employTeacher(
                    tg_date_start_period = body.date_start_period,
                    tg_date_end_period = body.date_end_period,
                    tg_teacher_id = body.teacher_id,
                    **update_data
                )

                # save changed data
                await session.commit()

                if not employment:
                    raise HTTPException(status_code=404, detail=f"График преподавателя {body.teacher_id} начиная с {body.date_start_period} и заканчивая {body.date_end_period} не найден")

            return ShowEmployment.from_orm(employment)

        except Exception as e:
            await session.rollback()
            logger.warning(f"Изменение данных о графике отменено (Ошибка: {e})")
            raise


@employment_router.post("/create", response_model=ShowEmployment)
async def create_employment(body: CreateEmployment, db: AsyncSession = Depends(get_db)):
    return await _create_new_employment(body, db)


@employment_router.get("/search/{teacher_id}/{date_start_period}/{date_end_period}", response_model=ShowEmployment,
                    responses={404: {"description": "График не найден"}})
async def get_employment(date_start_period: date, date_end_period: date, teacher_id: int, db: AsyncSession = Depends(get_db)):
    return await _get_employment(date_start_period, date_end_period, teacher_id, db)


@employment_router.get("/search", response_model=list[ShowEmployment], responses={404: {"description": "График не найден"}})
async def get_all_employments(query_param: Annotated[QueryParams, Depends()], db: AsyncSession = Depends(get_db)):
    return await _get_all_employments(query_param.page, query_param.limit, db)


@employment_router.get("/search/by_date/{date_start_period}/{date_end_period}", response_model=list[ShowEmployment], responses={404: {"description": "Графики не найдены"}})
async def get_all_employments_by_date(date_start_period: date, date_end_period: date, query_param: Annotated[QueryParams, Depends()], db: AsyncSession = Depends(get_db)):
    return await _get_all_employments_by_date(date_start_period, date_end_period, query_param.page, query_param.limit, db)


@employment_router.put("/delete/{teacher_id}/{date_start_period}/{date_end_period}", response_model=ShowEmployment,
                    responses={404: {"description": "График не найден"}})
async def delete_employment(date_start_period: date, date_end_period: date, teacher_id: int, db: AsyncSession = Depends(get_db)):
    return await _delete_employment(date_start_period, date_end_period, teacher_id, db)


@employment_router.put("/update", response_model=ShowEmployment, responses={404: {"description": "График не найден"}})
async def update_employment(body: UpdateEmployment, db: AsyncSession = Depends(get_db)):
    return await _update_employment(body, db)


'''
==================================
CRUD operations for TeacherRequest
==================================
'''


async def _create_new_request(body: CreateTeacherRequest, db) -> ShowTeacherRequest:
    async with db as session:
        async with session.begin():
            request_dal = TeacherRequestDAL(session)
            group_dal = GroupDAL(session)
            teacher_dal = TeacherDAL(session)
            subject_dal = SubjectDAL(session)

            # Check that the teacher, subject, group exists
            # Check that the employment is unique
            # By using helpers
            if not await ensure_teacher_exists(teacher_dal, body.teacher_id):
                raise HTTPException(
                    status_code=400,
                    detail=f"Учитель: {body.teacher_id} не существует"
                )
            if not await ensure_subject_exists(subject_dal, body.subject_code):
                raise HTTPException(
                    status_code=400,
                    detail=f"Предмет: {body.subject_code} не существует"
                )
            if not await ensure_group_exists(group_dal, body.group_name):
                raise HTTPException(
                    status_code=400,
                    detail=f"Группа: {body.group_name} не существует"
                )
            if not await ensure_request_unique(request_dal, body.date_request, body.teacher_id, body.subject_code, body.group_name):
                raise HTTPException(
                    status_code=400,
                    detail=f"Запрос преподавателя {body.teacher_id} на предмет {body.subject_code} для группы {body.group_name} на дату {body.date_request} уже существует"
                )

            request = await request_dal.create_teacherRequest(
                date_request=body.date_request,
                teacher_id=body.teacher_id,
                subject_code=body.subject_code,
                group_name=body.group_name,
                lectures_hours=body.lectures_hours,
                laboratory_hours=body.laboratory_hours,
                practice_hours=body.practice_hours
            )
            return ShowTeacherRequest.from_orm(request)


async def _get_request(date_request: date, teacher_id: int, subject_code: str, group_name: str, db) -> ShowTeacherRequest:
    async with db as session:
        async with session.begin(): 
            request_dal = TeacherRequestDAL(session)
            request = await request_dal.get_teacherRequest(date_request, teacher_id, subject_code, group_name)

            # if curriculum doesn't exist
            if not request:
                raise HTTPException(status_code=404, detail=f"Запрос преподавателя {teacher_id} на предмет {subject_code} для группы {group_name} на дату {date_request} не найден")

            return ShowTeacherRequest.from_orm(request) 


async def _get_all_requests(page: int, limit: int, db) -> list[ShowTeacherRequest]:
    async with db as session:
        async with session.begin():
            request_dal = TeacherRequestDAL(session)
            requests = await request_dal.get_all_teachersRequests(page, limit)

            return [ShowTeacherRequest.from_orm(request) for request in requests]


async def _get_all_requests_by_teacher(teacher_id: int, page: int, limit: int, db) -> list[ShowTeacherRequest]:
    async with db as session:
        async with session.begin():
            request_dal = TeacherRequestDAL(session)
            requests = await request_dal.get_all_requests_by_teacher(teacher_id, page, limit)

            return [ShowTeacherRequest.from_orm(request) for request in requests]
        

'''
GROUP!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
'''
async def _get_all_requests_by_group(teacher_id: int, page: int, limit: int, db) -> list[ShowTeacherRequest]:
    async with db as session:
        async with session.begin():
            request_dal = TeacherRequestDAL(session)
            requests = await request_dal.get_all_requests_by_teacher(teacher_id, page, limit)

            return [ShowTeacherRequest.from_orm(request) for request in requests]
        

async def _delete_request(date_request: date, teacher_id: int, subject_code: str, group_name: str, db) -> ShowTeacherRequest:
    async with db as session:
        try:
            async with session.begin():
                request_dal = TeacherRequestDAL(session)
                request = await request_dal.delete_teacherRequest(date_request, teacher_id, subject_code, group_name)

                if not request:
                    raise HTTPException(status_code=404, detail=f"Запрос преподавателя {teacher_id} на предмет {subject_code} для группы {group_name} на дату {date_request} не найден")

            return ShowTeacherRequest.from_orm(request)

        except Exception as e:
            logger.warning(f"Удаление запроса отменено (Ошибка: {e})")
            raise


async def _update_request(body: UpdateTeacherRequest, db) -> ShowTeacherRequest:
    async with db as session:
        try:
            async with session.begin():
                # exclusion of None-fields from the transmitted data
                update_data = {
                    key: value for key, value in body.dict().items() 
                    if value is not None and key not in ["date_request", "teacher_id", "subject_code", "group_name"]
                }

                request_dal = TeacherRequestDAL(session)
                group_dal = GroupDAL(session)
                teacher_dal = TeacherDAL(session)
                subject_dal = SubjectDAL(session)

                # Check that the teacher, subject, group exists
                # Check that the request is unique
                # By using helpers
                if body.new_teacher_id != None and not await ensure_teacher_exists(teacher_dal, body.new_teacher_id):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Учитель: {body.new_teacher_id} не существует"
                    )
                if body.new_subject_code != None and not await ensure_subject_exists(subject_dal, body.new_subject_code):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Предмет: {body.new_subject_code} не существует"
                    )
                if body.new_group_name != None and not await ensure_group_exists(group_dal, body.new_group_name):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Группа: {body.new_group_name} не существует"
                    )
                if not await ensure_request_unique(request_dal, body.new_date_request, body.new_teacher_id, body.new_subject_code, body.new_group_name):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Запрос преподавателя {body.new_teacher_id} на предмет {body.new_subject_code} для группы {body.new_group_name} на дату {body.new_date_request} уже существует"
                    )
                
                # Rename field new_date_request to date_request
                if "new_date_request" in update_data:
                    update_data["date_request"] = update_data.pop("new_date_request")
                # Rename field new_teacher_id to teacher_id
                if "new_teacher_id" in update_data:
                    update_data["teacher_id"] = update_data.pop("new_teacher_id")
                # Rename field new_subject_code to subject_code
                if "new_subject_code" in update_data:
                    update_data["subject_code"] = update_data.pop("new_subject_code")
                # Rename field new_group_name to group_name
                if "new_group_name" in update_data:
                    update_data["group_name"] = update_data.pop("new_group_name")

                request = await request_dal.update_teacherRequest(
                    tg_date_request = body.date_request,
                    tg_teacher_id = body.teacher_id,
                    tg_subject_code = body.subject_code,
                    tg_group_name = body.group_name,
                    **update_data
                )

                # save changed data
                await session.commit()

                if not request:
                    raise HTTPException(status_code=404, detail=f"Запрос преподавателя {body.teacher_id} на предмет {body.subject_code} для группы {body.group_name} на дату {body.date_request} не найден")

            return ShowTeacherRequest.from_orm(request)

        except Exception as e:
            await session.rollback()
            logger.warning(f"Изменение данных о запросе отменено (Ошибка: {e})")
            raise


@request_router.post("/create", response_model=ShowTeacherRequest)
async def create_request(body: CreateTeacherRequest, db: AsyncSession = Depends(get_db)):
    return await _create_new_request(body, db)


@request_router.get("/search/{date_request}/{teacher_id}/{subject_code}/{group_name}", response_model=ShowTeacherRequest,
                    responses={404: {"description": "Запрос не найден"}})
async def get_request(date_request: date, teacher_id: int, subject_code: str, group_name: str, db: AsyncSession = Depends(get_db)):
    return await _get_request(date_request, teacher_id, subject_code, group_name, db)


@request_router.get("/search", response_model=list[ShowTeacherRequest], responses={404: {"description": "Запрос не найден"}})
async def get_all_requests(query_param: Annotated[QueryParams, Depends()], db: AsyncSession = Depends(get_db)):
    return await _get_all_requests(query_param.page, query_param.limit, db)


@request_router.get("/search/by_teacher/{teacher_id}", 
                    response_model=list[ShowTeacherRequest], responses={404: {"description": "Запросы не найдены"}})
async def get_all_requests_by_teacher(teacher_id: int, query_param: Annotated[QueryParams, Depends()], db: AsyncSession = Depends(get_db)):
    return await _get_all_requests_by_teacher(teacher_id, query_param.page, query_param.limit, db)


'''
GROUP!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
'''
@request_router.get("/search/by_group/{group_name}", 
                    response_model=list[ShowTeacherRequest], responses={404: {"description": "Запросы не найдены"}})
async def get_all_requests_by_teacher(group_name: str, teacher_id: int, query_param: Annotated[QueryParams, Depends()], db: AsyncSession = Depends(get_db)):
    return await _get_all_requests_by_teacher(group_name, teacher_id, query_param.page, query_param.limit, db)


@request_router.put("/delete/{date_request}/{teacher_id}/{subject_code}/{group_name}", response_model=ShowTeacherRequest,
                    responses={404: {"description": "Запрос не найден"}})
async def delete_request(date_request: date, teacher_id: int, subject_code: str, group_name: str, db: AsyncSession = Depends(get_db)):
    return await _delete_request(date_request, teacher_id, subject_code, group_name, db)


@request_router.put("/update", response_model=ShowTeacherRequest, responses={404: {"description": "Запрос не найден"}})
async def update_request(body: UpdateTeacherRequest, db: AsyncSession = Depends(get_db)):
    return await _update_request(body, db)


'''
===========================
CRUD operations for Session
===========================
'''


async def _create_new_session(body: CreateSession, db) -> ShowSession:
    async with db as session:
        async with session.begin():
            session_dal = SessionDAL(session)
            group_dal = GroupDAL(session)
            cabinet_dal = CabinetDAL(session)
            subject_dal = SubjectDAL(session)
            teacher_dal = TeacherDAL(session)

            # Check that the group, subject, teacher, cabinet exists
            # Check that the employment is unique
            # By using helpers
            if not await ensure_group_exists(group_dal, body.group_name):
                raise HTTPException(
                    status_code=400,
                    detail=f"Группа: {body.group_name} не существует"
                )    
            if  body.subject_code != None and not await ensure_subject_exists(subject_dal, body.subject_code):
                raise HTTPException(
                    status_code=400,
                    detail=f"Предмет: {body.subject_code} не существует"
                )
            if body.teacher_id != None and not await ensure_teacher_exists(teacher_dal, body.teacher_id):
                raise HTTPException(
                    status_code=400,
                    detail=f"Преподаватель: {body.teacher_id} не существует"
                )     
            if body.cabinet_number != None and body.building_number != None and not await ensure_cabinet_exists(cabinet_dal, body.cabinet_number, body.building_number):
                raise HTTPException(
                    status_code=400,
                    detail=f"Кабинет: {body.cabinet_number} в здании номер: {body.building_number} не существует"
                )
            if not await ensure_session_unique(session_dal, body.session_number, body.date, body.group_name):
                raise HTTPException(
                    status_code=400,
                    detail=f"Сессия у преподавателя под номером {body.session_number} для группы {body.group_name} на дату {body.date} уже существует"
                )

            session = await session_dal.create_session(
            session_number=body.session_number,
            date=body.date,
            group_name=body.group_name,
            session_type=body.session_type,
            subject_code=body.subject_code,
            teacher_id=body.teacher_id,
            cabinet_number=body.cabinet_number,
            building_number=body.building_number
            )
            return ShowSession.from_orm(session)


async def _get_session(session_number: int, date: date, group_name: str, db) -> ShowSession:
    async with db as session:
        async with session.begin(): 
            session_dal = SessionDAL(session)
            data_session = await session_dal.get_session(session_number, date, group_name)

            # if session doesn't exist
            if not data_session:
                raise HTTPException(status_code=404, detail=f"Сессия у преподавателя под номером {session_number} для группы {group_name} на дату {date} уже существует")

            return ShowSession.from_orm(data_session) 


async def _get_all_sessions(page: int, limit: int, db) -> list[ShowSession]:
    async with db as session:
        async with session.begin():
            session_dal = SessionDAL(session)
            data_sessions = await session_dal.get_all_sessions(page, limit)

            return [ShowSession.from_orm(data_session) for data_session in data_sessions]


async def _get_all_sessions_by_date(date: date, page: int, limit: int, db) -> list[ShowSession]:
    async with db as session:
        async with session.begin():
            session_dal = SessionDAL(session)
            data_sessions = await session_dal.get_all_sessions_by_date(date, page, limit)

            return [ShowSession.from_orm(data_session) for data_session in data_sessions]
        

async def _get_all_sessions_by_teacher(teacher_id: int, page: int, limit: int, db) -> list[ShowSession]:
    async with db as session:
        async with session.begin():
            session_dal = SessionDAL(session)
            data_sessions = await session_dal.get_all_sessions_by_teacher(teacher_id, page, limit)

            return [ShowSession.from_orm(data_session) for data_session in data_sessions]
        

async def _get_all_sessions_by_group(group_name: str, page: int, limit: int, db) -> list[ShowSession]:
    async with db as session:
        async with session.begin():
            session_dal = SessionDAL(session)
            data_sessions = await session_dal.get_all_sessions_by_group(group_name, page, limit)

            return [ShowSession.from_orm(data_session) for data_session in data_sessions]
        

async def _delete_session(session_number: int, date: date, group_name: str, db) -> ShowSession:
    async with db as session:
        try:
            async with session.begin():
                session_dal = SessionDAL(session)
                data_session = await session_dal.delete_session(session_number, date, group_name)

                if not session:
                    raise HTTPException(status_code=404, detail=f"Сессия у преподавателя под номером {session_number} для группы {group_name} на дату {date} не найден")

            return ShowSession.from_orm(data_session)

        except Exception as e:
            logger.warning(f"Удаление сессии отменено (Ошибка: {e})")
            raise


async def _update_session(body: UpdateSession, db) -> ShowSession:
    async with db as session:
        try:
            async with session.begin():
                # exclusion of None-fields from the transmitted data
                update_data = {
                    key: value for key, value in body.dict().items() 
                    if value is not None and key not in ["session_number", "session_date", "group_name"]
                }

                session_dal = SessionDAL(session)
                group_dal = GroupDAL(session)
                cabinet_dal = CabinetDAL(session)
                subject_dal = SubjectDAL(session)
                teacher_dal = TeacherDAL(session)

                # Check that the group, subject, teacher, cabinet exists
                # Check that the employment is unique
                # By using helpers
                if not await ensure_group_exists(group_dal, body.new_group_name):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Группа: {body.new_group_name} не существует"
                    )    
                if body.subject_code != None and not await ensure_subject_exists(subject_dal, body.subject_code):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Предмет: {body.subject_code} не существует"
                    )
                if body.teacher_id != None and not await ensure_teacher_exists(teacher_dal, body.teacher_id):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Преподаватель: {body.teacher_id} не существует"
                    )     
                if body.cabinet_number != None and body.building_number != None and not await ensure_cabinet_exists(cabinet_dal, body.cabinet_number, body.building_number):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Кабинет: {body.cabinet_number} в здании номер: {body.building_number} не существует"
                    )
                
                # Rename field new_session_number to session_number
                if "new_session_number" in update_data:
                    update_data["session_number"] = update_data.pop("new_session_number")
                # Rename field new_session_date to date
                if "new_session_date" in update_data:
                    update_data["date"] = update_data.pop("new_session_date")
                # Rename field new_group_name to group_name
                if "new_group_name" in update_data:
                    update_data["group_name"] = update_data.pop("new_group_name")

                session_data = await session_dal.update_session(
                    tg_session_number = body.session_number,
                    tg_date = body.session_date,
                    tg_group_name = body.group_name,
                    **update_data
                )

                # save changed data
                await session.commit()

                if not session:
                    raise HTTPException(status_code=404, detail=f"Сессия под номером {body.session_number} для группы {body.group_name} на дату {body.session_date} не найдена")

            return ShowSession.from_orm(session_data)

        except Exception as e:
            await session.rollback()
            logger.warning(f"Изменение данных о сессии отменено (Ошибка: {e})")
            raise


@session_router.post("/create", response_model=ShowSession)
async def create_session(body: CreateSession, db: AsyncSession = Depends(get_db)):
    return await _create_new_session(body, db)


@session_router.get("/search/{session_number}/{date}/{group_name}", response_model=ShowSession,
                    responses={404: {"description": "Сессия не найдена"}})
async def get_session(session_number: int, date: date, group_name: str, db: AsyncSession = Depends(get_db)):
    return await _get_session(session_number, date, group_name, db)


@session_router.get("/search", response_model=list[ShowSession], responses={404: {"description": "Сессия не найдена"}})
async def get_all_sessions(query_param: Annotated[QueryParams, Depends()], db: AsyncSession = Depends(get_db)):
    return await _get_all_sessions(query_param.page, query_param.limit, db)


@session_router.get("/search/by_date/{date}", 
                    response_model=list[ShowSession], responses={404: {"description": "Сессии не найдены"}})
async def get_all_session_by_date(date: date, query_param: Annotated[QueryParams, Depends()], db: AsyncSession = Depends(get_db)):
    return await _get_all_sessions_by_date(date, query_param.page, query_param.limit, db)


@session_router.get("/search/by_teacher/{teacher_id}", 
                    response_model=list[ShowSession], responses={404: {"description": "Сессии не найдены"}})
async def get_all_session_by_date(teacher_id: int, query_param: Annotated[QueryParams, Depends()], db: AsyncSession = Depends(get_db)):
    return await _get_all_sessions_by_teacher(teacher_id, query_param.page, query_param.limit, db)


@session_router.get("/search/by_group/{group_name}", 
                    response_model=list[ShowSession], responses={404: {"description": "Сессии не найдены"}})
async def get_all_session_by_date(group_name: str, query_param: Annotated[QueryParams, Depends()], db: AsyncSession = Depends(get_db)):
    return await _get_all_sessions_by_group(group_name, query_param.page, query_param.limit, db)


@session_router.put("/delete/{session_number}/{date}/{group_name}", response_model=ShowSession,
                    responses={404: {"description": "Сессия не найдена"}})
async def delete_session(session_number: int, date: date, group_name: str, db: AsyncSession = Depends(get_db)):
    return await _delete_session(session_number, date, group_name, db)


@session_router.put("/update", response_model=ShowSession, responses={404: {"description": "Сессия не найдена"}})
async def update_session(body: UpdateSession, db: AsyncSession = Depends(get_db)):
    return await _update_session(body, db)
