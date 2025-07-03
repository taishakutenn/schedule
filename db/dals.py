"""
File for encapsulating business logic,
here classes are written for implementing crud operations for each table.
There is no need to do checks in the data,
because it is assumed that the data submitted here is already validated.
"""

from typing import Union, Tuple, Optional

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from models import Teacher, Group, Cabinet, Building
from config.logging_config import configure_logging

# Создаём объект логгера
logger = configure_logging()


'''
================
DAL for Teacher
================
'''

class TeacherDAL:
    """Data Access Layer for operating teacher info"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_teacher(
            self, name: str, surname: str, phone_number: str, email: str = None, fathername: str = None
    ) -> Teacher:
        new_teacher = Teacher(
            name=name,
            surname=surname,
            phone_number=phone_number,
            email=email,
            fathername=fathername
        )

        # Add teacher in session
        self.db_session.add(new_teacher)

        # Add changes to the database, but do not commit them strictly
        await self.db_session.flush()
        logger.info("Новый учитель успешно добавлен в бд")
        return new_teacher

    async def delete_teacher(self, id) -> bool:
        query = delete(Teacher).where(Teacher.id == id).returning(Teacher.id)
        res = await self.db_session.execute(query)
        deleted_teacher = res.fetchone()
        if not deleted_teacher:  # if there aren't deleted records
            logger.warning(f"Не было найдено ни одного учителя с таким id: {id}")
            return False
        logger.info(f"Учитель с id {id} был успешно удалён из бд")
        return True

    async def get_teacher_by_id(self, id) -> Union[int, None]:
        query = select(Teacher).where(Teacher.id == id)
        res = await self.db_session.execute(query)  # Make an asynchronous query to the database to search for a teacher
        teacher_row = res.scalar()  # return object Teacher or None
        if teacher_row is not None:
            logger.info(f"Учитель с id: {id} был успешно найден")
            return teacher_row.id
        logger.warning(f"Не было найдено ни одного учителя с таким id: {id}")
        return None

    async def get_teacher_by_name_surname(self, name: str, surname: str) -> Union[int, None]:
        query = select(Teacher).where(
            (Teacher.name == name) & (Teacher.surname == surname)
        )
        res = await self.db_session.execute(query)
        teacher_row = res.scalar()  # return object Teacher or None
        if teacher_row is not None:
            logger.info(f"Учитель с ФИ: {name} - {surname} был успешно найден")
            return teacher_row.id
        logger.warning(f"Не было найдено ни одного учителя с таким ФИ: {name} - {surname}")
        return None

    async def update(self, id, **kwargs) -> Optional[int]:
        # kwargs - it is the fields which we want to update
        query = (
            update(Teacher).
            where(Teacher.id == id).
            values(**kwargs).
            returning(Teacher.id)
        )
        res = await self.db_session.execute(query)
        updated_teacher = res.scalar()  # return Teacher id or None (because returning == Teacher.id)
        if updated_teacher is not None:
            logger.info(f"У учителя с id: {id} были успешно обновлены поля: {" - ".join(kwargs.keys())}")
            return updated_teacher.id
        logger.warning(f"Не было найдено ни одного учителя с таким id: {id}")
        return None


'''
================
DAL for Building
================
'''

class BuildingDAL:
    """Data Access Layer for operating building info"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_building(
            self, building_number: int, city: str, building_address: int, cabinets: int
    ) -> Building:
        new_building = Building(
            building_number=building_number,
            city=city,
            building_address=building_address,
            cabinets=cabinets,
        )

        # Add building in session
        self.db_session.add(new_building)

        # Add changes to the database, but do not commit them strictly
        await self.db_session.flush()
        logger.info("Новое здание успешно добавлено в бд")
        return new_building
    
    async def delete_group(self, building_number: int) -> bool:
        query = delete(Building).where(Building.building_number == building_number).returning(Building.building_number)
        res = await self.db_session.execute(query)
        deleted_building = res.fetchone()
        if not deleted_building:  # if there aren't deleted records
            logger.warning(f"Не было найдено ни одного здания с таким номером: {building_number}")
            return False
        logger.info(f"Здание с номером: {building_number} было успешно удалено из бд")
        return True
    
    async def get_building_by_number(self, building_number: int) -> Union[int, None]:
        query = select(Building).where(Building.building_number == building_number)
        res = await self.db_session.execute(query)  # Make an asynchronous query to the database to search for a group
        building_row = res.scalar()  # return object Group or None
        if building_row is not None:
            logger.info(f"Здание с номером: {building_number} было успешно найдено")
            return building_row.building_number
        logger.warning(f"Не было найдено ни одного здания с номером: {building_number}")
        return None
    
    async def get_building_by_addres(self, building_addres: str) -> Union[str, None]:
        query = select(Building).where(Building.building_addres == building_addres)
        res = await self.db_session.execute(query)  # Make an asynchronous query to the database to search for a group
        building_row = res.scalar()  # return object Group or None
        if building_row is not None:
            logger.info(f"Здание по адресу: {building_addres} было успешно найдено")
            return building_row.building_number
        logger.warning(f"Не было найдено ни одного здания по адресу: {building_addres}")
        return None
    
    async def update(self, building_number: int, **kwargs) -> Optional[int]:
        query = (
            update(Building).
            where(Building.building_number == building_number).
            values(**kwargs).
            returning(Building.building_number)
        )
        res = await self.db_session.execute(query)
        update_building = res.scalar()  # return Group name or None
        if update_building is not None:
            logger.info(f"Для здания с номером: {building_number}. Были успешно обновлены поля: {" - ".join(kwargs.keys())}")
            return update_building.group_name
        logger.warning(f"Не было найдено ни однго здания под номером: {building_number}")
        return None


'''
==============
DAL for Group
==============
'''

class GroupDAL:
    """Data Access Layer for operating group info"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_group(
            self, group_name: str, speciality_code: str, quantity_students: int = None, group_advisor_id: int = None, 
    ) -> Group:
        new_group = Group(
            group_name=group_name,
            speciality_code=speciality_code,
            quantity_students=quantity_students,
            group_advisor_id=group_advisor_id,
        )

        # Add group in session
        self.db_session.add(new_group)

        # Add changes to the database, but do not commit them strictly
        await self.db_session.flush()
        logger.info("Новая группа успешно добавлена в бд")
        return new_group
    
    async def delete_group(self, group_name: str) -> bool:
        query = delete(Group).where(Group.group_name == group_name).returning(Group.group_name)
        res = await self.db_session.execute(query)
        deleted_group = res.fetchone()
        if not deleted_group:  # if there aren't deleted records
            logger.warning(f"Не было найдено ни одной группы с таким названием: {group_name}")
            return False
        logger.info(f"Группа с названием: '{group_name}' была успешно удалена из бд")
        return True
    
    async def get_group(self, group_name: str) -> Union[str, None]:
        query = select(Group).where(Group.group_name == group_name)
        res = await self.db_session.execute(query)  # Make an asynchronous query to the database to search for a group
        group_row = res.scalar()  # return object Group or None
        if group_row is not None:
            logger.info(f"Группа с названием: '{group_name}' была успешно найдена")
            return group_row.id
        logger.warning(f"Не было найдено ни одной группы с названием: '{group_name}'")
        return None
    
    async def update(self, group_name: str, **kwargs) -> Optional[str]:
        query = (
            update(Group).
            where(Group.group_name == group_name).
            values(**kwargs).
            returning(Group.group_name)
        )
        res = await self.db_session.execute(query)
        update_group = res.scalar()  # return Group name or None
        if update_group is not None:
            logger.info(f"Для группы с названием: '{group_name}'. Были успешно обновлены поля: {" - ".join(kwargs.keys())}")
            return update_group.group_name
        logger.warning(f"Не было найдено ни одной группы с таким названием: '{group_name}'")
        return None
    

'''
================
DAL for Cabinet
================
'''

class CabinetDAL:
    """Data Access Layer for operating group info"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_cabinet(
            self, cabinet_number: int, capacity: int = None, cabinet_state: str = None, building_number: int = None, 
    ) -> Cabinet:
        new_cabinet = Cabinet(
            cabinet_number=cabinet_number,
            capacity=capacity,
            cabinet_state=cabinet_state,
            building_number=building_number,
        )

        # Add cabinet in session
        self.db_session.add(new_cabinet)

        # Add changes to the database, but do not commit them strictly
        await self.db_session.flush()
        logger.info("Новый кабинет успешно добавлен в бд")
        return new_cabinet
    
    async def delete_cabinet(self, cabinet_number: int) -> bool:
        query = delete(Cabinet).where(Cabinet.cabinet_number == cabinet_number).returning(Cabinet.cabinet_number)
        res = await self.db_session.execute(query)
        deleted_cabinet = res.fetchone()
        if not deleted_cabinet:  # if there aren't deleted records
            logger.warning(f"Не было найдено ни одного кабинета с таким номером: {cabinet_number}")
            return False
        logger.info(f"Кабинет с номером: {cabinet_number} был успешно удален из бд")
        return True
    
    async def get_cabinet(self, cabinet_number: int) -> Union[int, None]:
        query = select(Cabinet).where(Cabinet.cabinet_number == cabinet_number)
        res = await self.db_session.execute(query)  # Make an asynchronous query to the database to search for a cabinet
        cabinet_row = res.scalar()  # return object Cabinet or None
        if cabinet_row is not None:
            logger.info(f"Кабинет с номером: {cabinet_number} был успешно найден")
            return cabinet_row.id
        logger.warning(f"Не было найдено ни одного кабинета с номером: {cabinet_number}")
        return None
    
    async def update(self, cabinet_number: int, **kwargs) -> Optional[int]:
        query = (
            update(Cabinet).
            where(Cabinet.cabinet_number == cabinet_number).
            values(**kwargs).
            returning(Cabinet.cabinet_number)
        )
        res = await self.db_session.execute(query)
        update_cabinet = res.scalar()  # return Group name or None
        if update_cabinet is not None:
            logger.info(f"Для кабнета с номером: {cabinet_number}. Были успешно обновлены поля: {" - ".join(kwargs.keys())}")
            return update_cabinet.group_name
        logger.warning(f"Не было найдено ни одного кабинета с таким номером: {cabinet_number}")
        return None