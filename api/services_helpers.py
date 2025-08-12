from fastapi import HTTPException

from db.dals import BuildingDAL, CabinetDAL, TeacherDAL, SpecialityDAL, GroupDAL, SubjectDAL, CurriculumDAL, EmployTeacherDAL, TeacherRequestDAL, SessionDAL
from config.logging_config import configure_logging

from sqlalchemy import Date

logger = configure_logging()


'''
=====
Exits
=====
'''

# Building
async def ensure_building_exists(building_dal: BuildingDAL, building_number: int):
    building = await building_dal.get_building_by_number(building_number)
    return building

# Cabinet
async def ensure_cabinet_exists(cabinet_dal: CabinetDAL, cabinet_number: int, building_number: int):
    cabinet = await cabinet_dal.get_cabinet_by_number_and_building(cabinet_number, building_number)
    return cabinet

# Teacher
async def ensure_teacher_exists(teacher_dal: TeacherDAL, teacher_id: int):
    teacher = await teacher_dal.get_teacher_by_id(teacher_id)
    return teacher

# Speciality
async def ensure_speciality_exists(speciality_dal: SpecialityDAL, speciality_code: str):
    speciality = await speciality_dal.get_speciality(speciality_code)
    return speciality

# Group
async def ensure_group_exists(group_dal: GroupDAL, group_name: str):
    group = await group_dal.get_group(group_name)
    return group

# Subject
async def ensure_subject_exists(subject_dal: SubjectDAL, subject_code: str):
    subject = await subject_dal.get_subject(subject_code)
    return subject


'''
======
Unique
======
'''

# Group
async def ensure_group_unique(group_dal: GroupDAL, group_name: str):
    group = await group_dal.get_group(group_name)
    return group is None
    
# Cabinet
async def ensure_cabinet_unique(cabinet_dal: CabinetDAL, building_number: int, cabinet_number: int):
    cabinet = await cabinet_dal.get_cabinet_by_number_and_building(building_number, cabinet_number)
    return cabinet is None

# Curriculum
async def ensure_curriculum_unique(curriculum_dal: CurriculumDAL,
                                   semester_number: int, group_name: str, subject_code: str):
    curriculum = await curriculum_dal.get_curriculum(semester_number, group_name, subject_code)
    return curriculum is None

# Subject
async def ensure_subject_unique(subject_dal: SubjectDAL, subject_code: str):
    subject = await subject_dal.get_subject(subject_code)
    return subject is None

# Employment
async def ensure_employment_unique(employment_dal: EmployTeacherDAL, 
                                   date_start_period: Date, date_end_period: Date, teacher_id: int):
    employment = await employment_dal.get_employTeacher(date_start_period, date_end_period, teacher_id)
    return employment is None

# TeacherRequest
async def ensure_request_unique(request_dal: TeacherRequestDAL, date_request: Date, teacher_id: int,
                                subject_code: str, group_name: str):
    request = await request_dal.get_teacherRequest(date_request, teacher_id, subject_code, group_name)
    return request is None

# Session
async def ensure_session_unique(session_dal: SessionDAL, session_number: int, date: Date, group_name: str):
    session = await session_dal.get_session(session_number, date, group_name)
    return session is None