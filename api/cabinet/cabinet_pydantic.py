from api.models import TunedModel
from typing import List


class ShowCabinet(TunedModel):
    """Class for get cabinet info"""
    cabinet_number: int
    building_number: int
    capacity: int | None = None
    cabinet_state: str | None = None


class CreateCabinet(TunedModel):
    cabinet_number: int
    building_number: int
    capacity: int | None = None
    cabinet_state: str | None = None


class UpdateCabinet(TunedModel):
    cabinet_number: int
    building_number: int
    new_cabinet_number: int | None = None
    new_building_number: int | None = None
    capacity: int | None = None
    cabinet_state: str | None = None


class ShowCabinetWithHATEOAS(TunedModel):
    cabinet: ShowCabinet
    links: dict[str, str] = {}


class ShowCabinetListWithHATEOAS(TunedModel):
    cabinets: List[ShowCabinetWithHATEOAS]
    links: dict[str, str] = {}
