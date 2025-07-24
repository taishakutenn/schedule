from typing import Optional
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import ShowTeacher, ShowBuilding, ShowCabinet, ShowSpeciality, ShowGroup, ShowCurriculum
from db.models import Teacher, Group, Cabinet, Building, Speciality, Curriculum
from config.decorators import log_exceptions

'''
================
DAL for Teacher
================
'''


class TeacherDAL:
    """Data Access Layer for operating teacher info"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
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
        self.db_session.add(new_teacher)
        await self.db_session.flush()
        return new_teacher  # Return real orm object

    @log_exceptions
    async def delete_teacher(self, id: int) -> Teacher | None:
        query_select = select(Teacher).where(Teacher.id == id)
        res = await self.db_session.execute(query_select)
        teacher = res.scalar_one_or_none()

        await self.db_session.execute(delete(Teacher).where(Teacher.id == id))
        return teacher  # Return orm object which was in the database

    @log_exceptions
    async def get_all_teachers(self, page: int, limit: int) -> list[Teacher]:
        query = select(Teacher).order_by(Teacher.surname.asc())
        if page > 0:
            query = query.offset((page - 1) * limit).limit(limit)

        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    @log_exceptions
    async def get_teacher_by_id(self, id: int) -> Teacher | None:
        result = await self.db_session.execute(select(Teacher).where(Teacher.id == id))
        return result.scalar_one_or_none()  # Don't build new orm object

    @log_exceptions
    async def get_teacher_by_name_surname(self, name: str, surname: str) -> Teacher | None:
        result = await self.db_session.execute(
            select(Teacher).where((Teacher.name == name) & (Teacher.surname == surname))
        )
        return result.scalar_one_or_none()

    @log_exceptions
    async def update_teacher(self, id: int, **kwargs) -> Teacher | None:
        result = await self.db_session.execute(
            update(Teacher).where(Teacher.id == id).values(**kwargs).returning(Teacher)
        )
        return result.scalar_one_or_none()


'''
================
DAL for Building
================
'''


class BuildingDAL:
    """Data Access Layer for operating building info"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_building(
            self, building_number: int, city: str, building_address: str
    ) -> Building:
        new_building = Building(
            building_number=building_number,
            city=city,
            building_address=building_address
        )
        self.db_session.add(new_building)
        await self.db_session.flush()
        return new_building

    @log_exceptions
    async def delete_building(self, building_number: int) -> Building | None:
        query = delete(Building).where(Building.building_number == building_number).returning(Building)
        res = await self.db_session.execute(query)
        deleted_building = res.scalar_one_or_none()
        return deleted_building

    @log_exceptions
    async def get_all_buildings(self, page: int, limit: int) -> list[Building]:
        if page == 0:
            query = select(Building).order_by(Building.building_number.asc())
        else:
            query = select(Building).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    @log_exceptions
    async def get_building_by_number(self, building_number: int) -> Building | None:
        query = select(Building).where(Building.building_number == building_number)
        res = await self.db_session.execute(query)
        return res.scalar_one_or_none()

    @log_exceptions
    async def get_building_by_address(self, building_address: str) -> Building | None:
        query = select(Building).where(Building.building_address == building_address)
        res = await self.db_session.execute(query)
        building_row = res.scalar_one_or_none()
        return building_row

    @log_exceptions
    async def update_building(self, target_number, **kwargs) -> Building | None:
        query = update(Building).where(Building.building_number == target_number).values(**kwargs).returning(Building)
        res = await self.db_session.execute(query)
        return res.scalar_one_or_none()


'''
===============
DAL for Cabinet
===============
'''


class CabinetDAL:
    """Data Access Layer for operating cabinet info"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_cabinet(
            self, cabinet_number: int, building_number: int, capacity: int = None, cabinet_state: str = None
    ) -> Cabinet:
        new_cabinet = Cabinet(
            cabinet_number=cabinet_number,
            capacity=capacity,
            cabinet_state=cabinet_state,
            building_number=building_number
        )
        self.db_session.add(new_cabinet)
        await self.db_session.flush()
        return new_cabinet

    @log_exceptions
    async def delete_cabinet(self, building_number: int, cabinet_number: int) -> Cabinet | None:
        query = delete(Cabinet).where(
            (Cabinet.cabinet_number == cabinet_number) & (Cabinet.building_number == building_number)
        ).returning(Cabinet)
        res = await self.db_session.execute(query)
        return res.fetchone() or None

    @log_exceptions
    async def get_cabinet_by_number_and_building(self, building_number: int, cabinet_number: int) -> Cabinet | None:
        query = select(Cabinet).where(
            (Cabinet.cabinet_number == cabinet_number) &
            (Cabinet.building_number == building_number)
        )
        res = await self.db_session.execute(query)
        return res.scalar_one_or_none()

    @log_exceptions
    async def get_all_cabinets(self, page: int, limit: int) -> list[Cabinet]:
        if page == 0:
            query = select(Cabinet).order_by(Cabinet.cabinet_number.asc())
        else:
            query = select(Cabinet).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        cabinets = list(result.scalars().all())
        return cabinets

    @log_exceptions
    async def get_cabinets_by_building(self, building_number: int, page: int, limit: int) -> list[Cabinet]:
        if page == 0:
            query = select(Cabinet).where(Cabinet.building_number == building_number).order_by(
                Cabinet.cabinet_number.asc())
        else:
            query = select(Cabinet).where(Cabinet.building_number == building_number).offset((page - 1) * limit).limit(
                limit)
        result = await self.db_session.execute(query)
        cabinets = list(result.scalars().all())
        return cabinets

    @log_exceptions
    async def update_cabinet(self, search_building_number: int, search_cabinet_number: int, **kwargs) -> Cabinet | None:
        """
        We use that names for the variables we are searching for because
        in **kwargs there are already variables with names: building_number and cabinet_number
        """
        query = update(Cabinet).where(
            (Cabinet.cabinet_number == search_cabinet_number) & (Cabinet.building_number == search_building_number)
        ).values(**kwargs).returning(Cabinet)
        res = await self.db_session.execute(query)
        return res.scalar()


'''
==================
DAL for Speciality
==================
'''


class SpecialityDAL:
    """Data Access Layer for operating speciality info"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_speciality(self, speciality_code: str) -> Speciality:
        new_speciality = Speciality(speciality_code)
        self.db_session.add(new_speciality)
        await self.db_session.flush()
        return new_speciality

    @log_exceptions
    async def delete_speciality(self, speciality_code: str) -> Speciality | None:
        query = delete(Speciality).where(Speciality.speciality_code == speciality_code).returning(Speciality)
        res = await self.db_session.execute(query)
        return res.fetchone() or None

    @log_exceptions
    async def get_all_speciality(self, page: int, limit: int) -> list[Speciality] | None:
        if page == 0:
            query = select(Speciality).order_by(Speciality.speciality_code.asc())
        else:
            query = select(Speciality).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        specialities = list(result.scalar().all())
        return specialities

    @log_exceptions
    async def get_speciality_by_code(self, speciality_code) -> Speciality | None:
        query = select(Speciality).where(Speciality.speciality_code == speciality_code)
        res = await self.db_session.execute(query)
        speciality = res.scalar()
        if not speciality:
            return None
        
        return speciality

    @log_exceptions
    async def update_speciality(self, speciality_code, new_speciality_code) -> Speciality | None:
        query = (
            update(Speciality)
            .where(Speciality.speciality_code == speciality_code)
            .values(new_speciality_code)
            .returning(Speciality)
        )
        res = await self.db_session.execute(query)
        return res.scalar()


'''
==============
DAL for Group
==============
'''


class GroupDAL:
    """Data Access Layer for operating group info"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_group(
            self, group_name: str, speciality_code: str, quantity_students: int = None, group_advisor_id: int = None,
    ) -> Group:
        new_group = Group(
            group_name=group_name,
            speciality_code=speciality_code,
            quantity_students=quantity_students,
            group_advisor_id=group_advisor_id,
        )
        self.db_session.add(new_group)
        await self.db_session.flush()
        return new_group

    @log_exceptions
    async def delete_group(self, group_name: str) -> Group | None:
        query = delete(Group).where(Group.group_name == group_name).returning(Group.group_name)
        res = await self.db_session.execute(query)
        return res.fetchone() or None

    @log_exceptions
    async def get_group(self, group_name: str) -> Group | None:
        query = select(Group).where(Group.group_name == group_name)
        res = await self.db_session.execute(query)
        return res.scalar_one_or_none()

    @log_exceptions
    async def get_all_group(self, page: int, limit: int) -> list[Group] | None:
        if page == 0:
            query = select(Group).order_by(Group.group_name.asc())
        else:
            query = select(Group).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        groups = list(result.scalars().all())
        return groups

    @log_exceptions
    async def update_group(self, group_name: str, **kwargs) -> Group | None:
        query = (
            update(Group)
            .where(Group.group_name == group_name)
            .values(**kwargs)
            .returning(Group.group_name)
        )
        res = await self.db_session.execute(query)
        return res.scalar()


'''
==========
Curriculum
==========
'''


class CurriculumDAL:
    """Data Access Layer for operating curriculum info"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_curriculum(
            self, semester_number: int, group_name: str, subject_code: str,
            lectures_hours: float = None, laboratory_hours: float = None, practical_hours: float = None
    ) -> Curriculum:
        new_curriculum = Curriculum(
            semester_number=semester_number,
            group_name=group_name,
            subject_code=subject_code,
            lectures_hours=lectures_hours,
            laboratory_hours=laboratory_hours,
            practical_hours=practical_hours
        )
        self.db_session.add(new_curriculum)
        await self.db_session.flush()
        return new_curriculum

    @log_exceptions
    async def delete_curriculum(self, semester_number: int, group_name: str,
                                subject_code: str) -> Curriculum | None:
        query = (
            delete(Curriculum)
            .where(
                Curriculum.semester_number == semester_number,
                Curriculum.group_name == group_name,
                Curriculum.subject_code == subject_code
            )
        )
        res = await self.db_session.execute(query)
        return res.fetchone() or None

    @log_exceptions
    async def get_all_curriculums(self, page: int, limit: int) -> list[Curriculum] | None:
        if page == 0:
            query = select(Curriculum).order_by(Curriculum.semester_number.asc())
        else:
            query = select(Curriculum).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        curriculums = list(result.scalars().all())
        return curriculums

    @log_exceptions
    async def get_curriculum(self, semester_number: int, group_name: str, subject_code: str) -> Curriculum | None:
        query = select(Curriculum).where(
            Curriculum.semester_number == semester_number,
            Curriculum.group_name == group_name,
            Curriculum.subject_code == subject_code
        )
        res = await self.db_session.execute(query)
        return res.scalar_one_or_none()
    
    async def get_group(self, group_name: str) -> Group | None:
        query = select(Group).where(Group.group_name == group_name)
        res = await self.db_session.execute(query)
        return res.scalar_one_or_none()
