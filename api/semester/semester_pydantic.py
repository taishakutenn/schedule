from api.models import TunedModel
from typing import List


class ShowSemester(TunedModel):
    """Class for get semester info"""
    semester: int
    weeks: float
    practice_weeks: int
    plan_id: int


class CreateSemester(TunedModel):
    semester: int
    weeks: float
    practice_weeks: int
    plan_id: int


class UpdateSemester(TunedModel):
    semester: int
    plan_id: int
    new_semester: int | None = None
    new_plan_id: int | None = None
    weeks: float | None = None
    practice_weeks: int | None = None


class ShowSemesterWithHATEOAS(TunedModel):
    semester: ShowSemester
    links: dict[str, str] = {}


class ShowSemesterListWithHATEOAS(TunedModel):
    semesters: List[ShowSemesterWithHATEOAS]
    links: dict[str, str] = {}
    