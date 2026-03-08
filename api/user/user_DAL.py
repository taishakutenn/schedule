from sqlalchemy import or_, select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User
from config.decorators import log_exceptions

class UserDAL:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_user(self, user: User):
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        return user

    # async def get_user_by_nickname(self, db: AsyncSession, nickname: str) -> User | None:
    #     result = await db.execute(select(User).where(User.nickname == nickname))
    #     user = result.scalar_one_or_none()
    #     return user

    # async def get_all_users(self, db: AsyncSession) -> list[User]:
    #     result = await db.execute(select(User))
    #     users = result.scalars().all()
    #     return list(users)

    # async def get_user_by_uuid(self, db: AsyncSession, user_uuid) -> User | None:
    #     result = await db.execute(select(User).where(User.uuid == user_uuid))
    #     user = result.scalar_one_or_none()
    #     return user

    # async def get_user_by_nickname_or_email(self, db: AsyncSession, nickname: str, email: str) -> User | None:
    #     stmt = select(User).where(
    #         or_(
    #             User.nickname == nickname,
    #             User.email == email,
    #         )
    #     )

    #     result = await db.execute(stmt)
    #     return result.scalar_one_or_none()

    # async def patch_user_nickname(self, db: AsyncSession, user: User) -> User:
    #     await db.commit()
    #     await db.refresh(user)
    #     return user

    # async def delete_user(self, db: AsyncSession, user_uuid) -> bool:
    #     stmt = delete(User).where(User.uuid == user_uuid).returning(User.uuid)  # returning для проверки на удалённость

    #     result = await db.execute(stmt)
    #     await db.commit()

    #     return result.scalar_one_or_none() is not User