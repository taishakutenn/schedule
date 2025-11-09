from api.models import TunedModel
from typing import List


class ShowModule(TunedModel):
    """Class for get module info"""
    id: int
    name: str
    code: str
    cycle_in_chapter_id: int


class CreateModule(TunedModel):
    name: str
    code: str
    cycle_in_chapter_id: int


class UpdateModule(TunedModel):
    module_id: int
    name: str | None = None
    code: str | None = None
    cycle_in_chapter_id: int | None = None


class ShowModuleWithHATEOAS(TunedModel):
    module: ShowModule
    links: dict[str, str] = {}


class ShowModuleListWithHATEOAS(TunedModel):
    modules: List[ShowModuleWithHATEOAS]
    links: dict[str, str] = {}
    