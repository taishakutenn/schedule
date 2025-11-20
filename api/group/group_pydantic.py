from api.models import TunedModel
from typing import List


class ShowGroup(TunedModel):
    """Class for get group info"""
    group_name: str
    speciality_code: str | None = None
    quantity_students: int | None = None
    group_advisor_id: int | None = None
    payment_form: str


class CreateGroup(TunedModel):
    group_name: str
    speciality_code: str | None = None
    quantity_students: int | None = None
    group_advisor_id: int | None = None
    payment_form: str


class UpdateGroup(TunedModel):
    group_name: str
    new_group_name: str | None = None
    speciality_code: str | None = None
    quantity_students: int | None = None
    group_advisor_id: int | None = None
    payment_form: str


class ShowGroupWithHATEOAS(TunedModel):
    group: ShowGroup
    links: dict[str, str] = {}


class ShowGroupListWithHATEOAS(TunedModel):
    groups: List[ShowGroupWithHATEOAS]
    links: dict[str, str] = {}
