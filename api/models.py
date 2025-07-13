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


class QueryParams(TunedModel):
    """
    This is model for validate query params
    when we need to retrieve all data from the table
     """
    page: int = Field(default=0, ge=0)
    limit: int = Field(default=10, ge=1, le=100)


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


