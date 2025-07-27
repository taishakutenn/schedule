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
from api.services_helpers import ensure_building_exists, ensure_cabinet_unique
from db.dals import TeacherDAL, BuildingDAL, CabinetDAL, SpecialityDAL
from db.session import get_db

from config.logging_config import configure_logging

# Сreate logger object
logger = configure_logging()

teacher_router = APIRouter()  # Create router for teachers
building_router = APIRouter()  # Create router for buildings
cabinet_router = APIRouter()  # Create route for cabinets
speciality_router = APIRouter() # Create router for speciality

'''
============================
CRUD operations for teachers
============================
'''


async def _create_new_teacher(body: CreateTeacher, db) -> ShowTeacher:
    async with db as session:
        async with session.begin():
            teacher_dal = TeacherDAL(session)
            teacher = await teacher_dal.create_teacher(
                name=body.name,
                surname=body.surname,
                phone_number=body.phone_number,
                email=str(body.email),
                fathername=body.fathername
            )
            return ShowTeacher.from_orm(teacher)


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


@teacher_router.post("/create", response_model=ShowTeacher)
async def create_teacher(body: CreateTeacher, db: AsyncSession = Depends(get_db)):
    return await _create_new_teacher(body, db)


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
                     responses={404: {"description": "Зданение не найдено"}})
async def get_building_by_number(building_number: int, db: AsyncSession = Depends(get_db)):
    return await _get_building_by_number(building_number, db)


@building_router.get("/search/by_address", response_model=ShowBuilding | None,
                     responses={404: {"description": "Зданение не найдено"}})
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
                     responses={404: {"description": "Зданение не найдено"}})
async def delete_building(building_number: int, db: AsyncSession = Depends(get_db)):
    return await _delete_building(building_number, db)


@building_router.put("/update", response_model=ShowBuilding, responses={404: {"description": "Зданение не найдено"}})
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
                    raise HTTPException(status_code=404, detail="Кабинет не был обновлёен")

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
                    value is not None and key not in ["speciality_code"]
                }

                # Create dal
                speciality_dal = SpecialityDAL(session)

                # Change data
                updated_speciality = await speciality_dal.update_speciality(body.speciality_code, **update_data)

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
async def get_speciality_by_code(speciality_code: str,
                                             db: AsyncSession = Depends(get_db)):
    return await _get_speciality(speciality_code, db)


@speciality_router.put("/delete/{speciality_code}", response_model=ShowSpeciality,
                    responses={404: {"description": "Не удаётся удалить специальность"}})
async def delete_speciality(speciality_code: str, db: AsyncSession = Depends(get_db)):
    return await _delete_speciality(speciality_code, db)


@speciality_router.put("/update", response_model=ShowSpeciality,
                    responses={404: {"description": "Специальность не найдена или нет возможности изменить её параметры"}})
async def update_speciality(body: UpdateSpeciality, db: AsyncSession = Depends(get_db)):
    return await _update_speciality(body, db)