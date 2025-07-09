"""
File for creating validation models
"""

from pydantic import BaseModel, EmailStr, validator


class TunedModel(BaseModel):
    class Config:
        """
        Tells pydantic to convert even non dict obj to json.
        We'll get fed up with this class
        """
        orm_mode = True


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


