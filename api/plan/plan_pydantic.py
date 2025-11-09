from api.models import TunedModel
from typing import List


class ShowPlan(TunedModel):
    """Class for get plan info"""
    id: int
    year: int
    speciality_code: str


class CreatePlan(TunedModel):
    year: int
    speciality_code: str


class UpdatePlan(TunedModel):
    plan_id: int
    year: int | None = None
    speciality_code: str | None = None


class ShowPlanWithHATEOAS(TunedModel):
    plan: ShowPlan
    links: dict[str, str] = {}


class ShowPlanListWithHATEOAS(TunedModel):
    plans: List[ShowPlanWithHATEOAS]
    links: dict[str, str] = {}
    