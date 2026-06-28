import uuid
from unittest.mock import AsyncMock

import pytest

from backend.src.utils.exceptions import ServiceError
from src.modules.auth.schemas.user.read import UserRead
from src.modules.profile.schemas.read import ProfileReadSchema
from src.modules.profile.service import ProfileService
from tests.conftest import make_fake_profile, make_fake_user


@pytest.fixture
def profile_service(user_repo, profile_repo):
    return ProfileService(repo=user_repo, profile_repo=profile_repo)


def make_creation_schema(
    birth_date=None, bio="Hi there", country="Ukraine", phone_number="+380999999999"
):
    from datetime import date
    from unittest.mock import MagicMock

    schema = MagicMock()
    schema.model_dump.return_value = {
        "birth_date": birth_date or date(2000, 1, 1),
        "bio": bio,
        "country": country,
        "phone_number": phone_number,
    }
    return schema


async def test_create_profile_raises_422_when_user_does_not_exist(
    profile_service, user_repo
):
    user_repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(ServiceError) as exc_info:
        await profile_service.create_profile(
            user_id=str(uuid.uuid4()), data=make_creation_schema()
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "User does not exist"


async def test_create_profile_raises_422_when_profile_already_exists(
    profile_service, user_repo, profile_repo
):
    user = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=user)
    profile_repo.get_user_by_id = AsyncMock(
        return_value=make_fake_profile(user_id=user.id)
    )

    with pytest.raises(ServiceError) as exc_info:
        await profile_service.create_profile(
            user_id=str(user.id), data=make_creation_schema()
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Profile already created"


async def test_create_profile_success_passes_user_id_to_repository(
    profile_service, user_repo, profile_repo
):
    user = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=user)
    profile_repo.get_user_by_id = AsyncMock(return_value=None)

    created_profile = make_fake_profile(user_id=user.id)
    profile_repo.create = AsyncMock(return_value=created_profile)

    result = await profile_service.create_profile(
        user_id=str(user.id), data=make_creation_schema(bio="My new bio")
    )

    profile_repo.create.assert_awaited_once()
    _, create_kwargs = profile_repo.create.call_args
    assert create_kwargs["user_id"] == user.id
    assert create_kwargs["bio"] == "My new bio"

    profile_repo.session.commit.assert_awaited_once()
    assert result is created_profile


async def test_get_my_profile_raises_422_when_user_does_not_exist(
    profile_service, user_repo
):
    user_repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(ServiceError) as exc_info:
        await profile_service.get_my_profile(user_id=uuid.uuid4())

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "User does not exist"


async def test_get_my_profile_returns_user_read_when_profile_not_created_yet(
    profile_service, user_repo, profile_repo
):
    user = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=user)
    profile_repo.get_one = AsyncMock(return_value=None)

    result = await profile_service.get_my_profile(user_id=user.id)

    assert isinstance(result, UserRead)
    assert result.id == user.id
    assert result.username == user.username


async def test_get_my_profile_returns_full_profile_when_it_exists(
    profile_service, user_repo, profile_repo
):
    user = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=user)

    profile = make_fake_profile(user_id=user.id, bio="Full profile bio")
    profile_repo.get_one = AsyncMock(return_value=profile)

    result = await profile_service.get_my_profile(user_id=user.id)

    assert isinstance(result, ProfileReadSchema)
    assert result.bio == "Full profile bio"
    assert result.country == profile.country


async def test_delete_profile_raises_422_when_user_does_not_exist(
    profile_service, user_repo
):
    user_repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(ServiceError) as exc_info:
        await profile_service.delete_profile(user_id=uuid.uuid4())

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "User does not exist"


async def test_delete_profile_raises_422_when_profile_does_not_exist(
    profile_service, user_repo, profile_repo
):
    user = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=user)
    profile_repo.get_one = AsyncMock(return_value=None)

    with pytest.raises(ServiceError) as exc_info:
        await profile_service.delete_profile(user_id=user.id)

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Profile does not exist"


async def test_delete_profile_success(profile_service, user_repo, profile_repo):
    user = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=user)

    profile = make_fake_profile(user_id=user.id)
    profile_repo.get_one = AsyncMock(return_value=profile)
    profile_repo.delete_obj = AsyncMock(return_value=profile)

    result = await profile_service.delete_profile(user_id=user.id)

    profile_repo.delete_obj.assert_awaited_once_with(profile.id)
    profile_repo.session.commit.assert_awaited_once()
    assert result == "Profile has been deleted succesfuly"


async def test_update_username_raises_422_when_user_does_not_exist(
    profile_service, user_repo
):
    user_repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(ServiceError) as exc_info:
        await profile_service.update_username(
            user_id=uuid.uuid4(), new_username="newname"
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "User does not exist"


async def test_update_username_raises_422_when_new_username_taken_by_someone_else(
    profile_service, user_repo
):
    user = make_fake_user(username="currentname")
    user_repo.get_by_id = AsyncMock(return_value=user)
    user_repo.get_one = AsyncMock(return_value=make_fake_user(username="takenname"))

    with pytest.raises(ServiceError) as exc_info:
        await profile_service.update_username(user_id=user.id, new_username="takenname")

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "That username already taken"


async def test_update_username_success_changes_username_in_place(
    profile_service, user_repo, profile_repo
):

    user = make_fake_user(username="oldname")
    user_repo.get_by_id = AsyncMock(return_value=user)
    user_repo.get_one = AsyncMock(return_value=None)
    profile_repo.get_one = AsyncMock(return_value=None)

    result = await profile_service.update_username(
        user_id=user.id, new_username="newname"
    )

    assert user.username == "newname"
    user_repo.session.commit.assert_awaited_once()
    assert isinstance(result, UserRead)
    assert result.username == "newname"
