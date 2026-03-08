from pydantic import EmailStr
from api.models import TunedModel


class Token(TunedModel):
    """Модель, используемая для ответа токеном при авторизации"""
    access_token: str
    token_type: str


class TokenData(TunedModel):
    """Модель данных для сериализации пользователя"""
    email: EmailStr | None = None


class LoginRequest(TunedModel):
    """Модель для запроса аутентификации (получения токена)"""
    email: EmailStr
    password: str
