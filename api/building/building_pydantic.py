from api.models import TunedModel
from typing import List


class ShowBuilding(TunedModel):
    """Class for get building info"""
    building_number: int
    city: str
    building_address: str


class CreateBuilding(TunedModel):
    building_number: int
    city: str = "Орск"
    building_address: str


class UpdateBuilding(TunedModel):
    building_number: int
    new_building_number: int | None = None
    city: str | None = None
    building_address: str | None = None


class ShowBuildingWithHATEOAS(TunedModel):
    building: ShowBuilding
    links: dict[str, str] = {}


class ShowBuildingListWithHATEOAS(TunedModel):
    buildings: List[ShowBuildingWithHATEOAS]
    links: dict[str, str] = {}
