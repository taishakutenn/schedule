from fastapi import HTTPException

from db.dals import BuildingDAL, CabinetDAL, TeacherDAL, SpecialityDAL, GroupDAL
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
