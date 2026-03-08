from datetime import timedelta
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import ACCESS_TOKEN_EXPIRE_MINUTES
from security.jwt import authenticate_user, create_access_token
from security.security_pydantic import Token, LoginRequest


class AuthService:
    async def authenticate(self, body: LoginRequest, db: AsyncSession) -> Token:
        """Аутентификация пользователя и выдача JWT токена"""
        user = await authenticate_user(db, body.email, body.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = await create_access_token(
            data={"sub": user.email, "role": user.role},
            expires_delta=access_token_expires
        )
        
        return Token(access_token=access_token, token_type="bearer")
