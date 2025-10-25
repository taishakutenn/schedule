from typing import Optional

from fastapi import Depends
from sqlalchemy import select, delete, update, Date
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Certification, Teacher, Group, Cabinet, Building, Speciality, Session, TeacherCategory, SessionType, Semester, Plan, Chapter, Cycle, Module, SubjectsInCycle, SubjectsInCycleHours, TeacherInPlan
from config.decorators import log_exceptions
from db.session import get_db

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
            self, name: str, surname: str, phone_number: str, email: str = None, fathername: str = None, salary_rate: float = None, teacher_category: str = None
    ) -> Teacher:
        new_teacher = Teacher(
            name=name,
            surname=surname,
            phone_number=phone_number,
            email=email,
            fathername=fathername,
            salary_rate=salary_rate,
            teacher_category=teacher_category
        )
        self.db_session.add(new_teacher)
        await self.db_session.flush()
        return new_teacher

    @log_exceptions
    async def delete_teacher(self, id: int) -> Teacher | None:
        query_select = select(Teacher).where(Teacher.id == id)
        res = await self.db_session.execute(query_select)
        teacher = res.scalar_one_or_none()
        if teacher:
            await self.db_session.execute(delete(Teacher).where(Teacher.id == id))
            await self.db_session.flush()
        return teacher

    @log_exceptions
    async def get_all_teachers(self, page: int, limit: int) -> list[Teacher]:
        query = select(Teacher).order_by(Teacher.id.asc())
        if page > 0:
            query = query.offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    @log_exceptions
    async def get_teacher_by_id(self, id: int) -> Teacher | None:
        query = select(Teacher).where(Teacher.id == id)
        res = await self.db_session.execute(query)
        return res.scalar_one_or_none()

    @log_exceptions
    async def get_teacher_by_name_surname(self, name: str, surname: str) -> Teacher | None:
        result = await self.db_session.execute(select(Teacher).where((Teacher.name == name) & (Teacher.surname == surname)))
        return result.scalar_one_or_none()

    @log_exceptions
    async def update_teacher(self, id: int, **kwargs) -> Teacher | None:
        result = await self.db_session.execute(update(Teacher).where(Teacher.id == id).values(**kwargs).returning(Teacher))
        updated_teacher = result.scalar_one_or_none()
        if updated_teacher:
            await self.db_session.flush()
        return updated_teacher

    @log_exceptions
    async def get_teacher_by_email(self, email: str) -> Teacher | None:
        query = select(Teacher).where(Teacher.email == email)
        res = await self.db_session.execute(query)
        return res.scalar_one_or_none()

    @log_exceptions
    async def get_teacher_by_phone_number(self, phone_number: str) -> Teacher | None:
        query = select(Teacher).where(Teacher.phone_number == phone_number)
        res = await self.db_session.execute(query)
        return res.scalar_one_or_none()

    @log_exceptions
    async def get_all_teachers_by_category(self, category: str, page: int, limit: int) -> list[Teacher]:
        query = select(Teacher).where(Teacher.teacher_category == category).order_by(Teacher.id.asc())
        if page > 0:
            query = query.offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        return list(result.scalars().all())


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
        building_row = res.scalar_one_or_none()
        return building_row

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
================
DAL for Cabinet
================
'''
class CabinetDAL:
    """Data Access Layer for operating cabinet info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_cabinet(self, cabinet_number: int, building_number: int, capacity: int = None, cabinet_state: str = None) -> Cabinet:
        new_cabinet = Cabinet(
            cabinet_number=cabinet_number,
            building_number=building_number,
            capacity=capacity,
            cabinet_state=cabinet_state
        )
        self.db_session.add(new_cabinet)
        await self.db_session.flush()
        return new_cabinet

    @log_exceptions
    async def delete_cabinet(self, building_number: int, cabinet_number: int) -> Cabinet | None:
        query = delete(Cabinet).where((Cabinet.cabinet_number == cabinet_number) & (Cabinet.building_number == building_number)).returning(Cabinet)
        res = await self.db_session.execute(query)
        deleted_cabinet = res.scalar_one_or_none()
        return deleted_cabinet

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
            query = select(Cabinet).where(Cabinet.building_number == building_number).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        cabinets = list(result.scalars().all())
        return cabinets

    @log_exceptions
    async def get_cabinet_by_number_and_building(self, building_number: int, cabinet_number: int) -> Cabinet | None:
        query = select(Cabinet).where((Cabinet.cabinet_number == cabinet_number) &
                                      (Cabinet.building_number == building_number))
        res = await self.db_session.execute(query)
        cabinet_row = res.scalar_one_or_none()
        return cabinet_row

    @log_exceptions
    async def update_cabinet(self, search_building_number: int, search_cabinet_number: int, **kwargs) -> Cabinet | None:
        """
        We use that names for the variables we are searching for because
        in **kwargs there are already variables with names: building_number and cabinet_number
        """
        query = update(Cabinet).where(
            (Cabinet.cabinet_number == search_cabinet_number) & (Cabinet.building_number == search_building_number)).values(**kwargs).returning(Cabinet)
        res = await self.db_session.execute(query)
        return res.scalar_one_or_none()


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
        new_speciality = Speciality(
            speciality_code=speciality_code
        )
        self.db_session.add(new_speciality)
        await self.db_session.flush()
        return new_speciality

    @log_exceptions
    async def delete_speciality(self, speciality_code: str) -> Speciality | None:
        query = delete(Speciality).where(Speciality.speciality_code == speciality_code).returning(Speciality)
        res = await self.db_session.execute(query)
        deleted_speciality = res.scalar_one_or_none()
        return deleted_speciality

    @log_exceptions
    async def get_all_specialities(self, page: int, limit: int) -> list[Speciality]:
        if page == 0:
            query = select(Speciality).order_by(Speciality.speciality_code.asc())
        else:
            query = select(Speciality).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        specialities = list(result.scalars().all())
        return specialities

    @log_exceptions
    async def get_speciality(self, speciality_code: str) -> Speciality | None:
        query = select(Speciality).where(Speciality.speciality_code == speciality_code)
        res = await self.db_session.execute(query)
        speciality_row = res.scalar_one_or_none()
        return speciality_row

    @log_exceptions
    async def update_speciality(self, target_code: str, **kwargs) -> Speciality | None:
        query = update(Speciality).where(Speciality.speciality_code == target_code).values(**kwargs).returning(Speciality)
        res = await self.db_session.execute(query)
        updated_speciality = res.scalar_one_or_none()
        return updated_speciality


'''
================
DAL for Group
================
'''
class GroupDAL:
    """Data Access Layer for operating group info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_group(self, group_name: str, speciality_code: str = None, quantity_students: int = None, group_advisor_id: int = None) -> Group:
        new_group = Group(
            group_name=group_name,
            speciality_code=speciality_code,
            quantity_students=quantity_students,
            group_advisor_id=group_advisor_id
        )
        self.db_session.add(new_group)
        await self.db_session.flush()
        return new_group

    @log_exceptions
    async def delete_group(self, group_name: str) -> Group | None:
        query = delete(Group).where(Group.group_name == group_name).returning(Group)
        res = await self.db_session.execute(query)
        deleted_group = res.scalar_one_or_none()
        return deleted_group

    @log_exceptions
    async def get_all_groups(self, page: int, limit: int) -> list[Group]:
        if page == 0:
            query = select(Group).order_by(Group.group_name.asc())
        else:
            query = select(Group).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        groups = list(result.scalars().all())
        return groups

    @log_exceptions
    async def get_group_by_name(self, group_name: str) -> Group | None:
        query = select(Group).where(Group.group_name == group_name)
        res = await self.db_session.execute(query)
        group_row = res.scalar_one_or_none()
        return group_row

    @log_exceptions
    async def get_group_by_advisor_id(self, group_advisor_id: int) -> Group | None:
        query = select(Group).where(Group.group_advisor_id == group_advisor_id)
        res = await self.db_session.execute(query)
        group_row = res.scalar_one_or_none()
        return group_row
    
    @log_exceptions
    async def get_groups_by_speciality(self, speciality_code: str, page: int, limit: int) -> list[Group]:
        if page == 0:
            query = select(Group).where(Group.speciality_code == speciality_code).order_by(Group.group_name.asc())
        else:
            query = select(Group).where(Group.speciality_code == speciality_code).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        groups = list(result.scalars().all())
        return groups if groups is not None else []

    @log_exceptions
    async def update_group(self, target_group_name: str, **kwargs) -> Group | None:
        query = update(Group).where(Group.group_name == target_group_name).values(**kwargs).returning(Group)
        res = await self.db_session.execute(query)
        updated_group = res.scalar_one_or_none()
        return updated_group


# '''
# =========================
# DAL for EmploymentTeacher
# =========================
# '''


# class EmployTeacherDAL:
#     """Data Access Layer for operating teacher's employment info"""

#     def __init__(self, db_session: AsyncSession):
#         self.db_session = db_session

#     @log_exceptions
#     async def create_employTeacher(
#             self, date_start_period: Date, date_end_period: Date, teacher_id: int,  monday: str = None,
#             tuesday: str = None, wednesday: str = None, thursday: str = None,
#             friday: str = None, saturday: str = None
#     ) -> EmploymentTeacher:
#         new_employTeacher = EmploymentTeacher(
#             date_start_period=date_start_period,
#             date_end_period=date_end_period,
#             teacher_id=teacher_id,
#             monday=monday,
#             tuesday=tuesday,
#             wednesday=wednesday,
#             thursday=thursday,
#             friday=friday,
#             saturday=saturday
#         )
#         self.db_session.add(new_employTeacher)
#         await self.db_session.flush()
#         return new_employTeacher

#     @log_exceptions
#     async def delete_employTeacher(self, date_start_period: Date, date_end_period: Date,
#                                 teacher_id: int) -> EmploymentTeacher | None:
#         query = (
#             delete(EmploymentTeacher)
#             .where(
#                 EmploymentTeacher.date_start_period == date_start_period,
#                 EmploymentTeacher.date_end_period == date_end_period,
#                 EmploymentTeacher.teacher_id == teacher_id
#             )
#             .returning(EmploymentTeacher)
#         )
#         res = await self.db_session.execute(query)
#         deleted_emloyTeacher = res.scalar_one_or_none()
#         return deleted_emloyTeacher

#     @log_exceptions
#     async def get_all_employTeacher(self, page: int, limit: int) -> list[EmploymentTeacher] | None:
#         if page == 0:
#             query = select(EmploymentTeacher).order_by(EmploymentTeacher.date_start_period.asc())
#         else:
#             query = select(EmploymentTeacher).offset((page - 1) * limit).limit(limit)
#         result = await self.db_session.execute(query)
#         employs = list(result.scalars().all())
#         return employs

#     @log_exceptions
#     async def get_all_employTeacher_by_teacher(self, teacher_id, page: int, limit: int) -> list[EmploymentTeacher] | None:
#         if page == 0:
#             query = select(EmploymentTeacher).where(EmploymentTeacher.teacher_id == teacher_id).order_by(EmploymentTeacher.date_start_period.asc())
#         else:
#             query = select(EmploymentTeacher).offset((page - 1) * limit).limit(limit)
#         result = await self.db_session.execute(query)
#         employs = list(result.scalars().all())
#         return employs

#     @log_exceptions
#     async def get_employTeacher(self, date_start_period: Date, date_end_period: Date,
#                             teacher_id: int) -> EmploymentTeacher | None:
#         query = select(EmploymentTeacher).where(
#             EmploymentTeacher.date_start_period == date_start_period,
#             EmploymentTeacher.date_end_period == date_end_period,
#             EmploymentTeacher.teacher_id == teacher_id
#         )
#         res = await self.db_session.execute(query)
#         return res.scalar_one_or_none()

#     @log_exceptions
#     async def get_all_employTeacher_by_date(self, date_start_period: Date, date_end_period: Date,
#                                         page: int, limit: int) -> list[EmploymentTeacher] | None:
#         if page == 0:
#             query = select(EmploymentTeacher).where(
#                 EmploymentTeacher.date_start_period == date_start_period,
#                 EmploymentTeacher.date_end_period == date_end_period
#             ).order_by(EmploymentTeacher.date_start_period.asc())
#         else:
#             query = select(EmploymentTeacher).offset((page - 1) * limit).limit(limit)
#         result = await self.db_session.execute(query)
#         employs = list(result.scalars().all())
#         return employs

#     # tg_ mean target
#     @log_exceptions
#     async def update_employTeacher(self, tg_date_start_period: Date, tg_date_end_period: Date, tg_teacher_id: int, **kwargs) -> EmploymentTeacher | None:
#         query = (
#             update(EmploymentTeacher)
#             .where(
#                 EmploymentTeacher.date_start_period == tg_date_start_period,
#                 EmploymentTeacher.date_end_period == tg_date_end_period,
#                 EmploymentTeacher.teacher_id == tg_teacher_id
#             )
#             .values(**kwargs)
#             .returning(EmploymentTeacher)
#         )
#         res = await self.db_session.execute(query)
#         return res.scalar_one_or_none()


'''
===============
DAL for Session
===============
'''


class SessionDAL:
    """Data Access Layer for operating session info"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_session(
            self, session_number: int, date: Date, group_name: str,  session_type: str,
            subject_code: str = None, teacher_id: int = None, cabinet_number: int = None,
            building_number: int = None
    ) -> Session:
        new_session = Session(
            session_number=session_number,
            date=date,
            group_name=group_name,
            session_type=session_type,
            subject_code=subject_code,
            teacher_id=teacher_id,
            cabinet_number=cabinet_number,
            building_number=building_number
        )
        self.db_session.add(new_session)
        await self.db_session.flush()
        return new_session

    @log_exceptions
    async def delete_session(self, session_number: int, date: Date, group_name: str) -> Session | None:
        query = (
            delete(Session)
            .where(
                Session.session_number == session_number,
                Session.date == date,
                Session.group_name == group_name
            ).returning(Session)
        )
        res = await self.db_session.execute(query)
        deleted_session = res.scalar_one_or_none()
        return deleted_session

    @log_exceptions
    async def get_all_sessions(self, page: int, limit: int) -> list[Session] | None:
        if page == 0:
            query = select(Session).order_by(Session.session_number.asc())
        else:
            query = select(Session).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        sessions = list(result.scalars().all())
        return sessions

    @log_exceptions
    async def get_session(self, session_number: int, date: Date, group_name: str) -> Session | None:
        query = select(Session).where(
                Session.session_number == session_number,
                Session.date == date,
                Session.group_name == group_name
            )
        res = await self.db_session.execute(query)
        return res.scalar_one_or_none()

    @log_exceptions
    async def get_all_sessions_by_date(self, date: Date, page: int, limit: int) -> list[Session] | None:
        if page == 0:
            query = select(Session).where(Session.date == date).order_by(Session.session_number.asc())
        else:
            query = select(Session).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        sessions = list(result.scalars().all())
        return sessions

    @log_exceptions
    async def get_all_sessions_by_teacher(self, teacher_id: int, page: int, limit: int) -> list[Session] | None:
        if page == 0:
            query = select(Session).where(Session.teacher_id == teacher_id).order_by(Session.date.asc())
        else:
            query = select(Session).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        sessions = list(result.scalars().all())
        return sessions

    @log_exceptions
    async def get_all_sessions_by_group(self, group_name: str, page: int, limit: int) -> list[Session] | None:
        if page == 0:
            query = select(Session).where(Session.group_name == group_name).order_by(Session.date.asc())
        else:
            query = select(Session).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        sessions = list(result.scalars().all())
        return sessions

    @log_exceptions
    async def get_all_sessions_by_subject(self, subject: str, page: int, limit: int) -> list[Session] | None:
        if page == 0:
            query = select(Session).where(Session.subject_code == subject).order_by(Session.date.asc())
        else:
            query = select(Session).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        sessions = list(result.scalars().all())
        return sessions

    # tg_ mean target
    @log_exceptions
    async def update_session(self, tg_session_number: int, tg_date: Date, tg_group_name: str, **kwargs) -> Session | None:
        query = (
            update(Session)
            .where(
                Session.session_number == tg_session_number,
                Session.date == tg_date,
                Session.group_name == tg_group_name
            )
            .values(**kwargs)
            .returning(Session)
        )
        res = await self.db_session.execute(query)
        return res.scalar_one_or_none()


# '''
# ===============
# DAL for Subject
# ===============
# '''


# class SubjectDAL:
#     """Data Access Layer for operating subject info"""

#     def __init__(self, db_session: AsyncSession):
#         self.db_session = db_session

#     @log_exceptions
#     async def create_subject(self, subject_code: str, name: str = None) -> Subject:
#         new_subject = Subject(
#             subject_code=subject_code,
#             name = name
#         )
#         self.db_session.add(new_subject)
#         await self.db_session.flush()
#         return new_subject

#     @log_exceptions
#     async def delete_subject(self, subject_code: str) -> Subject | None:
#         query = delete(Subject).where(Subject.subject_code == subject_code).returning(Subject)
#         res = await self.db_session.execute(query)
#         deleted_subject = res.scalar_one_or_none()
#         return deleted_subject

#     @log_exceptions
#     async def get_subject(self, subject_code: str) -> Subject | None:
#         query = select(Subject).where(
#                 Subject.subject_code == subject_code
#             )
#         res = await self.db_session.execute(query)
#         return res.scalar_one_or_none()

#     @log_exceptions
#     async def get_all_subjects(self, page: int, limit: int) -> list[Subject] | None:
#         if page == 0:
#             query = select(Subject).order_by(Subject.subject_code.asc())
#         else:
#             query = select(Subject).offset((page - 1) * limit).limit(limit)
#         result = await self.db_session.execute(query)
#         subjects = list(result.scalars().all())
#         return subjects

#     @log_exceptions
#     async def get_subjects_by_name(self, name: str, page: int, limit: int) -> list[Subject] | None:
#         if page == 0:
#             query = select(Subject).where(Subject.name == name).order_by(Subject.subject_code.asc())
#         else:
#             query = select(Subject).where(Subject.name == name).offset((page - 1) * limit).limit(limit)
#         result = await self.db_session.execute(query)
#         subjects = list(result.scalars().all())
#         return subjects

#     # tg_ mean target
#     @log_exceptions
#     async def update_subject(self, tg_subject_code: int, **kwargs) -> Subject | None:
#         query = (
#             update(Subject)
#             .where(Subject.subject_code == tg_subject_code)
#             .values(**kwargs)
#             .returning(Subject)
#         )
#         res = await self.db_session.execute(query)
#         return res.scalar_one_or_none()


# '''
# ======================
# DAL for TeacherRequest
# ======================
# '''


# class TeacherRequestDAL:
#     """Data Access Layer for operating teachers requests info"""

#     def __init__(self, db_session: AsyncSession):
#         self.db_session = db_session

#     @log_exceptions
#     async def create_teacherRequest(
#             self, date_request: Date, teacher_id: int, subject_code: str, group_name: str,
#             lectures_hours: int, laboratory_hours: int, practice_hours: int,
#     ) -> TeacherRequest:
#         new_teacherRequest = TeacherRequest(
#             date_request=date_request,
#             teacher_id=teacher_id,
#             subject_code=subject_code,
#             group_name=group_name,
#             lectures_hours=lectures_hours,
#             laboratory_hours=laboratory_hours,
#             practice_hours=practice_hours
#         )
#         self.db_session.add(new_teacherRequest)
#         await self.db_session.flush()
#         return new_teacherRequest

#     @log_exceptions
#     async def delete_teacherRequest(self, date_request: Date, teacher_id: int,
#                                     subject_code: str, group_name: str) -> TeacherRequest | None:
#         query = delete(TeacherRequest).where(
#             TeacherRequest.date_request == date_request,
#             TeacherRequest.teacher_id == teacher_id,
#             TeacherRequest.subject_code == subject_code,
#             TeacherRequest.group_name == group_name
#             ).returning(TeacherRequest)
#         res = await self.db_session.execute(query)
#         teacherRequest = res.scalar_one_or_none()
#         return teacherRequest

#     @log_exceptions
#     async def get_all_teachersRequests(self, page: int, limit: int) -> list[TeacherRequest]:
#         query = select(TeacherRequest).order_by(TeacherRequest.date_request.asc())
#         if page > 0:
#             query = query.offset((page - 1) * limit).limit(limit)

#         result = await self.db_session.execute(query)
#         return list(result.scalars().all())

#     @log_exceptions
#     async def get_teacherRequest(self, date_request: Date, teacher_id: int,
#                                 subject_code: str, group_name: str) -> TeacherRequest | None:
#         result = await self.db_session.execute(select(TeacherRequest).
#             where(TeacherRequest.date_request == date_request,
#                 TeacherRequest.teacher_id == teacher_id,
#                 TeacherRequest.subject_code == subject_code,
#                 TeacherRequest.group_name == group_name))
#         return result.scalar_one_or_none()

#     @log_exceptions
#     async def get_all_requests_by_teacher(self, teacher_id: int, page: int, limit: int) -> list[TeacherRequest]:
#         query = select(TeacherRequest).where(TeacherRequest.teacher_id == teacher_id
#             ).order_by(TeacherRequest.date_request.asc())
#         if page > 0:
#             query = query.offset((page - 1) * limit).limit(limit)

#         result = await self.db_session.execute(query)
#         return list(result.scalars().all())

#     @log_exceptions
#     async def get_all_requests_by_group(self, group: str, page: int, limit: int) -> list[TeacherRequest]:
#         query = select(TeacherRequest).where(TeacherRequest.group_name == group
#             ).order_by(TeacherRequest.date_request.asc())
#         if page > 0:
#             query = query.offset((page - 1) * limit).limit(limit)

#         result = await self.db_session.execute(query)
#         return list(result.scalars().all())

#     @log_exceptions
#     async def get_all_requests_by_subject(self, subject: str, page: int, limit: int) -> list[TeacherRequest]:
#         query = select(TeacherRequest).where(TeacherRequest.subject_code == subject
#             ).order_by(TeacherRequest.date_request.asc())
#         if page > 0:
#             query = query.offset((page - 1) * limit).limit(limit)

#         result = await self.db_session.execute(query)
#         return list(result.scalars().all())

#     # tg_ mean target
#     @log_exceptions
#     async def update_teacherRequest(self, tg_date_request: Date, tg_teacher_id: int,
#                                 tg_subject_code: str, tg_group_name: str, **kwargs) -> TeacherRequest | None:
#         result = await self.db_session.execute(
#             update(TeacherRequest).where(
#             TeacherRequest.date_request == tg_date_request,
#             TeacherRequest.teacher_id == tg_teacher_id,
#             TeacherRequest.subject_code == tg_subject_code,
#             TeacherRequest.group_name == tg_group_name
#             ).values(**kwargs).returning(TeacherRequest)
#         )
#         return result.scalar_one_or_none()


'''
================
DAL for TeacherCategory
================
'''
class TeacherCategoryDAL:
    """Data Access Layer for operating teacher category info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_teacher_category(
            self, teacher_category: str
) -> TeacherCategory:
        new_category = TeacherCategory(
            teacher_category=teacher_category
        )
        self.db_session.add(new_category)
        await self.db_session.flush()
        return new_category

    @log_exceptions
    async def delete_teacher_category(self, teacher_category: str) -> TeacherCategory | None:
        query = delete(TeacherCategory).where(TeacherCategory.teacher_category == teacher_category).returning(TeacherCategory)
        res = await self.db_session.execute(query)
        deleted_category = res.scalar_one_or_none()
        return deleted_category

    @log_exceptions
    async def get_all_teacher_categories(self, page: int, limit: int) -> list[TeacherCategory]:
        if page == 0:
            query = select(TeacherCategory).order_by(TeacherCategory.teacher_category.asc())
        else:
            query = select(TeacherCategory).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        categories = list(result.scalars().all())
        return categories

    @log_exceptions
    async def get_teacher_category(self, teacher_category: str) -> TeacherCategory | None:
        query = select(TeacherCategory).where(TeacherCategory.teacher_category == teacher_category)
        res = await self.db_session.execute(query)
        return res.scalar_one_or_none()

    @log_exceptions
    async def update_teacher_category(self, target_category: str, **kwargs) -> TeacherCategory | None:
        query = (
            update(TeacherCategory)
            .where(TeacherCategory.teacher_category == target_category)
            .values(**kwargs)
            .returning(TeacherCategory)
        )
        res = await self.db_session.execute(query)
        return res.scalar_one_or_none()


'''
===================
DAL for SessionType
===================
'''
class SessionTypeDAL:
    """Data Access Layer for operating session type info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_session_type(self, name: str) -> SessionType:
        new_type = SessionType(
            name=name
        )
        self.db_session.add(new_type)
        await self.db_session.flush()
        return new_type

    @log_exceptions
    async def delete_session_type(self, name: str) -> SessionType | None:
        query = delete(SessionType).where(SessionType.name == name).returning(SessionType)
        res = await self.db_session.execute(query)
        deleted_type = res.scalar_one_or_none()
        return deleted_type

    @log_exceptions
    async def get_all_session_types(self, page: int, limit: int) -> list[SessionType]:
        if page == 0:
            query = select(SessionType).order_by(SessionType.name.asc())
        else:
            query = select(SessionType).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        types = list(result.scalars().all())
        return types

    @log_exceptions
    async def get_session_type(self, name: str) -> SessionType | None:
        query = select(SessionType).where(SessionType.name == name)
        res = await self.db_session.execute(query)
        type_row = res.scalar_one_or_none()
        return type_row

    @log_exceptions
    async def update_session_type(self, current_name: str, **kwargs) -> SessionType | None:
        query = update(SessionType).where(SessionType.name == current_name).values(**kwargs).returning(SessionType)
        res = await self.db_session.execute(query)
        updated_type = res.scalar_one_or_none()
        return updated_type


'''
================
DAL for Semester
================
'''
class SemesterDAL:
    """Data Access Layer for operating semester info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_semester(self, semester: int, weeks: float, practice_weeks: int, plan_id: int) -> Semester:
        new_semester = Semester(
            semester=semester,
            weeks=weeks,
            practice_weeks=practice_weeks,
            plan_id=plan_id
        )
        self.db_session.add(new_semester)
        await self.db_session.flush()
        return new_semester

    @log_exceptions
    async def delete_semester(self, semester: int, plan_id: int) -> Semester | None:
        query = delete(Semester).where((Semester.semester == semester) & (Semester.plan_id == plan_id)).returning(Semester)
        res = await self.db_session.execute(query)
        deleted_semester = res.scalar_one_or_none()
        return deleted_semester

    @log_exceptions
    async def get_all_semesters(self, page: int, limit: int) -> list[Semester]:
        if page == 0:
            query = select(Semester).order_by(Semester.semester.asc())
        else:
            query = select(Semester).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        semesters = list(result.scalars().all())
        return semesters

    @log_exceptions
    async def get_semester_by_semester_and_plan(self, semester: int, plan_id: int) -> Semester | None:
        query = select(Semester).where((Semester.semester == semester) & (Semester.plan_id == plan_id))
        res = await self.db_session.execute(query)
        semester_row = res.scalar_one_or_none()
        return semester_row

    @log_exceptions
    async def update_semester(self, target_semester: int, target_plan_id: int, **kwargs) -> Semester | None:
        query = update(Semester).where(
            (Semester.semester == target_semester) & (Semester.plan_id == target_plan_id)
        ).values(**kwargs).returning(Semester)
        res = await self.db_session.execute(query)
        updated_semester = res.scalar_one_or_none()
        return updated_semester
    

'''
================
DAL for Plan
================
'''
class PlanDAL:
    """Data Access Layer for operating plan info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_plan(self, year: int, speciality_code: str) -> Plan:
        new_plan = Plan(
            year=year,
            speciality_code=speciality_code
        )
        self.db_session.add(new_plan)
        await self.db_session.flush()
        return new_plan

    @log_exceptions
    async def delete_plan(self, id: int) -> Plan | None:
        query = delete(Plan).where(Plan.id == id).returning(Plan)
        res = await self.db_session.execute(query)
        deleted_plan = res.scalar_one_or_none()
        return deleted_plan

    @log_exceptions
    async def get_all_plans(self, page: int, limit: int) -> list[Plan]:
        if page == 0:
            query = select(Plan).order_by(Plan.id.asc())
        else:
            query = select(Plan).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        plans = list(result.scalars().all())
        return plans

    @log_exceptions
    async def get_plan_by_id(self, id: int) -> Plan | None:
        query = select(Plan).where(Plan.id == id)
        res = await self.db_session.execute(query)
        plan_row = res.scalar_one_or_none()
        return plan_row

    @log_exceptions
    async def update_plan(self, target_id: int, **kwargs) -> Plan | None:
        query = update(Plan).where(Plan.id == target_id).values(**kwargs).returning(Plan)
        res = await self.db_session.execute(query)
        updated_plan = res.scalar_one_or_none()
        return updated_plan


'''
================
DAL for Chapter
================
'''
class ChapterDAL:
    """Data Access Layer for operating chapter info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_chapter(self, code: str, name: str, plan_id: int) -> Chapter:
        new_chapter = Chapter(
            code=code,
            name=name,
            plan_id=plan_id
        )
        self.db_session.add(new_chapter)
        await self.db_session.flush()
        return new_chapter

    @log_exceptions
    async def delete_chapter(self, id: int) -> Chapter | None:
        query = delete(Chapter).where(Chapter.id == id).returning(Chapter)
        res = await self.db_session.execute(query)
        deleted_chapter = res.scalar_one_or_none()
        return deleted_chapter

    @log_exceptions
    async def get_all_chapters(self, page: int, limit: int) -> list[Chapter]:
        if page == 0:
            query = select(Chapter).order_by(Chapter.id.asc())
        else:
            query = select(Chapter).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        chapters = list(result.scalars().all())
        return chapters

    @log_exceptions
    async def get_chapter_by_id(self, id: int) -> Chapter | None:
        query = select(Chapter).where(Chapter.id == id)
        res = await self.db_session.execute(query)
        chapter_row = res.scalar_one_or_none()
        return chapter_row

    @log_exceptions
    async def get_chapters_by_plan(self, plan_id: int, page: int, limit: int) -> list[Chapter]:
        if page == 0:
            query = select(Chapter).where(Chapter.plan_id == plan_id).order_by(Chapter.id.asc())
        else:
            query = select(Chapter).where(Chapter.plan_id == plan_id).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        chapters = list(result.scalars().all())
        return chapters

    @log_exceptions
    async def update_chapter(self, target_id: int, **kwargs) -> Chapter | None:
        query = update(Chapter).where(Chapter.id == target_id).values(**kwargs).returning(Chapter)
        res = await self.db_session.execute(query)
        updated_chapter = res.scalar_one_or_none()
        return updated_chapter
    

'''
================
DAL for Cycle
================
'''
class CycleDAL:
    """Data Access Layer for operating cycle info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_cycle(self, contains_modules: bool, code: str, name: str, chapter_in_plan_id: int) -> Cycle:
        new_cycle = Cycle(
            contains_modules=contains_modules,
            code=code,
            name=name,
            chapter_in_plan_id=chapter_in_plan_id
        )
        self.db_session.add(new_cycle)
        await self.db_session.flush()
        return new_cycle

    @log_exceptions
    async def delete_cycle(self, id: int) -> Cycle | None:
        query = delete(Cycle).where(Cycle.id == id).returning(Cycle)
        res = await self.db_session.execute(query)
        deleted_cycle = res.scalar_one_or_none()
        return deleted_cycle

    @log_exceptions
    async def get_all_cycles(self, page: int, limit: int) -> list[Cycle]:
        if page == 0:
            query = select(Cycle).order_by(Cycle.id.asc())
        else:
            query = select(Cycle).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        cycles = list(result.scalars().all())
        return cycles

    @log_exceptions
    async def get_cycle_by_id(self, id: int) -> Cycle | None:
        query = select(Cycle).where(Cycle.id == id)
        res = await self.db_session.execute(query)
        cycle_row = res.scalar_one_or_none()
        return cycle_row

    @log_exceptions
    async def get_cycles_by_chapter(self, chapter_in_plan_id: int, page: int, limit: int) -> list[Cycle]:
        if page == 0:
            query = select(Cycle).where(Cycle.chapter_in_plan_id == chapter_in_plan_id).order_by(Cycle.id.asc())
        else:
            query = select(Cycle).where(Cycle.chapter_in_plan_id == chapter_in_plan_id).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        cycles = list(result.scalars().all())
        return cycles

    @log_exceptions
    async def update_cycle(self, target_id: int, **kwargs) -> Cycle | None:
        query = update(Cycle).where(Cycle.id == target_id).values(**kwargs).returning(Cycle)
        res = await self.db_session.execute(query)
        updated_cycle = res.scalar_one_or_none()
        return updated_cycle
    

'''
================
DAL for Module
================
'''
class ModuleDAL:
    """Data Access Layer for operating module info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_module(self, name: str, code: str, cycle_in_chapter_id: int) -> Module:
        new_module = Module(
            name=name,
            code=code,
            cycle_in_chapter_id=cycle_in_chapter_id
        )
        self.db_session.add(new_module)
        await self.db_session.flush()
        return new_module

    @log_exceptions
    async def delete_module(self, id: int) -> Module | None:
        query = delete(Module).where(Module.id == id).returning(Module)
        res = await self.db_session.execute(query)
        deleted_module = res.scalar_one_or_none()
        return deleted_module

    @log_exceptions
    async def get_all_modules(self, page: int, limit: int) -> list[Module]:
        if page == 0:
            query = select(Module).order_by(Module.id.asc())
        else:
            query = select(Module).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        modules = list(result.scalars().all())
        return modules

    @log_exceptions
    async def get_module_by_id(self, id: int) -> Module | None:
        query = select(Module).where(Module.id == id)
        res = await self.db_session.execute(query)
        module_row = res.scalar_one_or_none()
        return module_row

    @log_exceptions
    async def get_modules_by_cycle(self, cycle_in_chapter_id: int, page: int, limit: int) -> list[Module]:
        if page == 0:
            query = select(Module).where(Module.cycle_in_chapter_id == cycle_in_chapter_id).order_by(Module.id.asc())
        else:
            query = select(Module).where(Module.cycle_in_chapter_id == cycle_in_chapter_id).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        modules = list(result.scalars().all())
        return modules

    @log_exceptions
    async def update_module(self, target_id: int, **kwargs) -> Module | None:
        query = update(Module).where(Module.id == target_id).values(**kwargs).returning(Module)
        res = await self.db_session.execute(query)
        updated_module = res.scalar_one_or_none()
        return updated_module
    

'''
=======================
DAL for SubjectsInCycle
=======================
'''
class SubjectsInCycleDAL:
    """Data Access Layer for operating subjects in cycle info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_subject_in_cycle(self, code: str, title: str, cycle_in_chapter_id: int, module_in_cycle_id: int | None = None) -> SubjectsInCycle:
        new_subject_in_cycle = SubjectsInCycle(
            code=code,
            title=title,
            cycle_in_chapter_id=cycle_in_chapter_id,
            module_in_cycle_id=module_in_cycle_id
        )
        self.db_session.add(new_subject_in_cycle)
        await self.db_session.flush()
        return new_subject_in_cycle

    @log_exceptions
    async def delete_subject_in_cycle(self, id: int) -> SubjectsInCycle | None:
        query = delete(SubjectsInCycle).where(SubjectsInCycle.id == id).returning(SubjectsInCycle)
        res = await self.db_session.execute(query)
        deleted_subject_in_cycle = res.scalar_one_or_none()
        return deleted_subject_in_cycle

    @log_exceptions
    async def get_all_subjects_in_cycles(self, page: int, limit: int) -> list[SubjectsInCycle]:
        if page == 0:
            query = select(SubjectsInCycle).order_by(SubjectsInCycle.id.asc())
        else:
            query = select(SubjectsInCycle).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        subjects_in_cycles = list(result.scalars().all())
        return subjects_in_cycles

    @log_exceptions
    async def get_subject_in_cycle_by_id(self, id: int) -> SubjectsInCycle | None:
        query = select(SubjectsInCycle).where(SubjectsInCycle.id == id)
        res = await self.db_session.execute(query)
        subject_in_cycle_row = res.scalar_one_or_none()
        return subject_in_cycle_row

    @log_exceptions
    async def get_subjects_in_cycle_by_cycle(self, cycle_in_chapter_id: int, page: int, limit: int) -> list[SubjectsInCycle]:
        if page == 0:
            query = select(SubjectsInCycle).where(SubjectsInCycle.cycle_in_chapter_id == cycle_in_chapter_id).order_by(SubjectsInCycle.id.asc())
        else:
            query = select(SubjectsInCycle).where(SubjectsInCycle.cycle_in_chapter_id == cycle_in_chapter_id).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        subjects_in_cycles = list(result.scalars().all())
        return subjects_in_cycles

    @log_exceptions
    async def get_subjects_in_cycle_by_module(self, module_in_cycle_id: int, page: int, limit: int) -> list[SubjectsInCycle]:
        if page == 0:
            query = select(SubjectsInCycle).where(SubjectsInCycle.module_in_cycle_id == module_in_cycle_id).order_by(SubjectsInCycle.id.asc())
        else:
            query = select(SubjectsInCycle).where(SubjectsInCycle.module_in_cycle_id == module_in_cycle_id).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        subjects_in_cycles = list(result.scalars().all())
        return subjects_in_cycles

    @log_exceptions
    async def update_subject_in_cycle(self, target_id: int, **kwargs) -> SubjectsInCycle | None:
        query = update(SubjectsInCycle).where(SubjectsInCycle.id == target_id).values(**kwargs).returning(SubjectsInCycle)
        res = await self.db_session.execute(query)
        updated_subject_in_cycle = res.scalar_one_or_none()
        return updated_subject_in_cycle
    

'''
================
DAL for SubjectsInCycleHours
================
'''
class SubjectsInCycleHoursDAL:
    """Data Access Layer for operating subjects in cycle hours info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_subject_in_cycle_hours(
        self,
        semester: int,
        self_study_hours: int,
        lectures_hours: int,
        laboratory_hours: int,
        practical_hours: int,
        course_project_hours: int,
        consultation_hours: int,
        intermediate_assessment_hours: int,
        subject_in_cycle_id: int
    ) -> SubjectsInCycleHours:
        new_subject_in_cycle_hours = SubjectsInCycleHours(
            semester=semester,
            self_study_hours=self_study_hours,
            lectures_hours=lectures_hours,
            laboratory_hours=laboratory_hours,
            practical_hours=practical_hours,
            course_project_hours=course_project_hours,
            consultation_hours=consultation_hours,
            intermediate_assessment_hours=intermediate_assessment_hours,
            subject_in_cycle_id=subject_in_cycle_id
        )
        self.db_session.add(new_subject_in_cycle_hours)
        await self.db_session.flush()
        return new_subject_in_cycle_hours

    @log_exceptions
    async def delete_subject_in_cycle_hours(self, id: int) -> SubjectsInCycleHours | None:
        query = delete(SubjectsInCycleHours).where(SubjectsInCycleHours.id == id).returning(SubjectsInCycleHours)
        res = await self.db_session.execute(query)
        deleted_subject_in_cycle_hours = res.scalar_one_or_none()
        return deleted_subject_in_cycle_hours

    @log_exceptions
    async def get_all_subjects_in_cycle_hours(self, page: int, limit: int) -> list[SubjectsInCycleHours]:
        if page == 0:
            query = select(SubjectsInCycleHours).order_by(SubjectsInCycleHours.id.asc())
        else:
            query = select(SubjectsInCycleHours).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        subjects_in_cycle_hours = list(result.scalars().all())
        return subjects_in_cycle_hours

    @log_exceptions
    async def get_subject_in_cycle_hours_by_id(self, id: int) -> SubjectsInCycleHours | None:
        query = select(SubjectsInCycleHours).where(SubjectsInCycleHours.id == id)
        res = await self.db_session.execute(query)
        subject_in_cycle_hours_row = res.scalar_one_or_none()
        return subject_in_cycle_hours_row

    @log_exceptions
    async def get_subjects_in_cycle_hours_by_subject_in_cycle(self, subject_in_cycle_id: int, page: int, limit: int) -> list[SubjectsInCycleHours]:
        if page == 0:
            query = select(SubjectsInCycleHours).where(SubjectsInCycleHours.subject_in_cycle_id == subject_in_cycle_id).order_by(SubjectsInCycleHours.semester.asc(), SubjectsInCycleHours.id.asc())
        else:
            query = select(SubjectsInCycleHours).where(SubjectsInCycleHours.subject_in_cycle_id == subject_in_cycle_id).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        subjects_in_cycle_hours = list(result.scalars().all())
        return subjects_in_cycle_hours if subjects_in_cycle_hours is not None else []
    
    @log_exceptions
    async def get_subjects_in_cycle_hours_by_subject_and_semester(self, subject_in_cycle_id: int, semester: int) -> list[SubjectsInCycleHours]:
        query = select(SubjectsInCycleHours).where(
            (SubjectsInCycleHours.subject_in_cycle_id == subject_in_cycle_id) &
            (SubjectsInCycleHours.semester == semester)
        ).order_by(SubjectsInCycleHours.id.asc())
        result = await self.db_session.execute(query)
        subjects_in_cycle_hours = list(result.scalars().all())
        return subjects_in_cycle_hours if subjects_in_cycle_hours is not None else []

    @log_exceptions
    async def get_subjects_in_cycle_hours_by_semester(self, semester: int, page: int, limit: int) -> list[SubjectsInCycleHours]:
        if page == 0:
            query = select(SubjectsInCycleHours).where(SubjectsInCycleHours.semester == semester).order_by(SubjectsInCycleHours.id.asc())
        else:
            query = select(SubjectsInCycleHours).where(SubjectsInCycleHours.semester == semester).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        subjects_in_cycle_hours = list(result.scalars().all())
        return subjects_in_cycle_hours

    @log_exceptions
    async def update_subject_in_cycle_hours(self, target_id: int, **kwargs) -> SubjectsInCycleHours | None:
        query = update(SubjectsInCycleHours).where(SubjectsInCycleHours.id == target_id).values(**kwargs).returning(SubjectsInCycleHours)
        res = await self.db_session.execute(query)
        updated_subject_in_cycle_hours = res.scalar_one_or_none()
        return updated_subject_in_cycle_hours


'''
================
DAL for Certification
================
'''
class CertificationDAL:
    """Data Access Layer for operating certification info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_certification(
        self,
        id: int,
        credit: bool = False,
        differentiated_credit: bool = False,
        course_project: bool = False,
        course_work: bool = False,
        control_work: bool = False,
        other_form: bool = False
    ) -> Certification:
        new_certification = Certification(
            id=id,
            credit=credit,
            differentiated_credit=differentiated_credit,
            course_project=course_project,
            course_work=course_work,
            control_work=control_work,
            other_form=other_form
        )
        self.db_session.add(new_certification)
        await self.db_session.flush()
        return new_certification

    @log_exceptions
    async def delete_certification(self, id: int) -> Certification | None:
        query = delete(Certification).where(Certification.id == id).returning(Certification)
        res = await self.db_session.execute(query)
        deleted_certification = res.scalar_one_or_none()
        return deleted_certification

    @log_exceptions
    async def get_all_certifications(self, page: int, limit: int) -> list[Certification]:
        if page == 0:
            query = select(Certification).order_by(Certification.id.asc())
        else:
            query = select(Certification).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        certifications = list(result.scalars().all())
        return certifications

    @log_exceptions
    async def get_certification_by_id(self, id: int) -> Certification | None:
        query = select(Certification).where(Certification.id == id)
        res = await self.db_session.execute(query)
        certification_row = res.scalar_one_or_none()
        return certification_row

    @log_exceptions
    async def update_certification(self, target_id: int, **kwargs) -> Certification | None:
        query = update(Certification).where(Certification.id == target_id).values(**kwargs).returning(Certification)
        res = await self.db_session.execute(query)
        updated_certification = res.scalar_one_or_none()
        return updated_certification


'''
================
DAL for TeacherInPlan
================
'''
class TeacherInPlanDAL:
    """Data Access Layer for operating teacher in plan info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_teacher_in_plan(self, subject_in_cycle_hours_id: int, teacher_id: int, group_name: str, session_type: str) -> TeacherInPlan:
        new_teacher_in_plan = TeacherInPlan(
            subject_in_cycle_hours_id=subject_in_cycle_hours_id,
            teacher_id=teacher_id,
            group_name=group_name,
            session_type=session_type
        )
        self.db_session.add(new_teacher_in_plan)
        await self.db_session.flush()
        return new_teacher_in_plan

    @log_exceptions
    async def delete_teacher_in_plan(self, id: int) -> TeacherInPlan | None:
        query = delete(TeacherInPlan).where(TeacherInPlan.id == id).returning(TeacherInPlan)
        res = await self.db_session.execute(query)
        deleted_teacher_in_plan = res.scalar_one_or_none()
        return deleted_teacher_in_plan

    @log_exceptions
    async def get_all_teachers_in_plans(self, page: int, limit: int) -> list[TeacherInPlan]:
        if page == 0:
            query = select(TeacherInPlan).order_by(TeacherInPlan.id.asc())
        else:
            query = select(TeacherInPlan).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        teachers_in_plans = list(result.scalars().all())
        return teachers_in_plans

    @log_exceptions
    async def get_teacher_in_plan_by_id(self, id: int) -> TeacherInPlan | None:
        query = select(TeacherInPlan).where(TeacherInPlan.id == id)
        res = await self.db_session.execute(query)
        teacher_in_plan_row = res.scalar_one_or_none()
        return teacher_in_plan_row

    @log_exceptions
    async def get_teachers_in_plans_by_teacher(self, teacher_id: int, page: int, limit: int) -> list[TeacherInPlan]:
        if page == 0:
            query = select(TeacherInPlan).where(TeacherInPlan.teacher_id == teacher_id).order_by(TeacherInPlan.id.asc())
        else:
            query = select(TeacherInPlan).where(TeacherInPlan.teacher_id == teacher_id).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        teachers_in_plans = list(result.scalars().all())
        return teachers_in_plans if teachers_in_plans is not None else []

    @log_exceptions
    async def get_teachers_in_plans_by_group(self, group_name: str, page: int, limit: int) -> list[TeacherInPlan]:
        if page == 0:
            query = select(TeacherInPlan).where(TeacherInPlan.group_name == group_name).order_by(TeacherInPlan.id.asc())
        else:
            query = select(TeacherInPlan).where(TeacherInPlan.group_name == group_name).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        teachers_in_plans = list(result.scalars().all())
        return teachers_in_plans if teachers_in_plans is not None else []

    @log_exceptions
    async def get_teachers_in_plans_by_subject_hours(self, subject_in_cycle_hours_id: int, page: int, limit: int) -> list[TeacherInPlan]:
        if page == 0:
            query = select(TeacherInPlan).where(TeacherInPlan.subject_in_cycle_hours_id == subject_in_cycle_hours_id).order_by(TeacherInPlan.id.asc())
        else:
            query = select(TeacherInPlan).where(TeacherInPlan.subject_in_cycle_hours_id == subject_in_cycle_hours_id).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        teachers_in_plans = list(result.scalars().all())
        return teachers_in_plans if teachers_in_plans is not None else []

    @log_exceptions
    async def get_teachers_in_plans_by_session_type(self, session_type: str, page: int, limit: int) -> list[TeacherInPlan]:
        if page == 0:
            query = select(TeacherInPlan).where(TeacherInPlan.session_type == session_type).order_by(TeacherInPlan.id.asc())
        else:
            query = select(TeacherInPlan).where(TeacherInPlan.session_type == session_type).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        teachers_in_plans = list(result.scalars().all())
        return teachers_in_plans if teachers_in_plans is not None else []

    @log_exceptions
    async def update_teacher_in_plan(self, target_id: int, **kwargs) -> TeacherInPlan | None:
        query = update(TeacherInPlan).where(TeacherInPlan.id == target_id).values(**kwargs).returning(TeacherInPlan)
        res = await self.db_session.execute(query)
        updated_teacher_in_plan = res.scalar_one_or_none()
        return updated_teacher_in_plan