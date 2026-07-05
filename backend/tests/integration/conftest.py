import os
from unittest.mock import patch, MagicMock
from urllib.parse import quote

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from src.databases.sql_db import Base

TEST_DB_URL = os.environ.get("TEST_DB_URL")


@pytest_asyncio.fixture(scope="session")
async def postgres_engine(tmp_path_factory):
    pgserver_instance = None

    if TEST_DB_URL:
        db_url = TEST_DB_URL
    else:
        try:
            import pgserver
        except ImportError:
            pytest.skip(
                "Integration tests require a real Postgres instance. "
                "Set TEST_DB_URL in the environment, or install the "
                "'pgserver' package for an ephemeral test database "
                "without Docker."
            )

        pgdata_dir = tmp_path_factory.mktemp("pgdata")
        pgserver_instance = pgserver.get_server(str(pgdata_dir))
        try:
            pgserver_instance.psql("CREATE DATABASE spacetune_test;")
        except Exception as exc:
            pgserver_instance.cleanup()
            pytest.skip(f"Failed to create test database via pgserver: {exc}")

        socket_dir = quote(str(pgserver_instance.pgdata), safe="")
        db_url = f"postgresql+asyncpg://postgres@/spacetune_test?host={socket_dir}"

    engine = create_async_engine(db_url, echo=False, poolclass=NullPool)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(lambda c: None)
    except Exception as exc:
        await engine.dispose()
        if pgserver_instance:
            pgserver_instance.cleanup()
        pytest.skip(
            f"Integration tests require a real Postgres instance at "
            f"{db_url!r}, but the connection failed: {exc}."
        )

    yield engine

    await engine.dispose()
    if pgserver_instance:
        pgserver_instance.cleanup()


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
    fake.upload_file.return_value = "fake-key"
    fake.delete_file.return_value = None
    fake.presigned_url.return_value = "https://s3.fake/presigned-url"
    with patch("src.modules.music.service.bucket_manager", fake):
        yield fake
