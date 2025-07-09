from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from config.settings import REAL_DATABASE_URL

# create async engine
engine = create_async_engine(REAL_DATABASE_URL, future=True, echo=True,
                             execution_options={"isolation_level": "AUTOCOMMIT"})
# create async session
# Use parameter bind, because parameter engine isn't using in sqlalchemy ver 2...
async_session = sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async session"""
    try:
        session: AsyncSession = async_session()
        yield session
    finally:
        await session.close()
