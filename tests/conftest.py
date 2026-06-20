import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest


def pytest_collection_modifyitems(config, items):
    pass


def make_fake_user(
    user_id=None,
    username="denkripton",
    email="denkripton@example.com",
    password=b"$2b$12$fakefakefakefakefakefakefakefakefake",
    google_id=None,
):
    user = MagicMock()
    user.id = user_id or uuid.uuid4()
    user.username = username
    user.email = email
    user.password = password
    user.google_id = google_id
    return user


def make_fake_track(
    track_id=None,
    owner_id=None,
    name="About Life",
    artists=None,
    duration=180_000,
    track_url=None,
    photo_url=None,
    created_at=None,
):
    track = MagicMock()
    track.id = track_id or uuid.uuid4()
    track.owner_id = owner_id or uuid.uuid4()
    track.name = name
    track.artists = artists if artists is not None else ["denkripton"]
    track.duration = duration
    track.track_url = track_url or f"track/{track.owner_id}/{uuid.uuid4()}"
    track.photo_url = photo_url or f"image/{track.owner_id}/{uuid.uuid4()}"
    track.created_at = created_at or datetime(2026, 1, 1, tzinfo=timezone.utc)
    return track


def make_fake_grade(grade_id=None, user_id=None, track_id=None, grade=8):
    obj = MagicMock()
    obj.id = grade_id or uuid.uuid4()
    obj.user_id = user_id or uuid.uuid4()
    obj.track_id = track_id or uuid.uuid4()
    obj.grade = grade
    return obj


def make_fake_profile(
    profile_id=None,
    user_id=None,
    birth_date=None,
    bio="Just a track creator",
    country="Ukraine",
    phone_number="+380999999999",
):
    profile = MagicMock()
    profile.id = profile_id or uuid.uuid4()
    profile.user_id = user_id or uuid.uuid4()
    profile.birth_date = birth_date or datetime(2000, 1, 1).date()
    profile.bio = bio
    profile.country = country
    profile.phone_number = phone_number
    return profile


def make_async_repo_session():
    session = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def track_repo():
    repo = MagicMock()
    repo.get_one = AsyncMock(return_value=None)
    repo.get_many = AsyncMock(return_value=[])
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_track_by_owner = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    repo.delete_obj = AsyncMock()
    repo.session = make_async_repo_session()
    return repo


@pytest.fixture
def user_repo():
    repo = MagicMock()
    repo.get_one = AsyncMock(return_value=None)
    repo.get_many = AsyncMock(return_value=[])
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_by_email = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    repo.delete_obj = AsyncMock()
    repo.session = make_async_repo_session()
    return repo


@pytest.fixture
def grade_repo():
    repo = MagicMock()
    repo.get_one = AsyncMock(return_value=None)
    repo.get_many = AsyncMock(return_value=[])
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_user_by_id = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    repo.delete_obj = AsyncMock()
    repo.session = make_async_repo_session()
    return repo


@pytest.fixture
def profile_repo():
    repo = MagicMock()
    repo.get_one = AsyncMock(return_value=None)
    repo.get_many = AsyncMock(return_value=[])
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_user_by_id = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    repo.delete_obj = AsyncMock()
    repo.session = make_async_repo_session()
    return repo


@pytest.fixture
def fake_jwt():
    jwt = MagicMock()
    jwt.create_access_token = MagicMock(return_value="fake.access.token")
    jwt.create_refresh_token = MagicMock(return_value="fake.refresh.token")
    jwt.validate_token = MagicMock(return_value=None)
    return jwt
