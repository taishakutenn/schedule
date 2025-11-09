from api.models import TunedModel
from typing import List


class ShowCertification(TunedModel):
    """Class for get certification info"""
    id: int
    credit: bool
    differentiated_credit: bool
    course_project: bool
    course_work: bool
    control_work: bool
    other_form: bool


class CreateCertification(TunedModel):
    id: int
    credit: bool = False
    differentiated_credit: bool = False
    course_project: bool = False
    course_work: bool = False
    control_work: bool = False
    other_form: bool = False


class UpdateCertification(TunedModel):
    certification_id: int
    credit: bool | None = None
    differentiated_credit: bool | None = None
    course_project: bool | None = None
    course_work: bool | None = None
    control_work: bool | None = None
    other_form: bool | None = None


class ShowCertificationWithHATEOAS(TunedModel):
    certification: ShowCertification
    links: dict[str, str] = {}


class ShowCertificationListWithHATEOAS(TunedModel):
    certifications: List[ShowCertificationWithHATEOAS]
    links: dict[str, str] = {}
    