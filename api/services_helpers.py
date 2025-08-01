from fastapi import HTTPException

from db.dals import BuildingDAL, CabinetDAL, TeacherDAL, SpecialityDAL, GroupDAL, SubjectDAL, CurriculumDAL
from config.logging_config import configure_logging

logger = configure_logging()


'''
====================
Helpers for cabinets
====================
'''


async def ensure_building_exists(building_dal: BuildingDAL, building_number: int):
    building = await building_dal.get_building_by_number(building_number)
    return building


async def ensure_cabinet_unique(cabinet_dal: CabinetDAL, building_number: int, cabinet_number: int):
    cabinet = await cabinet_dal.get_cabinet_by_number_and_building(building_number, cabinet_number)
    return cabinet is None


'''
==================
Helpers for groups
==================
'''


async def ensure_teacher_exists(teacher_dal: TeacherDAL, teacher_id: int):
    teacher = await teacher_dal.get_teacher_by_id(teacher_id)
    return teacher


async def ensure_speciality_exists(speciality_dal: SpecialityDAL, specilaity_code: str):
    speciality = await speciality_dal.get_speciality(specilaity_code)
    return speciality


async def ensure_group_unique(group_dal: GroupDAL, group_name: str):
    group = await group_dal.get_group(group_name)
    return group is None


'''
======================
Helpers for curriculum
======================
'''


async def ensure_group_exists(group_dal: GroupDAL, group_name: str):
    group = await group_dal.get_group(group_name)
    return group


async def ensure_subject_exists(subject_dal: SubjectDAL, subject_code: str):
    subject = await subject_dal.get_subject(subject_code)
    return subject


async def ensure_curriculum_unique(curriculum_dal: CurriculumDAL,
                                   semester_number: int, group_name: str, subject_code: str):
    curriculum = await curriculum_dal.get_curriculum(semester_number, group_name, subject_code)
    return curriculum is None


'''
===================
Helpers for subject
===================
'''


async def ensure_subject_unique(subject_dal: SubjectDAL, subject_code: str):
    subject = await subject_dal.get_subject(subject_code)
    return subject is None