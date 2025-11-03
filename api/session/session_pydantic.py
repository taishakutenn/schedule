from datetime import date
from api.models import TunedModel
from typing import List


class ShowSession(TunedModel):
    """Class for get session info"""
    session_number: int
    session_date: date
    teacher_in_plan: int
    session_type: str
    cabinet_number: int | None = None
    building_number: int | None = None


class CreateSession(TunedModel):
    session_number: int
    session_date: date
    teacher_in_plan: int
    session_type: str
    cabinet_number: int | None = None
    building_number: int | None = None


class UpdateSession(TunedModel):
    session_number: int
    session_date: date
    teacher_in_plan: int
    new_session_number: int | None = None
    new_session_date: date | None = None
    new_teacher_in_plan: int | None = None
    new_session_type: str | None = None
    new_cabinet_number: int | None = None
    new_building_number: int | None = None


class ShowSessionWithHATEOAS(TunedModel):
    session: ShowSession
    links: dict[str, str] = {}


class ShowSessionListWithHATEOAS(TunedModel):
    sessions: List[ShowSessionWithHATEOAS]
    links: dict[str, str] = {}
