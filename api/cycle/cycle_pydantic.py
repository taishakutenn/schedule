from api.models import TunedModel
from typing import List


class ShowCycle(TunedModel):
    """Class for get cycle info"""
    id: int
    contains_modules: bool
    code: str
    name: str
    chapter_in_plan_id: int


class CreateCycle(TunedModel):
    contains_modules: bool
    code: str
    name: str
    chapter_in_plan_id: int


class UpdateCycle(TunedModel):
    cycle_id: int
    contains_modules: bool | None = None
    code: str | None = None
    name: str | None = None
    chapter_in_plan_id: int | None = None


class ShowCycleWithHATEOAS(TunedModel):
    cycle: ShowCycle
    links: dict[str, str] = {}


class ShowCycleListWithHATEOAS(TunedModel):
    cycles: List[ShowCycleWithHATEOAS]
    links: dict[str, str] = {}
    