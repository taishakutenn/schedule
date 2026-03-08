from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

from typing import Annotated

import jwt
from fastapi import Depends
from jwt import InvalidTokenError

from db.session import get_db
from db.models import User
from config.settings import ALGORITHM, SECRET_KEY
from security.password import verify_password
from security.security_pydantic import TokenData
from api.user.user_services import UserService

from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime, timedelta, timezone


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | bool:
    """Функция для проверки подлинности пользователя"""
    user_service = UserService()

    user = await user_service._get_user_by_email(email, db)
    if not user:
        return False

    if not verify_password(password, user.hashed_password):
        return False

    return user


async def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Служебная функция для генерации нового токена"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

