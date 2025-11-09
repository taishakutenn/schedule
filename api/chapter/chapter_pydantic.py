from api.models import TunedModel
from typing import List


class ShowChapter(TunedModel):
    """Class for get chapter info"""
    id: int
    code: str
    name: str
    plan_id: int


class CreateChapter(TunedModel):
    code: str
    name: str
    plan_id: int


class UpdateChapter(TunedModel):
    chapter_id: int
    code: str | None = None
    name: str | None = None
    plan_id: int | None = None


class ShowChapterWithHATEOAS(TunedModel):
    chapter: ShowChapter
    links: dict[str, str] = {}


class ShowChapterListWithHATEOAS(TunedModel):
    chapters: List[ShowChapterWithHATEOAS]
    links: dict[str, str] = {}
    