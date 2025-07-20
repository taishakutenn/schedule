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
        return new_teacher

    @log_exceptions
    async def delete_teacher(self, id: int) -> ShowTeacher | None:
        query_select = select(Teacher).where(Teacher.id == id)
        res = await self.db_session.execute(query_select)
        teacher = res.scalar_one_or_none()
        if teacher is None:
            return None
        query_delete = delete(Teacher).where(Teacher.id == id)
        await self.db_session.execute(query_delete)
        return ShowTeacher(
            name=teacher.name,
            surname=teacher.surname,
            phone_number=teacher.phone_number,
            email=teacher.email,
            fathername=teacher.fathername
        )

    @log_exceptions
    async def get_all_teachers(self, page: int, limit: int) -> list[ShowTeacher] | None:
        if page == 0:
            query = select(Teacher).order_by(Teacher.surname.asc())
        else:
            query = select(Teacher).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        teachers = result.scalars().all()
        if teachers:
            return [
                ShowTeacher(
                    name=t.name,
                    surname=t.surname,
                    email=t.email,
                    phone_number=t.phone_number,
                    fathername=t.fathername
                ) for t in teachers
            ]
        return None

    @log_exceptions
    async def get_teacher_by_id(self, id) -> Teacher | None:
        query = select(Teacher).where(Teacher.id == id)
        res = await self.db_session.execute(query)
        teacher_row = res.scalar()
        if teacher_row is not None:
            return Teacher(
                name=teacher_row.name,
                surname=teacher_row.surname,
                phone_number=teacher_row.phone_number,
                email=teacher_row.email,
                fathername=teacher_row.fathername
            )
        return None

    @log_exceptions
    async def get_teacher_by_name_surname(self, name: str, surname: str) -> Teacher | None:
        query = select(Teacher).where((Teacher.name == name) & (Teacher.surname == surname))
        res = await self.db_session.execute(query)
        teacher_row = res.scalar()
        if teacher_row is not None:
            return Teacher(
                name=teacher_row.name,
                surname=teacher_row.surname,
                phone_number=teacher_row.phone_number,
                email=teacher_row.email,
                fathername=teacher_row.fathername
            )
        return None

    @log_exceptions
    async def update_teacher(self, id, **kwargs) -> Optional[Teacher]:
        query = update(Teacher).where(Teacher.id == id).values(**kwargs).returning(Teacher)
        res = await self.db_session.execute(query)
        return res.scalar()


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
    async def delete_building(self, building_number: int) -> bool:
        query = delete(Building).where(Building.building_number == building_number).returning(Building.building_number)
        res = await self.db_session.execute(query)
        deleted_building = res.fetchone()
        return bool(deleted_building)

    @log_exceptions
    async def get_all_buildings(self, page: int, limit: int) -> list[ShowBuilding] | None:
        if page == 0:
            query = select(Building).order_by(Building.building_number.asc())
        else:
            query = select(Building).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        buildings = result.scalars().all()
        if buildings:
            return [
                ShowBuilding(
                    building_number=b.building_number,
                    city=b.city,
                    building_address=b.building_address
                ) for b in buildings
            ]
        return None

    @log_exceptions
    async def get_building_by_number(self, building_number: int) -> Building | None:
        query = select(Building).where(Building.building_number == building_number)
        res = await self.db_session.execute(query)
        building_row = res.scalar()
        if building_row is not None:
            return Building(
                building_number=building_row.building_number,
                city=building_row.city,
                building_address=building_row.building_address
            )
        return None

    @log_exceptions
    async def get_building_by_address(self, building_address: str) -> Building | None:
        query = select(Building).where(Building.building_address == building_address)
        res = await self.db_session.execute(query)
        building_row = res.scalar()
        if building_row is not None:
            return Building(
                building_number=building_row.building_number,
                city=building_row.city,
                building_address=building_row.building_address
            )
        return None

    @log_exceptions
    async def update_building(self, building_number, **kwargs) -> Building | None:
        query = update(Building).where(Building.building_number == building_number).values(**kwargs).returning(Building)
        res = await self.db_session.execute(query)
        return res.scalar()


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
    async def delete_cabinet(self, building_number: int, cabinet_number: int) -> Cabinet | False:
        query = delete(Cabinet).where(
            (Cabinet.cabinet_number == cabinet_number) & (Cabinet.building_number == building_number)
        ).returning(Cabinet)
        res = await self.db_session.execute(query)
        return res.fetchone() or False

    @log_exceptions
    async def get_cabinet(self, cabinet_number: int) -> Optional[Cabinet]:
        query = select(Cabinet).where(Cabinet.cabinet_number == cabinet_number)
        res = await self.db_session.execute(query)
        cabinet_row = res.scalar()
        return cabinet_row.id if cabinet_row else None

    @log_exceptions
    async def get_cabinet_by_number_and_building(self, building_number: int, cabinet_number: int) -> Cabinet | None:
        query = select(Cabinet).where(
            (Cabinet.cabinet_number == cabinet_number) &
            (Cabinet.building_number == building_number)
        )
        res = await self.db_session.execute(query)
        return res.scalar_one_or_none()

    @log_exceptions
    async def get_all_cabinets(self, page: int, limit: int) -> list[ShowCabinet] | None:
        if page == 0:
            query = select(Cabinet).order_by(Cabinet.cabinet_number.asc())
        else:
            query = select(Cabinet).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        cabinets = result.scalars().all()
        if cabinets:
            return [
                ShowCabinet(
                    cabinet_number=c.cabinet_number,
                    capacity=c.capacity,
                    cabinet_state=c.cabinet_state,
                    building_number=c.building_number
                ) for c in cabinets
            ]
        return None

    @log_exceptions
    async def get_cabinets_by_building(self, building_number: int, page: int, limit: int) -> list[ShowCabinet] | None:
        if page == 0:
            query = select(Cabinet).where(Cabinet.building_number == building_number).order_by(Cabinet.cabinet_number.asc())
        else:
            query = select(Cabinet).where(Cabinet.building_number == building_number).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        cabinets = result.scalars().all()
        if cabinets:
            return [
                ShowCabinet(
                    cabinet_number=c.cabinet_number,
                    capacity=c.capacity,
                    cabinet_state=c.cabinet_state,
                    building_number=c.building_number
                ) for c in cabinets
            ]
        return None

    @log_exceptions
    async def update(self, building_number: int, cabinet_number: int, **kwargs) -> Cabinet | None:
        query = update(Cabinet).where(
            (Cabinet.cabinet_number == cabinet_number) & (Cabinet.building_number == building_number)
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
        query_select = select(Speciality).where(Speciality.speciality_code == speciality_code)
        res = await self.db_session.execute(query_select)
        speciality = res.scalar_one_or_none()
        if speciality is None:
            return None
        query_delete = delete(Speciality).where(Speciality.speciality_code == speciality_code)
        await self.db_session.execute(query_delete)
        return speciality

    @log_exceptions
    async def get_all_speciality(self, page: int, limit: int) -> list[ShowSpeciality] | None:
        if page == 0:
            query = select(Speciality).order_by(Speciality.speciality_code.asc())
        else:
            query = select(Speciality).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        specialities = result.scalars().all()
        if specialities:
            return [ShowSpeciality(speciality_code=sp.speciality_code) for sp in specialities]
        return None

    @log_exceptions
    async def get_speciality_by_code(self, speciality_code) -> ShowSpeciality | None:
        query = select(Speciality).where(Speciality.speciality_code == speciality_code)
        res = await self.db_session.execute(query)
        return res.scalar()

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
        return res.fetchone()

    @log_exceptions
    async def get_group(self, group_name: str) -> Group | None:
        query = select(Group).where(Group.group_name == group_name)
        res = await self.db_session.execute(query)
        return res.scalar()

    @log_exceptions
    async def get_all_group(self, page: int, limit: int) -> list[ShowGroup] | None:
        if page == 0:
            query = select(Group).order_by(Group.group_name.asc())
        else:
            query = select(Group).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        groups = result.scalars().all()
        if groups:
            return [
                ShowGroup(
                    group_name=gr.group_name,
                    speciality_code=gr.speciality_code,
                    quantity_students=gr.quantity_students,
                    group_advisor_id=gr.group_advisor_id
                ) for gr in groups
            ]
        return None

    @log_exceptions
    async def update(self, group_name: str, **kwargs) -> Group | None:
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
    async def delete_curriculum(self, semester_number: int, group_name: str, subject_code: str) -> ShowCurriculum | None:
        query_select = (
            select(Curriculum)
            .where(
                Curriculum.semester_number == semester_number,
                Curriculum.group_name == group_name,
                Curriculum.subject_code == subject_code
            )
        )
        res = await self.db_session.execute(query_select)
        curriculum = res.scalar_one_or_none()
        if curriculum is None:
            return None
        query_delete = delete(Curriculum).where(
            Curriculum.semester_number == semester_number,
            Curriculum.group_name == group_name,
            Curriculum.subject_code == subject_code
        )
        await self.db_session.execute(query_delete)
        return ShowCurriculum(
            semester_number=curriculum.semester_number,
            group_name=curriculum.group_name,
            subject_code=curriculum.subject_code,
            lectures_hours=curriculum.lectures_hours,
            laboratory_hours=curriculum.laboratory_hours,
            practical_hours=curriculum.practical_hours
        )

    @log_exceptions
    async def get_all_curriculums(self, page: int, limit: int) -> list[ShowCurriculum] | None:
        if page == 0:
            query = select(Curriculum).order_by(Curriculum.semester_number.asc())
        else:
            query = select(Curriculum).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        curriculums = result.scalars().all()
        if curriculums:
            return [
                ShowCurriculum(
                    semester_number=c.semester_number,
                    group_name=c.group_name,
                    subject_code=c.subject_code,
                    lectures_hours=c.lectures_hours,
                    laboratory_hours=c.laboratory_hours,
                    practical_hours=c.practical_hours
                ) for c in curriculums
            ]
        return None

    @log_exceptions
    async def get_curriculum(self, semester_number: int, group_name: str, subject_code: str) -> Curriculum | None:
        query = select(Curriculum).where(
            Curriculum.semester_number == semester_number,
            Curriculum.group_name == group_name,
            Curriculum.subject_code == subject_code
        )
        res = await self.db_session.execute(query)
        curriculum_row = res.scalar()
        if curriculum_row is not None:
            return Curriculum(
                semester_number=curriculum_row.semester_number,
                group_name=curriculum_row.group_name,
                subject_code=curriculum_row.subject_code,
                lectures_hours=curriculum_row.lectures_hours,
                laboratory_hours=curriculum_row.laboratory_hours,
                practical_hours=curriculum_row.practical_hours
            )
        return None
