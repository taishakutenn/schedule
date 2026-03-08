from typing import Annotated, List

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

import jwt
from jwt import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from db.models import User
from config.settings import ALGORITHM, SECRET_KEY
from security.exceptions import CredentialsException, ForbiddenAccess
from security.security_pydantic import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db)
) -> User:
    """Получение текущего пользователя из токена"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise CredentialsException
        
        token_data = TokenData(email=email)
    except InvalidTokenError:
        raise CredentialsException
    
    # Получаем пользователя из БД по email
    from api.user.user_services import UserService
    user_service = UserService()
    user = await user_service._get_user_by_email(db, token_data.email)
    
    if user is None:
        raise CredentialsException
    
    return user


def require_role(allowed_roles: List[str]):
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_user)]
    ) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenAccess
        return current_user

    return role_checker