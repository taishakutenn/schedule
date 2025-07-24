from fastapi import HTTPException

from db.dals import BuildingDAL, CabinetDAL
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
