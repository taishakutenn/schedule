"""
file for handlers
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from api.models import ShowTeacher, CreateTeacher, QueryParams, UpdateTeacher, ShowCabinet, CreateCabinet, UpdateCabinet
from api.models import ShowBuilding, CreateBuilding, UpdateBuilding
from db.dals import TeacherDAL, BuildingDAL, CabinetDAL
from db.session import get_db

from config.logging_config import configure_logging

# Сreate logger object
logger = configure_logging()

teacher_router = APIRouter()  # Create router for teachers
building_router = APIRouter()  # Create router for buildings
cabinet_router = APIRouter()  # Create route for cabinets

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


async def _get_teacher_by_id(id, db) -> ShowTeacher | None:
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
            return None


async def _get_teacher_by_name_and_surname(name, surname, db) -> ShowTeacher | None:
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

            return None


async def _get_all_teachers(page: int, limit: int, db) -> list[ShowTeacher] | None:
    async with db as session:
        async with session.begin():
            teacher_dal = TeacherDAL(session)
            teachers = await teacher_dal.get_all_teachers(page, limit)
            if teachers:
                return teachers

            return None


async def _delete_teacher(teacher_id: int, db) -> ShowTeacher | None:
    async with db as session:
        try:
            await session.begin()
            teacher_dal = TeacherDAL(session)
            teacher = await teacher_dal.delete_teacher(teacher_id)

            # save changed data
            await session.commit()

            if teacher:
                return teacher

            return None

        except Exception as e:
            await session.rollback()
            logger.warning(f"Изменение данных об учителе отменено (Ошибка: {e})")
            raise e


async def _update_teacher(body: UpdateTeacher, db) -> ShowTeacher | None:
    async with db as session:
        try:
            await session.begin()
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

            return None

        except Exception as e:
            await session.rollback()
            logger.warning(f"Изменение данных об учителе отменено (Ошибка: {e})")
            raise e


@teacher_router.post("/create", response_model=ShowTeacher)
async def create_teacher(body: CreateTeacher, db: AsyncSession = Depends(get_db)):
    return await _create_new_teacher(body, db)


@teacher_router.get("/search/by_id/{teacher_id}", response_model=ShowTeacher,
                    responses={404: {"description": "Учитель не найден"}})
async def get_teacher_by_id(teacher_id: int, db: AsyncSession = Depends(get_db)):
    teacher = await _get_teacher_by_id(teacher_id, db)
    if teacher is None:
        raise HTTPException(status_code=404, detail=f"Учитель с id: {teacher_id} не найден")
    return teacher


@teacher_router.get("/search/by_humanity", response_model=ShowTeacher,
                    responses={404: {"description": "Учитель не найден"}})
async def get_teacher_by_name_and_surname(name: str, surname: str, db: AsyncSession = Depends(get_db)):
    teacher = await _get_teacher_by_name_and_surname(name, surname, db)
    if teacher is None:
        raise HTTPException(status_code=404, detail=f"Учитель {name, surname} не найден")
    return teacher


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
    teachers = await _get_all_teachers(query_param.page, query_param.limit, db)
    if teachers is None:
        raise HTTPException(status_code=404, detail=f"Учителя не найдены")
    return teachers


@teacher_router.put("/delete/{teacher_id}", response_model=ShowTeacher,
                    responses={404: {"description": "Учитель не найден"}})
async def delete_teacher(teacher_id: int, db: AsyncSession = Depends(get_db)):
    teacher = await _delete_teacher(teacher_id, db)
    if teacher is None:
        raise HTTPException(status_code=404, detail=f"Учитель с id: {teacher_id} не найдены")
    return teacher


@teacher_router.put("/update", response_model=ShowTeacher, responses={404: {"description": "Учитель не найден"}})
async def update_teacher(body: UpdateTeacher, db: AsyncSession = Depends(get_db)):
    teacher = await _update_teacher(body, db)
    if teacher is None:
        raise HTTPException(status_code=404, detail=f"Учитель с id: {body.teacher_id} не найдены")
    return teacher


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


async def _get_building_by_number(number, db) -> ShowBuilding | None:
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

            return None


async def _get_building_by_address(address, db) -> ShowBuilding | None:
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

            return None


async def _get_all_buildings(page: int, limit: int, db) -> list[ShowBuilding] | None:
    async with db as session:
        async with session.begin():
            building_dal = BuildingDAL(session)
            building = await building_dal.get_all_buildings(page, limit)
            if building:
                return building

            return None


async def _delete_building(building_number: int, db) -> bool | None:
    async with db as session:
        try:
            await session.begin()

            building_dal = BuildingDAL(session)
            building = await building_dal.delete_building(building_number)

            # save changed data
            await session.commit()

            if building:
                return building

            return None

        except Exception as e:
            await session.rollback()
            logger.warning(f"Удаление данных о здании отменено (Ошибка: {e})")
            raise e


async def _update_building(body: UpdateBuilding, db) -> ShowBuilding | None:
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
            return None

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
    building = await _get_building_by_number(building_number, db)
    if building is None:
        raise HTTPException(status_code=404, detail=f"Здание с номером: {building_number} не найдено")
    return building


@building_router.get("/search/by_address/{address}", response_model=ShowBuilding,
                     responses={404: {"description": "Зданение не найдено"}})
async def get_building_by_address(address: str, db: AsyncSession = Depends(get_db)):
    building = await _get_building_by_address(address, db)
    if building is None:
        raise HTTPException(status_code=404, detail=f"Здание по адресу: {address} не найдено")
    return building


@building_router.get("/search", response_model=list[ShowBuilding],
                     responses={404: {"description": "Зданения не найдены"}})
async def get_all_buildings(query_param: Annotated[QueryParams, Depends()], db: AsyncSession = Depends(get_db)):
    """
    query_param set via Annotated so that fastapi understands
    that the pydantic model QueryParam refers to the query parameters,
    we specify this as the second argument for Annotated.
    Wherever there will be pagination and the number of elements on the page,
    it is better to use this pydantic model, so as not to manually enter these parameters each time.
    Link to documentation: https://fastapi.tiangolo.com/ru/tutorial/query-param-models/
    """
    building = await _get_all_buildings(query_param.page, query_param.limit, db)
    if building is None:
        raise HTTPException(status_code=404, detail=f"Зданий не найдено")
    return building


@building_router.put("/delete/{building_number}", response_model=bool,
                     responses={404: {"description": "Зданение не найдено"}})
async def delete_building(building_number: int, db: AsyncSession = Depends(get_db)):
    building = await _delete_building(building_number, db)
    if building is None:
        raise HTTPException(status_code=404, detail=f"Здание с номером: {building_number} не найдено")
    return building


@building_router.put("/update", response_model=ShowBuilding, responses={404: {"description": "Зданение не найдено"}})
async def update_building(body: UpdateBuilding, db: AsyncSession = Depends(get_db)):
    building = await _update_building(body, db)
    if building is None:
        raise HTTPException(status_code=404, detail=f"Здание с номером: {body.building_number} не найдено")
    return building


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
            building = await building_dal.get_building_by_number(body.building_number)
            if not building:
                logger.error(f"Здание с номером {body.building_number} не найдено")
                raise HTTPException(
                    status_code=404,
                    detail=f"Здание с номером {body.building_number} не найдено"
                )

            # Check that the cabinet is unique
            cabinet = await cabinet_dal.get_cabinet_by_number_and_building(
                body.cabinet_number,
                body.building_number
            )
            if cabinet:
                logger.error(
                    f"В здание с номером {body.building_number} уже есть кабинет с номером {body.cabinet_number}")
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

            return ShowCabinet(
                cabinet_number=new_cabinet.cabinet_number,
                building_number=new_cabinet.building_number,
                capacity=new_cabinet.capacity,
                cabinet_state=new_cabinet.cabinet_state
            )


async def _get_all_cabinets(page: int, limit: int, db) -> list[ShowCabinet]:
    async with db as session:
        async with session.begin():
            cabinet_dal = CabinetDAL(session)
            cabinets = cabinet_dal.get_all_cabinets(page, limit)

            if not cabinets:
                raise HTTPException(status_code=404, detail=f"Нет ещё ни одного кабинета")

            return await cabinets


async def _get_cabinets_by_building(building_number: int, page: int, limit: int, db) -> list[ShowCabinet]:
    async with db as session:
        async with session.begin():
            cabinet_dal = CabinetDAL(session)
            cabinets = cabinet_dal.get_cabinets_by_building(building_number, page, limit)

            if not cabinets:
                raise HTTPException(status_code=404,
                                    detail=f"В здании с номером {building_number} не было найдено кабинетов")

            return await cabinets


async def _get_cabinet_by_building_and_number(building_number: int, cabinet_number: int, db) -> ShowCabinet:
    async with db as session:
        async with session.begin():
            cabinet_dal = CabinetDAL(session)
            cabinet = await cabinet_dal.get_cabinet_by_number_and_building(building_number, cabinet_number)

            if not cabinet:
                raise HTTPException(status_code=404,
                                    detail=f"Кабинет с номером: {cabinet_number} в здании с номером: {building_number} - не найден")

            return ShowCabinet(
                cabinet_number=cabinet.cabinet_number,
                capacity=cabinet.capacity,
                cabinet_state=cabinet.cabinet_state,
                building_number=cabinet.building_number
            )


async def _delete_cabinet(building_number: int, cabinet_number: int, db) -> ShowCabinet:
    async with db as session:
        async with session.begin():
            cabinet_dal = CabinetDAL(session)
            cabinet = await cabinet_dal.delete_cabinet(building_number, cabinet_number)

            if not cabinet:
                raise HTTPException(status_code=404,
                                    detail=f"Кабинет с номером: {cabinet_number} в здании {building_number} не может быть удалён, т.к. не найден")

            return ShowCabinet(
                cabinet_number=cabinet.cabinet_number,
                capacity=cabinet.capacity,
                cabinet_state=cabinet.cabinet_state,
                building_number=cabinet.building_number
            )


async def _update_cabinet(body: UpdateCabinet, db) -> ShowCabinet:
    async with db as session:
        try:
            async with session.begin():
                # exclusion of None-fields from the transmitted data
                update_data = {
                    key: value for key, value in body.dict().items() if
                    value is not None and key not in ["building_number", "cabinet_number"]
                }

                # Rename the fields new_cabinet_number and new_building_number to cabinet_number and building_number
                if "new_building_number" in update_data:
                    update_data["building_number"] = update_data.pop("new_building_number")

                if "new_cabinet_number" in update_data:
                    update_data["cabinet_number"] = update_data.pop("new_cabinet_number")

                # Change data
                cabinet_dal = CabinetDAL(session)
                updated_cabinet = await cabinet_dal.update(body.building_number, body.cabinet_number, **update_data)

                if not updated_cabinet:
                    raise HTTPException(status_code=404, detail="Кабинет не был обновлёен")

                return ShowCabinet(
                    cabinet_number=updated_cabinet.cabinet_number,
                    capacity=updated_cabinet.capacity,
                    cabinet_state=updated_cabinet.cabinet_state,
                    building_number=updated_cabinet.building_number,
                )

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


@cabinet_router.get("/search/by_building_and_number", response_model=list[ShowCabinet])
async def get_cabinet_by_building_and_number(building_number: int,
                                             cabinet_number: int,
                                             db: AsyncSession = Depends(get_db)):
    return await _get_cabinet_by_building_and_number(building_number, cabinet_number, db)


@cabinet_router.put("/delete/{building_number}/{cabinet_number}", response_model=ShowCabinet)
async def delete_cabinet(building_number: int, cabinet_number: int, db: AsyncSession = Depends(get_db)):
    return await _delete_cabinet(building_number, cabinet_number, db)


@cabinet_router.put("/update", response_model=ShowCabinet)
async def update_cabinet(body: UpdateCabinet, db: AsyncSession = Depends(get_db)):
    return await _update_cabinet(body, db)
