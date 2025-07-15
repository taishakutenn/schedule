"""
file for handlers
"""

from fastapi import APIRouter, Depends, Query
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from api.models import ShowTeacher, CreateTeacher, QueryParams, UpdateTeacher
from api.models import ShowBuilding, CreateBuilding, UpdateBuilding
from db.dals import TeacherDAL, BuildingDAL
from db.session import get_db

from config.logging_config import configure_logging


# Сreate logger object
logger = configure_logging()

teacher_router = APIRouter()  # Create router for teachers
building_router = APIRouter()  # Create router for buildings


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
            return ShowTeacher(
                name=teacher.name,
                surname=teacher.surname,
                phone_number=teacher.phone_number,
                email=teacher.email,
                fathername=teacher.fathername
            )


async def _get_teacher_by_id(id, db) -> ShowTeacher | list:
    async with db as session:
        async with session.begin():
            teacher_dal = TeacherDAL(session)
            teacher = await teacher_dal.get_teacher_by_id(id)

            # if teacher exist
            if teacher is not None:
                return ShowTeacher(
                    name=teacher.name,
                    surname=teacher.surname,
                    phone_number=teacher.phone_number,
                    email=teacher.email,
                    fathername=teacher.fathername
                )
            return []


async def _get_teacher_by_name_and_surname(name, surname, db) -> ShowTeacher | list:
    async with db as session:
        async with session.begin():
            teacher_dal = TeacherDAL(session)
            teacher = await teacher_dal.get_teacher_by_name_surname(name, surname)

            # if teacher exist
            if teacher is not None:
                return ShowTeacher(
                    name=teacher.name,
                    surname=teacher.surname,
                    phone_number=teacher.phone_number,
                    email=teacher.email,
                    fathername=teacher.fathername
                )

            return []


async def _get_all_teachers(page: int, limit: int, db) -> list[ShowTeacher]:
    async with db as session:
        async with session.begin():
            teacher_dal = TeacherDAL(session)
            teachers = await teacher_dal.get_all_teachers(page, limit)
            if teachers:
                return teachers
            return []


async def _delete_teacher(teacher_id: int, db) -> ShowTeacher | list:
    async with db as session:
        async with await session.begin():
            teacher_dal = TeacherDAL(session)
            teacher = await teacher_dal.delete_teacher(teacher_id)
            if teacher:
                return teacher
            return []


async def _update_teacher(body: UpdateTeacher, db) -> ShowTeacher | list:
    async with db as session:
        try:
            await session.begin()
            # exclusion of None-fields from the transmitted data
            update_data = {
                key: value for key, value in body.dict().items() if value is not None  and key != "teacher_id"
            }

            # change data
            teacher_dal = TeacherDAL(session)
            teacher = await teacher_dal.update_teacher( 
                id=body.teacher_id,
                **update_data
            )
            
            # save changed data
            await session.commit()

            if teacher is not None:
                return ShowTeacher(
                    name=teacher.name,
                    surname=teacher.surname,
                    phone_number=teacher.phone_number,
                    email=teacher.email,
                    fathername=teacher.fathername
                )
            return []

        except Exception as e:
            await session.rollback()
            logger.warning(f"Изменение данных об учителе отменено (Ошибка: {e})")
            raise e


@teacher_router.post("/create", response_model=ShowTeacher)
async def create_teacher(body: CreateTeacher, db: AsyncSession = Depends(get_db)):
    return await _create_new_teacher(body, db)


@teacher_router.get("/search/by_id/{teacher_id}", response_model=ShowTeacher)
async def get_teacher_by_id(teacher_id: int, db: AsyncSession = Depends(get_db)):
    return await _get_teacher_by_id(teacher_id, db)


@teacher_router.get("/search/by_humanity", response_model=ShowTeacher)
async def get_teacher_by_name_and_surname(name: str, surname: str, db: AsyncSession = Depends(get_db)):
    return await _get_teacher_by_name_and_surname(name, surname, db)


@teacher_router.get("/search", response_model=list[ShowTeacher])
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


@teacher_router.put("/delete/{teacher_id}", response_model=ShowTeacher)
async def delete_teacher(teacher_id: int, db: AsyncSession = Depends(get_db)):
    return await _delete_teacher(teacher_id, db)


@teacher_router.put("/update/{teacher_id}", response_model=ShowTeacher)
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
            return ShowBuilding(
                building_number=building.building_number,
                city=building.city,
                building_address=building.building_address
            )


async def _get_building_by_number(number, db) -> ShowBuilding | list:
    async with db as session:
        async with session.begin():
            building_dal = BuildingDAL(session)
            building = await building_dal.get_building_by_number(number)

            # if building exist
            if building is not None:
                return ShowBuilding(
                    building_number=building.building_number,
                    city=building.city,
                    building_address=building.building_address
                )
            return []


async def _get_building_by_address(address, db) -> ShowBuilding | list:
    async with db as session:
        async with session.begin():
            building_dal = BuildingDAL(session)
            building = await building_dal.get_building_by_address(address)

            # if building exist
            if building is not None:
                return ShowBuilding(
                    building_number=building.building_number,
                    city=building.city,
                    building_address=building.building_address
                )
            return 
        


async def _get_all_buildings(page: int, limit: int, db) -> list[ShowBuilding]:
    async with db as session:
        async with session.begin():
            building_dal = BuildingDAL(session)
            building = await building_dal.get_all_buildings(page, limit)
            if building:
                return building
            return []


async def _delete_building(building_number: int, db) -> ShowBuilding | list:
    async with db as session:
        try:
            await session.begin()

            building_dal = BuildingDAL(session)
            building = await building_dal.delete_building(building_number)
            
            # save changed data
            await session.commit()

            return building
        except Exception as e:
            await session.rollback()
            logger.warning(f"Удаление данных о здании отменено (Ошибка: {e})")
            raise e


async def _update_building(body: UpdateBuilding, db) -> ShowBuilding | list:
    async with db as session:
        try:
            await session.begin()
            # exclusion of None-fields from the transmitted data
            update_data = {
                key: value for key, value in body.dict().items() if value is not None and key != "building_number"
            }

            # change data
            building_dal = BuildingDAL(session)
            building = await building_dal.update_building( 
                building_number=body.building_number,
                **update_data
            )
            
            # save changed data
            await session.commit()

            if building is not None:
                return ShowBuilding(
                        building_number=building.building_number,
                        city=building.city,
                        building_address=building.building_address
                    )
            return []
        
        except Exception as e:
            await session.rollback()
            logger.warning(f"Изменение данных о здании отменено (Ошибка: {e})")
            raise e


@building_router.post("/create", response_model=ShowBuilding)
async def create_building(body: CreateBuilding, db: AsyncSession = Depends(get_db)):
    return await _create_new_building(body, db)


@building_router.get("/search/by_number/{building_number}", response_model=ShowBuilding)
async def get_building_by_number(building_number: int, db: AsyncSession = Depends(get_db)):
    return await _get_building_by_number(building_number, db)


@building_router.get("/search/by_address/{address}", response_model=ShowBuilding)
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


@building_router.put("/delete/{building_number}", response_model=bool)
async def delete_building(building_number: int, db: AsyncSession = Depends(get_db)):
    return await _delete_building(building_number, db)


@building_router.put("/update/{building_number}", response_model=ShowBuilding)
async def update_building(body: UpdateBuilding, db: AsyncSession = Depends(get_db)):
    return await _update_building(body, db)