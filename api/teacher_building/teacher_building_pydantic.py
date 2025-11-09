from api.models import TunedModel
from typing import List


class ShowTeacherBuilding(TunedModel):
    """Class for get teacher-building relation info"""
    id: int
    teacher_id: int
    building_number: int


class CreateTeacherBuilding(TunedModel):
    teacher_id: int
    building_number: int


class UpdateTeacherBuilding(TunedModel):
    teacher_building_id: int
    teacher_id: int | None = None
    building_number: int | None = None


class ShowTeacherBuildingWithHATEOAS(TunedModel):
    teacher_building: ShowTeacherBuilding
    links: dict[str, str] = {}


class ShowTeacherBuildingListWithHATEOAS(TunedModel):
    teacher_buildings: List[ShowTeacherBuildingWithHATEOAS]
    links: dict[str, str] = {}
    