from pydantic import EmailStr, field_validator
from uuid import UUID

from api.models import TunedModel
from config.settings import USERS_ROLES


class CreateUser(TunedModel):
    username: str
    email: EmailStr
    password: str
    role: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        if value not in USERS_ROLES:
            raise ValueError(f"Недопустимая роль. Доступные роли: {', '.join(USERS_ROLES)}")
        return value


class ShowUser(TunedModel):
    username: str
    email: EmailStr
    role: str


class MeShow(ShowUser):
    uuid: UUID


class UserInDb(ShowUser):
    hashed_password: str