from api.models import TunedModel
from typing import List


class ShowTeacherInPlan(TunedModel):
    """Class for get teacher in plan info"""
    id: int
    subject_in_cycle_hours_id: int
    teacher_id: int
    group_name: str
    session_type: str


class CreateTeacherInPlan(TunedModel):
    subject_in_cycle_hours_id: int
    teacher_id: int
    group_name: str
    session_type: str


class UpdateTeacherInPlan(TunedModel):
    teacher_in_plan_id: int
    subject_in_cycle_hours_id: int | None = None
    teacher_id: int | None = None
    group_name: str | None = None
    session_type: str | None = None


class ShowTeacherInPlanWithHATEOAS(TunedModel):
    teacher_in_plan: ShowTeacherInPlan
    links: dict[str, str] = {}


class ShowTeacherInPlanListWithHATEOAS(TunedModel):
    teachers_in_plans: List[ShowTeacherInPlanWithHATEOAS]
    links: dict[str, str] = {}
