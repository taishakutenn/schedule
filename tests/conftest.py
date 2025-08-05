import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from config.settings import TEST_DATABASE_URL
from db.models import Base

test_engine = create_async_engine(TEST_DATABASE_URL, future=True, echo=True,
                                  execution_options={"isolation_level": "AUTOCOMMIT"})


@pytest.fixture(autouse=True, scope='session')
async def prepare_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
