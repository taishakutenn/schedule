from fastapi import HTTPException

from db.dals import BuildingDAL, CabinetDAL, TeacherDAL, SpecialityDAL, GroupDAL, SessionDAL
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
async def ensure_cabinet_exists(cabinet_dal, building_number: int, cabinet_number: int) -> bool:
    cabinet = await cabinet_dal.get_cabinet_by_number_and_building(building_number, cabinet_number)
    return cabinet is not None

# Teacher
async def ensure_teacher_exists(teacher_dal: TeacherDAL, teacher_id: int):
    teacher = await teacher_dal.get_teacher_by_id(teacher_id)
    return teacher

# Speciality
async def ensure_speciality_exists(speciality_dal, speciality_code: str) -> bool:
    speciality = await speciality_dal.get_speciality(speciality_code)
    return speciality is not None

# Group
async def ensure_group_exists(group_dal: GroupDAL, group_name: str):
    group = await group_dal.get_group(group_name)
    return group

async def ensure_plan_exists(plan_dal, plan_id: int) -> bool:
    plan = await plan_dal.get_plan_by_id(plan_id)
    return plan is not None

# # Subject
# async def ensure_subject_exists(subject_dal: SubjectDAL, subject_code: str):
#     subject = await subject_dal.get_subject(subject_code)
#     return subject

async def ensure_category_exists(category_dal, category_name: str) -> bool:
    category = await category_dal.get_teacher_category(category_name)
    return category is not None

async def ensure_teacher_exists(teacher_dal, teacher_id: int) -> bool:
    teacher = await teacher_dal.get_teacher_by_id(teacher_id)
    return teacher is not None

async def ensure_session_type_exists(session_type_dal, name: str) -> bool:
    session_type = await session_type_dal.get_session_type(name)
    return session_type is not None

async def ensure_semester_exists(semester_dal, semester: int, plan_id: int) -> bool:
    semester_obj = await semester_dal.get_semester_by_semester_and_plan(semester, plan_id)
    return semester_obj is not None

async def ensure_chapter_exists(chapter_dal, chapter_id: int) -> bool:
    chapter = await chapter_dal.get_chapter_by_id(chapter_id)
    return chapter is not None

async def ensure_cycle_exists(cycle_dal, cycle_id: int) -> bool:
    cycle = await cycle_dal.get_cycle_by_id(cycle_id)
    return cycle is not None

async def ensure_module_exists(module_dal, module_id: int) -> bool:
    module = await module_dal.get_module_by_id(module_id)
    return module is not None

async def ensure_subject_in_cycle_exists(subject_in_cycle_dal, subject_in_cycle_id: int) -> bool:
    subject_in_cycle = await subject_in_cycle_dal.get_subject_in_cycle_by_id(subject_in_cycle_id)
    return subject_in_cycle is not None

async def ensure_subject_in_cycle_hours_exists(subject_in_cycle_hours_dal, hours_id: int) -> bool:
    subject_in_cycle_hours = await subject_in_cycle_hours_dal.get_subject_in_cycle_hours_by_id(hours_id)
    return subject_in_cycle_hours is not None

async def ensure_certification_exists(certification_dal, certification_id: int) -> bool:
    certification = await certification_dal.get_certification_by_id(certification_id)
    return certification is not None


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
async def ensure_cabinet_unique(cabinet_dal, building_number: int, cabinet_number: int) -> bool:
    cabinet = await cabinet_dal.get_cabinet_by_number_and_building(building_number, cabinet_number)
    return cabinet is None

# # Curriculum
# async def ensure_curriculum_unique(curriculum_dal: CurriculumDAL,
#                                    semester_number: int, group_name: str, subject_code: str):
#     curriculum = await curriculum_dal.get_curriculum(semester_number, group_name, subject_code)
#     return curriculum is None

# # Subject
# async def ensure_subject_unique(subject_dal: SubjectDAL, subject_code: str):
#     subject = await subject_dal.get_subject(subject_code)
#     return subject is None

# # Employment
# async def ensure_employment_unique(employment_dal: EmployTeacherDAL, 
#                                    date_start_period: Date, date_end_period: Date, teacher_id: int):
#     employment = await employment_dal.get_employTeacher(date_start_period, date_end_period, teacher_id)
#     return employment is None

# # TeacherRequest
# async def ensure_request_unique(request_dal: TeacherRequestDAL, date_request: Date, teacher_id: int,
#                                 subject_code: str, group_name: str):
#     request = await request_dal.get_teacherRequest(date_request, teacher_id, subject_code, group_name)
#     return request is None

# Session
async def ensure_session_unique(session_dal: SessionDAL, session_number: int, date: Date, group_name: str):
    session = await session_dal.get_session(session_number, date, group_name)
    return session is None

# async def ensure_teacher_group_relation_unique(
#     teacher_group_dal: TeachersGroupsDAL, teacher_id: int, group_name: str):
#         existing_relation = await teacher_group_dal.get_teachers_groups_relation(teacher_id, group_name)
#         return existing_relation is None

# async def ensure_teacher_subject_relation_unique(
#     teacher_subject_dal: TeachersSubjectsDAL, teacher_id: int, subject_code: str):
#         existing_relation = await teacher_subject_dal.get_teachers_subjects_relation(teacher_id, subject_code)
#         return existing_relation is None

async def ensure_category_unique(category_dal, category_name: str) -> bool:
    category = await category_dal.get_teacher_category(category_name)
    return category is None

async def ensure_teacher_phone_unique(teacher_dal, phone_number: str, exclude_id: int = None) -> bool:
    teacher = await teacher_dal.get_teacher_by_phone_number(phone_number)
    return teacher is None or teacher.id == exclude_id

async def ensure_teacher_email_unique(teacher_dal, email: str, exclude_id: int = None) -> bool:
    teacher = await teacher_dal.get_teacher_by_email(email)
    return teacher is None or teacher.id == exclude_id

async def ensure_building_unique(building_dal, building_number: int) -> bool:
    building = await building_dal.get_building_by_number(building_number)
    return building is None

async def ensure_session_type_unique(session_type_dal, name: str) -> bool:
    session_type = await session_type_dal.get_session_type(name)
    return session_type is None

async def ensure_semester_unique(semester_dal, semester: int, plan_id: int) -> bool:
    semester_obj = await semester_dal.get_semester_by_semester_and_plan(semester, plan_id)
    return semester_obj is None

async def ensure_plan_unique(plan_dal, plan_id: int) -> bool:
    plan = await plan_dal.get_plan_by_id(plan_id)
    return plan is None

async def ensure_speciality_unique(speciality_dal, speciality_code: str) -> bool:
    speciality = await speciality_dal.get_speciality(speciality_code)
    return speciality is None

async def ensure_chapter_unique(chapter_dal, chapter_id: int) -> bool:
    chapter = await chapter_dal.get_chapter_by_id(chapter_id)
    return chapter is None

async def ensure_cycle_unique(cycle_dal, cycle_id: int) -> bool:
    cycle = await cycle_dal.get_cycle_by_id(cycle_id)
    return cycle is None

async def ensure_module_unique(module_dal, module_id: int) -> bool:
    module = await module_dal.get_module_by_id(module_id)
    return module is None

async def ensure_subject_in_cycle_unique(subject_in_cycle_dal, subject_in_cycle_id: int) -> bool:
    subject_in_cycle = await subject_in_cycle_dal.get_subject_in_cycle_by_id(subject_in_cycle_id)
    return subject_in_cycle is None

async def ensure_subject_in_cycle_hours_unique(subject_in_cycle_hours_dal, hours_id: int) -> bool:
    subject_in_cycle_hours = await subject_in_cycle_hours_dal.get_subject_in_cycle_hours_by_id(hours_id)
    return subject_in_cycle_hours is None

async def ensure_certification_unique(certification_dal, certification_id: int) -> bool:
    certification = await certification_dal.get_certification_by_id(certification_id)
    return certification is None


'''
Other
'''

async def ensure_cycle_contains_modules(cycle_dal, cycle_id: int) -> bool:
    """Проверяет, разрешено ли циклу содержать модули (contains_modules = True)."""
    cycle = await cycle_dal.get_cycle_by_id(cycle_id)
    return cycle.contains_modules if cycle else False