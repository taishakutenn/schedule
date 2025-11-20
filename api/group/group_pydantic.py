from api.models import TunedModel
from typing import List


class ShowGroup(TunedModel):
    """Class for get group info"""
    group_name: str
    speciality_code: str | None = None
    payment_form: str | None = None
    quantity_students: int | None = None
    group_advisor_id: int | None = None


class CreateGroup(TunedModel):
    group_name: str
    payment_form: str | None = None
    speciality_code: str | None = None
    quantity_students: int | None = None
    group_advisor_id: int | None = None


class UpdateGroup(TunedModel):
    group_name: str
    payment_form: str | None = None
    new_group_name: str | None = None
    speciality_code: str | None = None
    quantity_students: int | None = None
    group_advisor_id: int | None = None


class ShowGroupWithHATEOAS(TunedModel):
    group: ShowGroup
    links: dict[str, str] = {}


class ShowGroupListWithHATEOAS(TunedModel):
    groups: List[ShowGroupWithHATEOAS]
    links: dict[str, str] = {}
