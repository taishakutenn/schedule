from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from config.settings import REAL_DATABASE_URL

# create async engine
engine = create_async_engine(REAL_DATABASE_URL, future=True, echo=True)

# create async session
session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)