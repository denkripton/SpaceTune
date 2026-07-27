import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.modules.auth.services.user import UserService
from src.modules.auth.utils.hash_generation import pw_manager
from src.utils.exceptions import ServiceError

from tests.factories import make_fake_user


@pytest.fixture
def user_service(user_repo, fake_jwt, fake_uow):
    return UserService(repo=user_repo, jwt=fake_jwt, uow=fake_uow)


def make_creation_schema(
    username="newuser", email="newuser@example.com", password="Som3Th!ng"
):
    schema = MagicMock()
    schema.model_dump.return_value = {
        "username": username,
        "email": email,
        "password": password,
    }
    return schema


def make_login_schema(email="user@example.com", password="Som3Th!ng"):
    schema = MagicMock()
    schema.email = email
    schema.password = password
    return schema


async def test_register_raises_422_when_email_already_exists(user_service, user_repo):
    user_repo.get_by_email = AsyncMock(return_value=make_fake_user())

    with pytest.raises(ServiceError) as exc_info:
        await user_service.register(make_creation_schema())

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "User already exists"


async def test_register_raises_422_when_username_already_taken(user_service, user_repo):

    user_repo.get_by_email = AsyncMock(return_value=None)
    user_repo.get_one = AsyncMock(return_value=make_fake_user(username="taken"))

    with pytest.raises(ServiceError) as exc_info:
        await user_service.register(make_creation_schema(username="taken"))

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "That username already taken"


async def test_register_stores_hashed_password_not_plaintext(user_service, user_repo):

    user_repo.get_by_email = AsyncMock(return_value=None)
    user_repo.get_one = AsyncMock(return_value=None)

    created_user = make_fake_user(username="newuser", email="newuser@example.com")
    user_repo.create = AsyncMock(return_value=created_user)

    plain_password = "Som3Th!ng"
    await user_service.register(make_creation_schema(password=plain_password))

    user_repo.create.assert_awaited_once()
    _, create_kwargs = user_repo.create.call_args

    stored_password = create_kwargs["password"]
    assert stored_password != plain_password.encode()
    assert pw_manager.check_password(plain_password, stored_password) is True

    user_repo.session.commit.assert_awaited_once()
    user_repo.session.refresh.assert_awaited_once_with(created_user)


async def test_login_raises_403_on_incorrect_password(user_service, user_repo):
    real_hash = pw_manager.hash_password("CorrectPass1!")
    existing_user = make_fake_user(password=real_hash)
    user_repo.get_by_email = AsyncMock(return_value=existing_user)

    with pytest.raises(ServiceError) as exc_info:
        await user_service.login(make_login_schema(password="WrongPass1!"))

    assert exc_info.value.status_code == 403
    assert exc_info.value.message == "Invalid email or password"


async def test_login_raises_403_when_user_does_not_exist(user_service, user_repo):
    user_repo.get_by_email = AsyncMock(return_value=None)

    with pytest.raises(ServiceError) as exc_info:
        await user_service.login(make_login_schema())

    assert exc_info.value.status_code == 403
    assert exc_info.value.message == "Invalid email or password"


async def test_login_raises_403_for_oauth_only_account_no_password_set(
    user_service, user_repo
):
    oauth_user = make_fake_user(password=None)
    user_repo.get_by_email = AsyncMock(return_value=oauth_user)

    with pytest.raises(ServiceError) as exc_info:
        await user_service.login(make_login_schema(password="AnyPass1!"))

    assert exc_info.value.status_code == 403
    assert exc_info.value.message == "Invalid email or password"


async def test_login_error_messages_are_identical_across_failure_reasons(
    user_service, user_repo
):
    messages = set()

    user_repo.get_by_email = AsyncMock(return_value=None)
    with pytest.raises(ServiceError) as exc_info:
        await user_service.login(make_login_schema())
    messages.add(exc_info.value.message)

    oauth_user = make_fake_user(password=None)
    user_repo.get_by_email = AsyncMock(return_value=oauth_user)
    with pytest.raises(ServiceError) as exc_info:
        await user_service.login(make_login_schema())
    messages.add(exc_info.value.message)

    real_hash = pw_manager.hash_password("CorrectPass1!")
    existing_user = make_fake_user(password=real_hash)
    user_repo.get_by_email = AsyncMock(return_value=existing_user)
    with pytest.raises(ServiceError) as exc_info:
        await user_service.login(make_login_schema(password="WrongPass1!"))
    messages.add(exc_info.value.message)

    assert len(messages) == 1


async def test_login_calls_check_password_even_when_user_does_not_exist(
    user_service, user_repo
):
    from unittest.mock import patch

    user_repo.get_by_email = AsyncMock(return_value=None)

    with (
        patch(
            "src.modules.auth.services.user.pw_manager.check_password",
            return_value=False,
        ) as mock_check,
        pytest.raises(ServiceError),
    ):
        await user_service.login(make_login_schema())

    mock_check.assert_called_once()


async def test_login_returns_access_and_refresh_tokens_on_success(
    user_service, user_repo, fake_jwt
):
    real_hash = pw_manager.hash_password("CorrectPass1!")
    existing_user = make_fake_user(password=real_hash)
    user_repo.get_by_email = AsyncMock(return_value=existing_user)

    result = await user_service.login(make_login_schema(password="CorrectPass1!"))

    assert result == {"access": "fake.access.token", "refresh": "fake.refresh.token"}

    fake_jwt.create_access_token.assert_called_once_with(str(existing_user.id))
    fake_jwt.create_refresh_token.assert_called_once_with(str(existing_user.id))


async def test_set_password_raises_422_when_user_does_not_exist(
    user_service, user_repo
):
    user_repo.get_by_id_locked = AsyncMock(return_value=None)

    schema = MagicMock()
    schema.model_dump.return_value = {
        "password": "Som3Th!ng",
        "confirm_password": "Som3Th!ng",
    }

    with pytest.raises(ServiceError) as exc_info:
        await user_service.set_password(user_id=uuid.uuid4(), data=schema)

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "User does not exist"


async def test_set_password_raises_409_when_password_already_set(
    user_service, user_repo
):
    existing_user = make_fake_user(password=b"already-set-hash")
    user_repo.get_by_id_locked = AsyncMock(return_value=existing_user)

    schema = MagicMock()
    schema.model_dump.return_value = {
        "password": "Som3Th!ng",
        "confirm_password": "Som3Th!ng",
    }

    with pytest.raises(ServiceError) as exc_info:
        await user_service.set_password(user_id=existing_user.id, data=schema)

    assert exc_info.value.status_code == 409
    assert exc_info.value.message == "User password already exists"


async def test_set_password_succeeds_for_oauth_user_without_password(
    user_service, user_repo
):
    oauth_user = make_fake_user(password=None)
    user_repo.get_by_id_locked = AsyncMock(return_value=oauth_user)

    schema = MagicMock()
    schema.model_dump.return_value = {
        "password": "BrandNew1!",
        "confirm_password": "BrandNew1!",
    }

    result = await user_service.set_password(user_id=oauth_user.id, data=schema)

    assert result == "Password added successfully"
    assert oauth_user.password != b"BrandNew1!"
    assert pw_manager.check_password("BrandNew1!", oauth_user.password) is True
    user_repo.session.commit.assert_awaited_once()


async def test_change_password_raises_400_when_password_not_set(
    user_service, user_repo
):
    oauth_user = make_fake_user(password=None)
    user_repo.get_by_id_locked = AsyncMock(return_value=oauth_user)

    schema = MagicMock()
    schema.model_dump.return_value = {
        "password": "Old1!",
        "new_password": "New1!",
        "confirm_password": "New1!",
    }

    with pytest.raises(ServiceError) as exc_info:
        await user_service.change_password(user_id=oauth_user.id, data=schema)

    assert exc_info.value.status_code == 400
    assert exc_info.value.message == "Password is not set"


async def test_change_password_raises_403_on_wrong_current_password(
    user_service, user_repo
):
    real_hash = pw_manager.hash_password("CurrentPass1!")
    existing_user = make_fake_user(password=real_hash)
    user_repo.get_by_id_locked = AsyncMock(return_value=existing_user)

    schema = MagicMock()
    schema.model_dump.return_value = {
        "password": "WrongCurrent1!",
        "new_password": "New1!",
        "confirm_password": "New1!",
    }

    with pytest.raises(ServiceError) as exc_info:
        await user_service.change_password(user_id=existing_user.id, data=schema)

    assert exc_info.value.status_code == 403
    assert exc_info.value.message == "Incorrect password"


async def test_set_password_uses_locked_read_not_plain_get_by_id(
    user_service, user_repo
):
    oauth_user = make_fake_user(password=None)
    user_repo.get_by_id_locked = AsyncMock(return_value=oauth_user)

    schema = MagicMock()
    schema.model_dump.return_value = {
        "password": "BrandNew1!",
        "confirm_password": "BrandNew1!",
    }

    await user_service.set_password(user_id=oauth_user.id, data=schema)

    user_repo.get_by_id_locked.assert_awaited_once_with(id=oauth_user.id)
    user_repo.get_by_id.assert_not_awaited()


async def test_change_password_uses_locked_read_not_plain_get_by_id(
    user_service, user_repo
):
    old_hash = pw_manager.hash_password("CurrentPass1!")
    existing_user = make_fake_user(password=old_hash)
    user_repo.get_by_id_locked = AsyncMock(return_value=existing_user)

    schema = MagicMock()
    schema.model_dump.return_value = {
        "password": "CurrentPass1!",
        "new_password": "BrandNewPass1!",
        "confirm_password": "BrandNewPass1!",
    }

    await user_service.change_password(user_id=existing_user.id, data=schema)

    user_repo.get_by_id_locked.assert_awaited_once_with(id=existing_user.id)
    user_repo.get_by_id.assert_not_awaited()


async def test_change_password_updates_hash_on_success(user_service, user_repo):
    old_hash = pw_manager.hash_password("CurrentPass1!")
    existing_user = make_fake_user(password=old_hash)
    user_repo.get_by_id_locked = AsyncMock(return_value=existing_user)

    schema = MagicMock()
    schema.model_dump.return_value = {
        "password": "CurrentPass1!",
        "new_password": "BrandNewPass1!",
        "confirm_password": "BrandNewPass1!",
    }

    result = await user_service.change_password(user_id=existing_user.id, data=schema)

    assert result == "Password changed successfully"
    assert pw_manager.check_password("BrandNewPass1!", existing_user.password) is True
    assert pw_manager.check_password("CurrentPass1!", existing_user.password) is False
    user_repo.session.commit.assert_awaited_once()
