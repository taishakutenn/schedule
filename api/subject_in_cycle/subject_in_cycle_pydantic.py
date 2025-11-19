from api.models import TunedModel
from typing import List


class ShowSubjectsInCycle(TunedModel):
    """Class for get subject in cycle info"""
    id: int
    code: str
    title: str
    module_in_cycle_id: int | None = None
    cycle_in_chapter_id: int | None = None


class CreateSubjectsInCycle(TunedModel):
    code: str
    title: str
    module_in_cycle_id: int | None = None
    cycle_in_chapter_id: int | None = None


class UpdateSubjectsInCycle(TunedModel):
    subject_in_cycle_id: int
    code: str | None = None
    title: str | None = None
    module_in_cycle_id: int | None = None
    cycle_in_chapter_id: int | None = None


class ShowSubjectsInCycleWithHATEOAS(TunedModel):
    subject_in_cycle: ShowSubjectsInCycle
    links: dict[str, str] = {}


class ShowSubjectsInCycleListWithHATEOAS(TunedModel):
    subjects_in_cycles: List[ShowSubjectsInCycleWithHATEOAS]
    links: dict[str, str] = {}
    