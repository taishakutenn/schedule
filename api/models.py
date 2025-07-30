"""
File for creating validation models
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class TunedModel(BaseModel):
    class Config:
        """
        Tells pydantic to convert even non dict obj to json.
        We'll get fed up with this class
        """
        orm_mode = True
        from_attributes = True


class QueryParams(TunedModel):
    """
    This is model for validate query params
    when we need to retrieve all data from the table
     """
    page: int = Field(default=0, ge=0)
    limit: int = Field(default=10, ge=1, le=100)


'''
========
Teachers
========
'''


class ShowTeacher(TunedModel):
    """Class for get teacher info"""
    name: str
    surname: str
    phone_number: str
    email: EmailStr
    fathername: str | None = None


class CreateTeacher(TunedModel):
    name: str
    surname: str
    phone_number: str
    email: EmailStr
    fathername: str | None = None


class UpdateTeacher(TunedModel):
    teacher_id: int
    name: str | None = None
    surname: str | None = None
    phone_number: str | None = None
    email: EmailStr | None = None
    fathername: str | None = None


'''
=========
Buildings
=========
'''


class ShowBuilding(TunedModel):
    """Class for get building info"""
    building_number: int
    city: str
    building_address: str


class CreateBuilding(TunedModel):
    building_number: int
    city: str
    building_address: str


class UpdateBuilding(TunedModel):
    building_number: int
    new_building_number: int | None = None
    city: str | None = None
    building_address: str | None = None


'''
=======
Cabinet
=======
'''


class ShowCabinet(TunedModel):
    """Class for get cabinet info"""
    cabinet_number: int
    capacity: int | None = None
    cabinet_state: str | None = None
    building_number: int


class CreateCabinet(TunedModel):
    """Class for add new cabinet in db"""
    cabinet_number: int
    capacity: int | None = None
    cabinet_state: str | None = None
    building_number: int


class UpdateCabinet(TunedModel):
    cabinet_number: int
    new_cabinet_number: int | None = None
    capacity: int | None = None
    cabinet_state: str | None = None
    building_number: int
    new_building_number: int | None = None


'''
==========
Speciality
==========
'''


class ShowSpeciality(TunedModel):
    """Class for get speciality info"""
    speciality_code: str


class CreateSpeciality(TunedModel):
    speciality_code: str


class UpdateSpeciality(TunedModel):
    speciality_code: str
    new_speciality_code: str


'''
=====
GROUP
=====
'''


class ShowGroup(TunedModel):
    """Class for get group info"""
    group_name: str
    speciality_code: str
    quantity_students: int
    group_advisor_id: int


class CreateGroup(TunedModel):
    group_name: str
    speciality_code: str | None = None
    quantity_students: int | None = None
    group_advisor_id: int | None = None


class UpdateGroup(TunedModel):
    group_name: str
    new_group_name: str | None = None
    speciality_code: str | None = None
    quantity_students: int | None = None
    group_advisor_id: int | None = None


'''
==========
Curriculum
==========
''' 


class ShowCurriculum(TunedModel):
    """Class for get curriculum info"""
    semester_number: int
    group_name: str
    subject_code: str
    lectures_hours: float
    laboratory_hours: float
    practical_hours: float