from api.models import TunedModel
from typing import List


class ShowSubjectsInCycleHours(TunedModel):
    """Class for get subject in cycle hours info"""
    id: int
    semester: int
    self_study_hours: int
    lectures_hours: int
    laboratory_hours: int
    practical_hours: int
    course_project_hours: int
    consultation_hours: int
    intermediate_assessment_hours: int
    subject_in_cycle_id: int


class CreateSubjectsInCycleHours(TunedModel):
    semester: int
    self_study_hours: int
    lectures_hours: int
    laboratory_hours: int
    practical_hours: int
    course_project_hours: int
    consultation_hours: int
    intermediate_assessment_hours: int
    subject_in_cycle_id: int


class UpdateSubjectsInCycleHours(TunedModel):
    hours_id: int
    semester: int | None = None
    self_study_hours: int | None = None
    lectures_hours: int | None = None
    laboratory_hours: int | None = None
    practical_hours: int | None = None
    course_project_hours: int | None = None
    consultation_hours: int | None = None
    intermediate_assessment_hours: int | None = None
    subject_in_cycle_id: int | None = None


class ShowSubjectsInCycleHoursWithHATEOAS(TunedModel):
    subject_in_cycle_hours: ShowSubjectsInCycleHours
    links: dict[str, str] = {}


class ShowSubjectsInCycleHoursListWithHATEOAS(TunedModel):
    subjects_in_cycle_hours: List[ShowSubjectsInCycleHoursWithHATEOAS]
    links: dict[str, str] = {}
    