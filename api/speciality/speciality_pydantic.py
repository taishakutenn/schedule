from api.models import TunedModel
from typing import List


class ShowSpeciality(TunedModel):
    """Class for get speciality info"""
    speciality_code: str


class CreateSpeciality(TunedModel):
    speciality_code: str


class UpdateSpeciality(TunedModel):
    speciality_code: str
    new_speciality_code: str | None = None


class ShowSpecialityWithHATEOAS(TunedModel):
    speciality: ShowSpeciality
    links: dict[str, str] = {}


class ShowSpecialityListWithHATEOAS(TunedModel):
    specialities: List[ShowSpecialityWithHATEOAS]
    links: dict[str, str] = {}
