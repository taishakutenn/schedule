from api.models import TunedModel
from typing import List


class ShowSessionType(TunedModel):
    """Class for get session type info"""
    name: str


class CreateSessionType(TunedModel):
    name: str


class UpdateSessionType(TunedModel):
    current_name: str
    new_name: str


class ShowSessionTypeWithHATEOAS(TunedModel):
    session_type: ShowSessionType
    links: dict[str, str] = {}


class ShowSessionTypeListWithHATEOAS(TunedModel):
    session_types: List[ShowSessionTypeWithHATEOAS]
    links: dict[str, str] = {}
