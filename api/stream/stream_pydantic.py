from api.models import TunedModel
from typing import List


class ShowStream(TunedModel):
    """Class for get stream info"""
    stream_id: int
    group_name: str
    subject_id: int


class CreateStream(TunedModel):
    stream_id: int
    group_name: str
    subject_id: int


class UpdateStream(TunedModel):
    stream_id: int
    group_name: str
    subject_id: int
    new_stream_id: int | None = None
    new_group_name: str | None = None
    new_subject_id: int | None = None


class ShowStreamWithHATEOAS(TunedModel):
    stream: ShowStream
    links: dict[str, str] = {}


class ShowStreamListWithHATEOAS(TunedModel):
    streams: List[ShowStreamWithHATEOAS]
    links: dict[str, str] = {}
    