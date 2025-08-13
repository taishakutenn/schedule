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
============================
CRUD operations for teachers
============================
'''


# async def _create_new_teacher(body: CreateTeacher, db) -> ShowTeacher:
#     async with db as session:
#         async with session.begin():
#             teacher_dal = TeacherDAL(session)
#             teacher = await teacher_dal.create_teacher(
#                 name=body.name,
#                 surname=body.surname,
#                 phone_number=body.phone_number,
#                 email=str(body.email),
#                 fathername=body.fathername
#             )
#             return ShowTeacher.from_orm(teacher)
        

async def _create_new_teacher(body: CreateTeacher, request:Request, db) -> ShowTeacherWithHATEOAS:
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
                    "self": f'{api_base_url}/teachers/{teacher_id}',
                    "update": f'{api_base_url}/teachers/{teacher_id}',
                    "delete": f'{api_base_url}/teachers/{teacher_id}',
                    "teachers": f'{api_base_url}/teachers'
                }
                # teacher_pydantic.links = hateoas_links

                return ShowTeacherWithHATEOAS(teacher=teacher_pydantic, links=hateoas_links)
            
            except IntegrityError as e:
                await session.rollback()

                #???????????????????????????????????????????????????????????????????????????????????????????????????
                # ДОДЕЛАТЬ
                #???????????????????????????????????????????????????????????????????????????????????????????????????

                if "email" in str(e.orig).lower():
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Учитель с таким email уже существует.")
                elif "phone_number" in str(e.orig).lower():
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Учитель с таким номером телефона уже существует.")
                else:
                    logger.error(f"Ошибка целостности БД при создании учителя: {e}")
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Невозможно создать учителя из-за конфликта данных.")
                     
            except Exception as e:
                 await session.rollback()
                 logger.error(f"Неожиданная ошибка при создании учителя: {e}")
                 raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка сервера.")


async def _get_teacher_by_id(teacher_id, db) -> ShowTeacher:
    async with db as session:
        async with session.begin():
            teacher_dal = TeacherDAL(session)
            teacher = await teacher_dal.get_teacher_by_id(teacher_id)

            # if teacher doesn't exist
            if not teacher:
                raise HTTPException(status_code=404, detail=f"Учитель с id: {teacher_id} не найден")

            return ShowTeacher.from_orm(teacher)


async def _get_teacher_by_name_and_surname(name, surname, db) -> ShowTeacher:
    async with db as session:
        async with session.begin():
            teacher_dal = TeacherDAL(session)
            teacher = await teacher_dal.get_teacher_by_name_surname(name, surname)

            # if teacher exist
            if not teacher:
                raise HTTPException(status_code=404, detail=f"Учитель {name, surname} не найден")

            return ShowTeacher.from_orm(teacher)


async def _get_all_teachers(page: int, limit: int, db) -> list[ShowTeacher]:
    async with db as session:
        async with session.begin():
            teacher_dal = TeacherDAL(session)
            teachers = await teacher_dal.get_all_teachers(page, limit)

            # If you need to return a list of objects
            # and they were not found,
            # then we return an empty list instead of 404.
            # We return 404 when a specific object was not found.
            return [ShowTeacher.from_orm(teacher) for teacher in teachers]


async def _delete_teacher(teacher_id: int, db) -> ShowTeacher:
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
                    raise HTTPException(status_code=404, detail=f"Учитель с id: {teacher_id} не найден")

            return ShowTeacher.from_orm(teacher)

        except Exception as e:
            logger.warning(f"Удаление учителя отменено (Ошибка: {e})")
            raise


async def _update_teacher(body: UpdateTeacher, db) -> ShowTeacher:
    """Use it for the same reasons as for the delete operation"""
    async with db as session:
        try:
            async with session.begin():
                # exclusion of None-fields from the transmitted data
                update_data = {
                    key: value for key, value in body.dict().items() if value is not None and key != "teacher_id"
                }

                # change data
                teacher_dal = TeacherDAL(session)
                teacher = await teacher_dal.update_teacher(
                    id=body.teacher_id,
                    **update_data
                )

                if not teacher:
                    raise HTTPException(status_code=404, detail=f"Учитель с id: {body.teacher_id} не найден")

            return ShowTeacher.from_orm(teacher)

        except Exception as e:
            await session.rollback()
            logger.warning(f"Изменение данных об учителе отменено (Ошибка: {e})")
            raise


# @teacher_router.post("/create", response_model=ShowTeacher)
# async def create_teacher(body: CreateTeacher, db: AsyncSession = Depends(get_db)):
#     return await _create_new_teacher(body, db)

@teacher_router.post("/", response_model=ShowTeacherWithHATEOAS, status_code=status.HTTP_201_CREATED) # 201 Created standard code
async def create_teacher(body: CreateTeacher, request: Request, db: AsyncSession = Depends(get_db)):
    return await _create_new_teacher(body, request, db)


@teacher_router.get("/search/by_id/{teacher_id}", response_model=ShowTeacher,
                    responses={404: {"description": "Учитель не найден"}})
async def get_teacher_by_id(teacher_id: int, db: AsyncSession = Depends(get_db)):
    return await _get_teacher_by_id(teacher_id, db)


@teacher_router.get("/search/by_humanity", response_model=ShowTeacher,
                    responses={404: {"description": "Учитель не найден"}})
async def get_teacher_by_name_and_surname(name: str, surname: str, db: AsyncSession = Depends(get_db)):
    return await _get_teacher_by_name_and_surname(name, surname, db)


@teacher_router.get("/search", response_model=list[ShowTeacher], responses={404: {"description": "Учителя не найдены"}})
async def get_all_teachers(query_param: Annotated[QueryParams, Depends()], db: AsyncSession = Depends(get_db)):
    """
    query_param set via Annotated so that fastapi understands
    that the pydantic model QueryParam refers to the query parameters,
    we specify this as the second argument for Annotated.
    Wherever there will be pagination and the number of elements on the page,
    it is better to use this pydantic model, so as not to manually enter these parameters each time.
    Link to documentation: https://fastapi.tiangolo.com/ru/tutorial/query-param-models/
    """
    return await _get_all_teachers(query_param.page, query_param.limit, db)


@teacher_router.put("/delete/{teacher_id}", response_model=ShowTeacher,
                    responses={404: {"description": "Учитель не найден"}})
async def delete_teacher(teacher_id: int, db: AsyncSession = Depends(get_db)):
    return await _delete_teacher(teacher_id, db)


@teacher_router.put("/update", response_model=ShowTeacher, responses={404: {"description": "Учитель не найден"}})
async def update_teacher(body: UpdateTeacher, db: AsyncSession = Depends(get_db)):
    return await _update_teacher(body, db)


'''
=============================
CRUD operations for buildings
=============================
'''


async def _create_new_building(body: CreateBuilding, db) -> ShowBuilding:
    async with db as session:
        async with session.begin():
            building_dal = BuildingDAL(session)
            building = await building_dal.create_building(
                building_number=body.building_number,
                city=body.city,
                building_address=body.building_address
            )

            return ShowBuilding.from_orm(building)


async def _get_building_by_number(number, db) -> ShowBuilding:
    async with db as session:
        async with session.begin():
            building_dal = BuildingDAL(session)
            building = await building_dal.get_building_by_number(number)

            # if building exist
            if not building:
                raise HTTPException(status_code=404, detail=f"Здание с номером: {number} не найдено")

            return ShowBuilding.from_orm(building)


async def _get_building_by_address(address, db) -> ShowBuilding:
    async with db as session:
        async with session.begin():
            building_dal = BuildingDAL(session)
            building = await building_dal.get_building_by_address(address)

            # if building exist
            if not building:
                raise HTTPException(status_code=404, detail=f"Здание по адресу: {address} не найдено")

            return ShowBuilding.from_orm(building)


async def _get_all_buildings(page: int, limit: int, db) -> list[ShowBuilding]:
    async with db as session:
        async with session.begin():
            building_dal = BuildingDAL(session)
            buildings = await building_dal.get_all_buildings(page, limit)

            return [ShowBuilding.from_orm(building) for building in buildings]


async def _delete_building(building_number: int, db) -> ShowBuilding:
    async with db as session:
        try:
            async with session.begin():
                building_dal = BuildingDAL(session)
                building = await building_dal.delete_building(building_number)
                # save changed data
                await session.commit()

                if not building:
                    raise HTTPException(status_code=404, detail=f"Здание с номером: {building_number} не найдено")

                return ShowBuilding.from_orm(building)

        except Exception as e:
            logger.warning(f"Удаление данных о здании отменено (Ошибка: {e})")
            raise e


async def _update_building(body: UpdateBuilding, db) -> ShowBuilding:
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

                # save changed data
                await session.commit()

                if not building:
                    raise HTTPException(status_code=404, detail=f"Здание с номером: {body.building_number} не найдено")

                return ShowBuilding.from_orm(building)

        except Exception as e:
            await session.rollback()
            logger.warning(f"Изменение данных о здании отменено (Ошибка: {e})")
            raise e


@building_router.post("/create", response_model=ShowBuilding)
async def create_building(body: CreateBuilding, db: AsyncSession = Depends(get_db)):
    return await _create_new_building(body, db)


@building_router.get("/search/by_number/{building_number}", response_model=ShowBuilding,
                     responses={404: {"description": "Здание не найдено"}})
async def get_building_by_number(building_number: int, db: AsyncSession = Depends(get_db)):
    return await _get_building_by_number(building_number, db)


@building_router.get("/search/by_address", response_model=ShowBuilding | None,
                     responses={404: {"description": "Здание не найдено"}})
async def get_building_by_address(address: str, db: AsyncSession = Depends(get_db)):
    return await _get_building_by_address(address, db)


@building_router.get("/search", response_model=list[ShowBuilding])
async def get_all_buildings(query_param: Annotated[QueryParams, Depends()], db: AsyncSession = Depends(get_db)):
    """
    query_param set via Annotated so that fastapi understands
    that the pydantic model QueryParam refers to the query parameters,
    we specify this as the second argument for Annotated.
    Wherever there will be pagination and the number of elements on the page,
    it is better to use this pydantic model, so as not to manually enter these parameters each time.
    Link to documentation: https://fastapi.tiangolo.com/ru/tutorial/query-param-models/
    """
    return await _get_all_buildings(query_param.page, query_param.limit, db)


@building_router.put("/delete/{building_number}", response_model=ShowBuilding,
                     responses={404: {"description": "Здание не найдено"}})
async def delete_building(building_number: int, db: AsyncSession = Depends(get_db)):
    return await _delete_building(building_number, db)


@building_router.put("/update", response_model=ShowBuilding, responses={404: {"description": "Здание не найдено"}})
async def update_building(body: UpdateBuilding, db: AsyncSession = Depends(get_db)):
    return await _update_building(body, db)


'''
============================
CRUD operations for cabinets
============================
'''


async def _create_cabinet(body: CreateCabinet, db) -> ShowCabinet:
    async with db as session:
        async with session.begin():
            building_dal = BuildingDAL(session)
            cabinet_dal = CabinetDAL(session)

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
            new_cabinet = await cabinet_dal.create_cabinet(
                cabinet_number=body.cabinet_number,
                building_number=body.building_number,
                capacity=body.capacity,
                cabinet_state=body.cabinet_state
            )

            return ShowCabinet.from_orm(new_cabinet)


async def _get_all_cabinets(page: int, limit: int, db) -> list[ShowCabinet]:
    async with db as session:
        async with session.begin():
            cabinet_dal = CabinetDAL(session)
            cabinets = await cabinet_dal.get_all_cabinets(page, limit)

            return [ShowCabinet.from_orm(cabinet) for cabinet in cabinets]


async def _get_cabinets_by_building(building_number: int, page: int, limit: int, db) -> list[ShowCabinet]:
    async with db as session:
        async with session.begin():
            cabinet_dal = CabinetDAL(session)
            cabinets = await cabinet_dal.get_cabinets_by_building(building_number, page, limit)

            return [ShowCabinet.from_orm(cabinet) for cabinet in cabinets]


async def _get_cabinet_by_building_and_number(building_number: int, cabinet_number: int, db) -> ShowCabinet:
    async with db as session:
        async with session.begin():
            cabinet_dal = CabinetDAL(session)
            cabinet = await cabinet_dal.get_cabinet_by_number_and_building(building_number, cabinet_number)

            if not cabinet:
                raise HTTPException(status_code=404,
                                    detail=f"Кабинет с номером: {cabinet_number} в здании с номером: {building_number} - не найден")

            return ShowCabinet.from_orm(cabinet)


async def _delete_cabinet(building_number: int, cabinet_number: int, db) -> ShowCabinet:
    async with db as session:
        async with session.begin():
            cabinet_dal = CabinetDAL(session)
            cabinet = await cabinet_dal.delete_cabinet(building_number, cabinet_number)

            if not cabinet:
                raise HTTPException(status_code=404,
                                    detail=f"Кабинет с номером: {cabinet_number} в здании {building_number} не может быть удалён, т.к. не найден")

            return ShowCabinet.from_orm(cabinet)


async def _update_cabinet(body: UpdateCabinet, db) -> ShowCabinet:
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

                return ShowCabinet.from_orm(updated_cabinet)

        # Because "Exception" will catch and the api route will not return an error when updating
        except HTTPException as e:
            raise e
        except Exception as e:
            await session.rollback()
            logger.warning(f"Изменение данных о кабинете отменено (Ошибка: {e})")
            raise HTTPException(status_code=500, detail="Произошла непредвиденная ошибка")


@cabinet_router.post("/create", response_model=ShowCabinet)
async def create_cabinet(body: CreateCabinet, db: AsyncSession = Depends(get_db)):
    return await _create_cabinet(body, db)


@cabinet_router.get("/search", response_model=list[ShowCabinet])
async def get_all_cabinets(query_param: Annotated[QueryParams, Depends()], db: AsyncSession = Depends(get_db)):
    return await _get_all_cabinets(query_param.page, query_param.limit, db)


@cabinet_router.get("/search/by_building/{building_number}", response_model=list[ShowCabinet])
async def get_cabinets_by_building(building_number: int,
                                   query_param: Annotated[QueryParams, Depends()],
                                   db: AsyncSession = Depends(get_db)):
    return await _get_cabinets_by_building(building_number, query_param.page, query_param.limit, db)


@cabinet_router.get("/search/by_building_and_number", response_model=ShowCabinet,
                    responses={404: {"description": "Кабинет не найден"}})
async def get_cabinet_by_building_and_number(building_number: int,
                                             cabinet_number: int,
                                             db: AsyncSession = Depends(get_db)):
    return await _get_cabinet_by_building_and_number(building_number, cabinet_number, db)


@cabinet_router.put("/delete/{building_number}/{cabinet_number}", response_model=ShowCabinet,
                    responses={404: {"description": "Не удаётся удалить кабинет"}})
async def delete_cabinet(building_number: int, cabinet_number: int, db: AsyncSession = Depends(get_db)):
    return await _delete_cabinet(building_number, cabinet_number, db)


@cabinet_router.put("/update", response_model=ShowCabinet,
                    responses={404: {"description": "Кабинет не найден или нет возможности изменить его параметры"}})
async def update_cabinet(body: UpdateCabinet, db: AsyncSession = Depends(get_db)):
    return await _update_cabinet(body, db)


'''
==============================
CRUD operations for speciality
==============================
'''


async def _create_speciality(body: CreateSpeciality, db) -> ShowSpeciality:
    async with db as session:
        async with session.begin():
            speciality_dal = SpecialityDAL(session)
            new_speciality = await speciality_dal.create_speciality(speciality_code=body.speciality_code)

            return ShowSpeciality.from_orm(new_speciality)


async def _get_all_specialties(page: int, limit: int, db) -> list[ShowSpeciality]:
    async with db as session:
        async with session.begin():
            speciality_dal = SpecialityDAL(session)
            specialities = await speciality_dal.get_all_specialties(page, limit)

            return [ShowSpeciality.from_orm(speciality) for speciality in specialities]


async def _get_speciality(speciality_code: str, db) -> list[ShowSpeciality]:
    async with db as session:
        async with session.begin():
            speciality_dal = SpecialityDAL(session)
            speciality = await speciality_dal.get_speciality(speciality_code)

            # if speciality doesn't exist
            if not speciality:
                raise HTTPException(status_code=404, detail=f"Специальность с кодом: {speciality_code} не найдена")

            return ShowSpeciality.from_orm(speciality)


async def _delete_speciality(speciality_code: str, db) -> ShowSpeciality:
    async with db as session:
        async with session.begin():
            speciality_dal = SpecialityDAL(session)
            speciality = await speciality_dal.delete_speciality(speciality_code)

            if not speciality:
                raise HTTPException(status_code=404,
                                    detail=f"Специальность с кодом: {speciality_code} не может быть удалена, т.к. не найдена")

            return ShowSpeciality.from_orm(speciality)


async def _update_speciality(body: UpdateSpeciality, db) -> ShowSpeciality:
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
                updated_speciality = await speciality_dal.update_speciality(
                    target_code=body.speciality_code, 
                    **update_data
                    )
                
                # save changed data
                await session.commit()

                if not updated_speciality:
                    raise HTTPException(status_code=404, detail="Специальность не была обновлена")

                return ShowSpeciality.from_orm(updated_speciality)

        # Because "Exception" will catch and the api route will not return an error when updating
        except HTTPException as e:
            raise e
        except Exception as e:
            await session.rollback()
            logger.warning(f"Изменение данных о специальности отменено (Ошибка: {e})")
            raise HTTPException(status_code=500, detail="Произошла непредвиденная ошибка")


@speciality_router.post("/create", response_model=ShowSpeciality)
async def create_speciality(body: CreateSpeciality, db: AsyncSession = Depends(get_db)):
    return await _create_speciality(body, db)


@speciality_router.get("/search", response_model=list[ShowSpeciality])
async def get_all_specialities(query_param: Annotated[QueryParams, Depends()], db: AsyncSession = Depends(get_db)):
    return await _get_all_specialties(query_param.page, query_param.limit, db)


@speciality_router.get("/search/by_speciality_code", response_model=ShowSpeciality,
                    responses={404: {"description": "Специальность не найдена"}})
async def get_speciality_by_code(speciality_code: str, db: AsyncSession = Depends(get_db)):
    return await _get_speciality(speciality_code, db)


@speciality_router.put("/delete/{speciality_code}", response_model=ShowSpeciality,
                    responses={404: {"description": "Не удаётся удалить специальность"}})
async def delete_speciality(speciality_code: str, db: AsyncSession = Depends(get_db)):
    return await _delete_speciality(speciality_code, db)


@speciality_router.put("/update", response_model=ShowSpeciality,
                    responses={404: {"description": "Специальность не найдена или нет возможности изменить её параметры"}})
async def update_speciality(body: UpdateSpeciality, db: AsyncSession = Depends(get_db)):
    return await _update_speciality(body, db)


'''
=========================
CRUD operations for group
=========================
'''


async def _create_new_group(body: CreateGroup, db) -> ShowGroup:
    async with db as session:
        async with session.begin():
            group_dal = GroupDAL(session)
            teacher_dal = TeacherDAL(session)
            speciality_dal = SpecialityDAL(session)

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
            return ShowGroup.from_orm(group)


async def _get_group_by_name(group_name: str, db) -> ShowGroup:
    async with db as session:
        async with session.begin(): 
            group_dal = GroupDAL(session)
            group = await group_dal.get_group(group_name)

            # if group doesn't exist
            if not group:
                raise HTTPException(status_code=404, detail=f"Группа с названием: {group_name} не найдена")

            return ShowGroup.from_orm(group) 


async def _get_all_groups(page: int, limit: int, db) -> list[ShowGroup]:
    async with db as session:
        async with session.begin():
            group_dal = GroupDAL(session)
            groups = await group_dal.get_all_groups(page, limit)

            return [ShowGroup.from_orm(group) for group in groups]
        

async def _get_all_groups_by_speciality(speciality_code: str, page: int, limit: int, db) -> list[ShowGroup]:
    async with db as session:
        async with session.begin():
            group_dal = GroupDAL(session)
            speciality_dal = SpecialityDAL(session)

            if not await ensure_speciality_exists(speciality_dal, speciality_code):
                raise HTTPException(
                    status_code=404,
                    detail=f"Специальность с кодом {speciality_code} не найдена"
                )

            groups = await group_dal.get_all_groups_by_speciality(speciality_code, page, limit)

            return [ShowGroup.from_orm(group) for group in groups]


async def _delete_group(group_name: str, db) -> ShowGroup:
    async with db as session:
        try:
            async with session.begin():
                group_dal = GroupDAL(session)
                group = await group_dal.delete_group(group_name)

                if not group:
                    raise HTTPException(status_code=404, detail=f"Группа с названием: {group_name} не найдена")

            return ShowGroup.from_orm(group)

        except Exception as e:
            logger.warning(f"Удаление группы отменено (Ошибка: {e})")
            raise


async def _update_group(body: UpdateGroup, db) -> ShowGroup:
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

                # save changed data
                await session.commit()

                if not group:
                    raise HTTPException(status_code=404, detail=f"Группа с названием: {body.group_name} не найдена")

            return ShowGroup.from_orm(group)

        except Exception as e:
            await session.rollback()
            logger.warning(f"Изменение данных о группе отменено (Ошибка: {e})")
            raise


@group_router.post("/create", response_model=ShowGroup)
async def create_group(body: CreateGroup, db: AsyncSession = Depends(get_db)):
    return await _create_new_group(body, db)


@group_router.get("/search/by_group_name/{group_name}", response_model=ShowGroup,
                    responses={404: {"description": "Группа не найдена"}})
async def get_group_by_name(group_name: str, db: AsyncSession = Depends(get_db)):
    return await _get_group_by_name(group_name, db)


@group_router.get("/search", response_model=list[ShowGroup], responses={404: {"description": "Группы не найдены"}})
async def get_all_groups(query_param: Annotated[QueryParams, Depends()], db: AsyncSession = Depends(get_db)):
    return await _get_all_groups(query_param.page, query_param.limit, db)


@group_router.get("/search/by_speciality/{speciality_code}", response_model=list[ShowGroup], responses={404: {"description": "Группы не найдены"}})
async def get_all_groups_by_speciality(speciality_code: str, query_param: Annotated[QueryParams, Depends()], db: AsyncSession = Depends(get_db)):
    return await _get_all_groups_by_speciality(speciality_code, query_param.page, query_param.limit, db)


@group_router.put("/delete/{group_name}", response_model=ShowGroup,
                    responses={404: {"description": "Группа не найдена"}})
async def delete_group(group_name: str, db: AsyncSession = Depends(get_db)):
    return await _delete_group(group_name, db)


@group_router.put("/update", response_model=ShowGroup, responses={404: {"description": "Группа не найдена"}})
async def update_group(body: UpdateGroup, db: AsyncSession = Depends(get_db)):
    return await _update_group(body, db)


'''
==============================
CRUD operations for curriculum
==============================
'''


async def _create_new_curriculum(body: CreateCurriculum, db) -> ShowCurriculum:
    async with db as session:
        async with session.begin():
            group_dal = GroupDAL(session)
            subject_dal = SubjectDAL(session)
            curriculum_dal = CurriculumDAL(session)

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
            return ShowCurriculum.from_orm(curriculum)


async def _get_curriculum(semester_number: int, group_name: str, subject_code: str, db) -> ShowCurriculum:
    async with db as session:
        async with session.begin(): 
            curriculum_dal = CurriculumDAL(session)
            curriculum = await curriculum_dal.get_curriculum(semester_number, group_name, subject_code)

            # if curriculum doesn't exist
            if not curriculum:
                raise HTTPException(status_code=404, detail=f"План для предмета: {subject_code} в группе: {group_name} на семестр: {semester_number} не найден")

            return ShowCurriculum.from_orm(curriculum) 


async def _get_all_curriculums(page: int, limit: int, db) -> list[ShowCurriculum]:
    async with db as session:
        async with session.begin():
            curriculum_dal = CurriculumDAL(session)
            curriculums = await curriculum_dal.get_all_curriculums(page, limit)

            return [ShowCurriculum.from_orm(curriculum) for curriculum in curriculums]


async def _delete_curriculum(semester_number: int, group_name: str, subject_code: str, db) -> ShowCurriculum:
    async with db as session:
        try:
            async with session.begin():
                curriculum_dal = CurriculumDAL(session)
                curriculum = await curriculum_dal.delete_curriculum(semester_number, group_name, subject_code)

                if not curriculum:
                    raise HTTPException(status_code=404, detail=f"План для предмета: {subject_code} в группе: {group_name} на семестр: {semester_number} не найден")

            return ShowCurriculum.from_orm(curriculum)

        except Exception as e:
            logger.warning(f"Удаление плана отменено (Ошибка: {e})")
            raise


async def _update_curriculum(body: UpdateCurriculum, db) -> ShowCurriculum:
    async with db as session:
        try:
            async with session.begin():
                # exclusion of None-fields from the transmitted data
                update_data = {
                    key: value for key, value in body.dict().items() 
                    if value is not None and key not in ["semester_number", "group_name", "subject_code"]
                }

                group_dal = GroupDAL(session)
                subject_dal = SubjectDAL(session)
                curriculum_dal = CurriculumDAL(session)

                if body.new_group_name != None and not await ensure_group_exists(group_dal, body.new_group_name):
                    raise HTTPException(
                        status_code=404,
                        detail=f"Группа с названием {body.new_group_name} не найдена"
                    )
                
                if body.new_subject_code != None and not await ensure_subject_exists(subject_dal, body.new_subject_code):
                    raise HTTPException(
                        status_code=404,
                        detail=f"Предмет с кодом {body.new_subject_code} не найден"
                    )

                if not await ensure_curriculum_unique(curriculum_dal, body.new_semester_number, body.group_name, body.subject_code):
                    raise HTTPException(
                        status_code=400,
                        detail=f"План для предмета: {body.subject_code} в группе: {body.group_name} на семестр: {body.new_semester_number} уже существует"
                    )

                # Rename field new_semester_number to semester_number
                if "new_semester_number" in update_data:
                    update_data["semester_number"] = update_data.pop("new_semester_number")
                # Rename field new_group_name to group_name
                if "new_group_name" in update_data:
                    update_data["group_name"] = update_data.pop("new_group_name")
                # Rename field new_subject_code to subject_code
                if "new_subject_code" in update_data:
                    update_data["subject_code"] = update_data.pop("new_subject_code")

                curriculum = await curriculum_dal.update_curriculum(
                    tg_semester_number = body.semester_number,
                    tg_group_name = body.group_name,
                    tg_subject_code = body.subject_code,
                    **update_data
                )

                # save changed data
                await session.commit()

                if not curriculum:
                    raise HTTPException(status_code=404, detail=f"План для предмета: {body.subject_code} в группе: {body.group_name} на семестр: {body.semester_number} не найден")

            return ShowCurriculum.from_orm(curriculum)

        except Exception as e:
            await session.rollback()
            logger.warning(f"Изменение данных о плане отменено (Ошибка: {e})")
            raise


@curriculum_router.post("/create", response_model=ShowCurriculum)
async def create_curriculum(body: CreateCurriculum, db: AsyncSession = Depends(get_db)):
    return await _create_new_curriculum(body, db)


@curriculum_router.get("/search/{group_name}/{subject_code}/{semester_number}", response_model=ShowCurriculum,
                    responses={404: {"description": "План не найден"}})
async def get_curriculum(semester_number: int, group_name: str, subject_code: str, db: AsyncSession = Depends(get_db)):
    return await _get_curriculum(semester_number, group_name, subject_code, db)


@curriculum_router.get("/search", response_model=list[ShowCurriculum], responses={404: {"description": "Планы не найдены"}})
async def get_all_curriculums(query_param: Annotated[QueryParams, Depends()], db: AsyncSession = Depends(get_db)):
    return await _get_all_curriculums(query_param.page, query_param.limit, db)


@curriculum_router.put("/delete/{group_name}/{subject_code}/{semester_number}", response_model=ShowCurriculum,
                    responses={404: {"description": "План не найден"}})
async def delete_curriculum(semester_number: int, group_name: str, subject_code: str, db: AsyncSession = Depends(get_db)):
    return await _delete_curriculum(semester_number, group_name, subject_code, db)


@curriculum_router.put("/update", response_model=ShowCurriculum, responses={404: {"description": "План не найден"}})
async def update_curriculum(body: UpdateCurriculum, db: AsyncSession = Depends(get_db)):
    return await _update_curriculum(body, db)


'''
===========================
CRUD operations for subject
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


@subject_router.get("/search/{subject_code}", response_model=ShowSubject,
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
                    response_model=list[ShowTeacherRequest], responses={404: {"description": "Запрос не найдены"}})
async def get_all_requests_by_teacher(teacher_id: int, query_param: Annotated[QueryParams, Depends()], db: AsyncSession = Depends(get_db)):
    return await _get_all_requests_by_teacher(teacher_id, query_param.page, query_param.limit, db)


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
