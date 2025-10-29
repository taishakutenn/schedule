from api.models import TunedModel
from typing import Optional, List


class CreateTeacherCategory(TunedModel):
    teacher_category: str


class UpdateTeacherCategory(TunedModel):
    teacher_category: Optional[str] = None
    new_teacher_category: Optional[str] = None


class ShowTeacherCategory(TunedModel):
    teacher_category: str


class ShowTeacherCategoryWithHATEOAS(TunedModel):
    category: ShowTeacherCategory
    links: dict[str, str]


class ShowTeacherCategoryListWithHATEOAS(TunedModel):
    categories: List[ShowTeacherCategoryWithHATEOAS]
    links: dict[str, str]
