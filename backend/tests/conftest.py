from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.factories import make_async_repo_session


def pytest_collection_modifyitems(config, items):
    pass


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
