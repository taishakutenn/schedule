from pydantic import EmailStr
from api.models import TunedModel
from typing import Optional, List


class ShowTeacher(TunedModel):
    """Class for get teacher info"""
    id: int
    surname: str
    name: str
    fathername: str | None = None
    phone_number: str
    email: EmailStr | None = None
    teacher_category: str | None = None


class CreateTeacher(TunedModel):
    surname: str
    name: str
    fathername: str | None = None
    phone_number: str
    email: EmailStr | None = None
    teacher_category: str | None = None


class UpdateTeacher(TunedModel):
    teacher_id: int
    surname: str
    name: str | None = None
    fathername: str | None = None
    phone_number: str | None = None
    email: EmailStr | None = None
    teacher_category: str | None = None


class ShowTeacherWithHATEOAS(TunedModel):
    teacher: ShowTeacher
    links: dict[str, str] = {}


class ShowTeacherListWithHATEOAS(TunedModel):
    teachers: List[ShowTeacherWithHATEOAS]
    links: dict[str, str] = {}
