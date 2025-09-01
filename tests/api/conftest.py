import asyncio
import os
from typing import Generator, Any

import pytest
import pytest_asyncio
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command

from starlette.testclient import TestClient

from main import app
from db.session import get_db
from config.settings import TEST_DATABASE_URL
from db.models import Base, Teacher

# Create engine for test db
test_engine = create_async_engine(TEST_DATABASE_URL, future=True, echo=True)
AsyncSessionLocal = sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)

# Tables name for clean his
CLEAN_TABLES = [Teacher]


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    """Before testing, we apply Alembic migrations to the test database"""
    # Save original value
    original_db_url = os.environ.get("DATABASE_URL")

    try:
        # Set URL for Alembic
        os.environ["DATABASE_URL"] = TEST_DATABASE_URL.replace("+asyncpg", "")
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
    finally:
        # Restore the original value
        if original_db_url is not None:
            os.environ["DATABASE_URL"] = original_db_url
        elif "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]

    yield


@pytest.fixture(autouse=True)
def clean_tables_sync():
    async def _clean():
        async with AsyncSessionLocal() as session:

            print(f"\nВнутрення ошибка какая-то :) {await session.rollback()}")
            for model in CLEAN_TABLES:
                await session.execute(delete(model))
            await session.commit()
    asyncio.get_event_loop().run_until_complete(_clean())


@pytest.fixture()
async def db_session():
    """Create test session"""
    async with AsyncSessionLocal() as session:
        yield session
        await session.close()


async def _get_test_db():
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, Any, None]:
    """
    Create a new FastAPI TestClient that uses the test database session
    """
    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as client:
        yield client
