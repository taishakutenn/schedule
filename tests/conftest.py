import asyncio
import os
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command

from config.settings import TEST_DATABASE_URL  # твой URL
from db.models import Base


# Создаем engine для тестовой БД
test_engine = create_async_engine(TEST_DATABASE_URL, future=True, echo=False)
AsyncSessionLocal = sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture(scope="session")
def event_loop():
    """Create pytest event_loop for async fixtures"""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    """Before testing, we roll out Alembic tests to the test database"""
    alembic_cfg = Config("alembic.ini")
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL.replace("+asyncpg", "")
    command.upgrade(alembic_cfg, "head")
    yield


@pytest.fixture()
async def db_session():
    """Create test session"""
    async with AsyncSessionLocal() as session:
        yield session
