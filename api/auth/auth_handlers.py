from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from security.security_pydantic import Token, LoginRequest
from db.session import get_db
from api.auth.auth_services import AuthService

auth_router = APIRouter()
auth_service = AuthService()


@auth_router.post("/token", response_model=Token)
async def login_for_access_token(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Получение JWT токена для авторизованного пользователя"""
    return await auth_service.authenticate(body, db)
