from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from src.config import settings
from src.databases.sql_db import Base


@pytest_asyncio.fixture(scope="session")
async def postgres_engine():
    test_db_url = settings.TEST_DB_URL
    if not test_db_url:
        pytest.fail(
            "Integration tests require TEST_DB_URL. Run `docker compose up -d db` "
            "and set TEST_DB_URL in backend/.env (see .env.example). There is no "
            "in-process fallback: pgserver has no wheels for Python 3.13, which "
            "this project targets."
        )

    engine = create_async_engine(test_db_url, echo=False, poolclass=NullPool)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(lambda c: None)
    except Exception as exc:
        await engine.dispose()
        pytest.fail(
            f"Could not connect to TEST_DB_URL={test_db_url!r}: {exc}. "
            "Is `docker compose up -d db` running?"
        )

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(postgres_engine):
    async with postgres_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=postgres_engine, expire_on_commit=False, autoflush=False
    )
    async with session_factory() as session:
        yield session
        await session.rollback()

    async with postgres_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def mocked_bucket_manager():
    fake = MagicMock()
    fake.upload_file = AsyncMock(return_value="fake-key")
    fake.delete_file = AsyncMock(return_value=None)
    fake.presigned_url.return_value = "https://s3.fake/presigned-url"
    with patch("src.modules.music.service.bucket_manager", fake):
        yield fake
