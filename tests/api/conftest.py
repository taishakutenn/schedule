# conftest.py
import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command

from main import app
from db.session import get_db
from db.models import Teacher
from config.settings import TEST_DATABASE_URL

# Create an engine and session for the test database
test_engine = create_async_engine(TEST_DATABASE_URL, future=True, echo=True)
TestAsyncSessionLocal = sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    """Applies Alembic migrations to the test database before running tests"""
    # Alembic usually works with a synchronous URL, so remove +asyncpg
    sync_test_db_url = TEST_DATABASE_URL.replace("+asyncpg", "")

    # Protect the original environment variable
    original_db_url = os.environ.get("DATABASE_URL")

    try:
        # Set environment variable for Alembic
        os.environ["DATABASE_URL"] = sync_test_db_url
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
    finally:
        # Restore the original environment variable
        if original_db_url is not None:
            os.environ["DATABASE_URL"] = original_db_url
        elif "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]

    yield


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clean_database():
    """Clears tables in the test database before each test"""
    CLEAN_TABLES = [Teacher]

    async with test_engine.begin() as conn:
        for table in CLEAN_TABLES:
            await conn.execute(delete(table))
    yield


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a session to the test database"""
    async with TestAsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    """Client for making HTTP requests to an application with a test database"""
    # Overriding get_db dependency in FastAPI application
    app.dependency_overrides[get_db] = override_get_db

    # Import httpx inside the fixture to avoid import issues
    from httpx import AsyncClient, ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clearing overrides after the test
    app.dependency_overrides.clear()
