import os
import uuid
from datetime import date
from unittest.mock import patch
from urllib.parse import quote

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.databases.sql_db import Base
from src.modules.auth.models import User
from src.modules.grades.models import Grade
from src.modules.music.models import Track
from src.modules.profile.models import Profile

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
    with patch("src.aws.utils.actions.bucket_manager") as fake:
        fake.upload_file.return_value = "fake-key"
        fake.delete_file.return_value = None
        fake.presigned_url.return_value = "https://s3.fake/presigned-url"
        yield fake


async def create_real_user(
    session,
    username="denkripton",
    email="denkripton@example.com",
    password=b"$2b$12$fakefakefakefakefakefakefakefakefake",
    google_id=None,
):
    user = User(
        id=uuid.uuid4(),
        username=username,
        email=email,
        password=password,
        google_id=google_id,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def create_real_track(
    session,
    owner_id,
    name="About Life",
    artists=None,
    duration=180_000,
    track_url=None,
    photo_url=None,
):
    track = Track(
        id=uuid.uuid4(),
        owner_id=owner_id,
        name=name,
        artists=artists if artists is not None else ["denkripton"],
        duration=duration,
        track_url=track_url or f"track/{owner_id}/{uuid.uuid4()}",
        photo_url=photo_url or f"image/{owner_id}/{uuid.uuid4()}",
    )
    session.add(track)
    await session.commit()
    await session.refresh(track)
    return track


async def create_real_grade(session, user_id, track_id, grade=8):
    obj = Grade(id=uuid.uuid4(), user_id=user_id, track_id=track_id, grade=grade)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def create_real_profile(
    session,
    user_id,
    birth_date=None,
    bio="bio",
    country="Ukraine",
    phone_number="+380999999999",
):
    profile = Profile(
        id=uuid.uuid4(),
        user_id=user_id,
        birth_date=birth_date or date(2000, 1, 1),
        bio=bio,
        country=country,
        phone_number=phone_number,
    )
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return profile
