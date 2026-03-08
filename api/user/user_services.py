from api.user.user_pydantic import *
from api.user.user_DAL import UserDAL
from db.models import User
from security.password import get_password_hash
from fastapi import HTTPException

from config.logging_config import configure_logging

# Create logger object
logger = configure_logging()


class UserService:
    async def _create_new_user(self, body: CreateUser, db) -> ShowUser:
        async with db as session:
            user_dal = UserDAL(session)

            # Проверяем, существует ли пользователь с таким email
            existing_user = await user_dal.get_user_by_email(body.email)
            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail=f"Пользователь с email {body.email} уже существует."
                )

            try:
                # Преобразовываем пароль в хеш
                hashed_password = get_password_hash(body.password)
                # Создаём пользователя
                user = User(
                    username=body.username,
                    email=body.email,
                    hashed_password=hashed_password,
                    role=body.role
                )

                # Сохраняем пользователя в бд
                user = await user_dal.create_user(user)
                return user

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при создании пользователя: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")

    async def _get_user_by_email(self, email: str, db) -> ShowUser:
        async with db as session:
            user_dal = UserDAL(session)
            user = await user_dal.get_user_by_email(email)

            if not user:
                raise HTTPException(status_code=404, detail="Пользователь не найден.")

            return user