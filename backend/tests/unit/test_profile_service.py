import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.utils.exceptions import FileSizeLimitExceeded, ServiceError
from src.modules.auth.schemas.user.read import UserRead
from src.modules.profile.schemas.read import ProfilePrivateReadSchema, ProfilePublicReadSchema
from src.modules.profile.schemas.update import ProfileUpdateSchema
from src.modules.profile.schemas.visibility import ProfileVisibilityUpdateSchema
from src.modules.profile.service import ProfileService
from src.modules.profile.utils.enums import PFPSizeLimit
from tests.factories import make_fake_bucket_manager, make_fake_profile, make_fake_user


@pytest.fixture
def profile_service(user_repo, profile_repo, fake_uow):
    return ProfileService(repo=user_repo, profile_repo=profile_repo, uow=fake_uow)


@pytest.fixture
def fake_bucket_manager(monkeypatch):
    fake = make_fake_bucket_manager()
    monkeypatch.setattr("src.modules.profile.service.bucket_manager", fake)
    return fake


def make_upload_file(content_type="image/png", size=1024, filename="pfp.png"):
    upload = MagicMock()
    upload.content_type = content_type
    upload.size = size
    upload.filename = filename
    upload.file = MagicMock()
    return upload


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


async def test_get_my_profile_returns_private_schema_with_nulls_when_profile_not_created_yet(
    profile_service, user_repo, profile_repo
):
    user = make_fake_user(photo_url="profile/x/y")
    user_repo.get_by_id = AsyncMock(return_value=user)
    profile_repo.get_one = AsyncMock(return_value=None)

    result = await profile_service.get_my_profile(user_id=user.id)

    assert isinstance(result, ProfilePrivateReadSchema)
    assert result.id == user.id
    assert result.username == user.username
    assert result.photo_url is not None
    assert "profile/x/y" in result.photo_url
    assert result.bio is None
    assert result.country is None


async def test_get_my_profile_returns_full_profile_when_it_exists(
    profile_service, user_repo, profile_repo
):
    user = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=user)

    profile = make_fake_profile(user_id=user.id, bio="Full profile bio")
    profile_repo.get_one = AsyncMock(return_value=profile)

    result = await profile_service.get_my_profile(user_id=user.id)

    assert isinstance(result, ProfilePrivateReadSchema)
    assert result.bio == "Full profile bio"
    assert result.country == profile.country


async def test_get_my_profile_survives_corrupted_visible_fields_data(
    profile_service, user_repo, profile_repo
):
    user = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=user)

    profile = make_fake_profile(
        user_id=user.id,
        visible_fields={
            "bio": True,
            "email": False,
            "phone_number": False,
            "visible_fields": {"bio": True},  # corrupted self-referential key
            "some_future_field_not_yet_known": True,
        },
    )
    profile_repo.get_one = AsyncMock(return_value=profile)

    result = await profile_service.get_my_profile(user_id=user.id)

    assert isinstance(result, ProfilePrivateReadSchema)
    assert result.visible_fields == {"bio": True, "email": False, "phone_number": False}


async def test_get_user_profile_raises_422_when_user_does_not_exist(
    profile_service, user_repo
):
    user_repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(ServiceError) as exc_info:
        await profile_service.get_user_profile(user_id=uuid.uuid4())

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "User does not exist"


async def test_get_user_profile_does_not_leak_email_when_no_profile_exists(
    profile_service, user_repo, profile_repo
):
    user = make_fake_user(email="secret@example.com")
    user_repo.get_by_id = AsyncMock(return_value=user)
    profile_repo.get_one = AsyncMock(return_value=None)

    result = await profile_service.get_user_profile(user_id=user.id)

    assert isinstance(result, ProfilePublicReadSchema)
    assert result.email is None
    assert result.bio is None
    assert result.country is None
    assert result.phone_number is None
    assert result.birth_date is None
    assert result.username == user.username


async def test_get_user_profile_hides_fields_marked_not_visible(
    profile_service, user_repo, profile_repo
):
    user = make_fake_user(email="visible-check@example.com")
    user_repo.get_by_id = AsyncMock(return_value=user)

    profile = make_fake_profile(
        user_id=user.id,
        bio="Should be hidden",
        country="Should be visible",
        visible_fields={
            "email": False,
            "phone_number": False,
            "birth_date": False,
            "bio": False,
            "country": True,
        },
    )
    profile_repo.get_one = AsyncMock(return_value=profile)

    result = await profile_service.get_user_profile(user_id=user.id)

    assert isinstance(result, ProfilePublicReadSchema)
    assert result.email is None
    assert result.bio is None
    assert result.country == "Should be visible"


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


async def test_delete_profile_does_not_touch_users_photo(
    profile_service, user_repo, profile_repo, fake_bucket_manager
):
    user = make_fake_user(photo_url="profile/x/y")
    user_repo.get_by_id = AsyncMock(return_value=user)
    profile = make_fake_profile(user_id=user.id)
    profile_repo.get_one = AsyncMock(return_value=profile)
    profile_repo.delete_obj = AsyncMock(return_value=profile)

    await profile_service.delete_profile(user_id=user.id)

    fake_bucket_manager.delete_file.assert_not_awaited()
    assert user.photo_url == "profile/x/y"


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
    assert isinstance(result, ProfilePrivateReadSchema)
    assert result.username == "newname"


def make_update_schema(**fields):
    return ProfileUpdateSchema(**fields)


async def test_update_profile_raises_422_when_user_does_not_exist(
    profile_service, user_repo
):
    user_repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(ServiceError) as exc_info:
        await profile_service.update_profile(
            user_id=uuid.uuid4(), data=make_update_schema(bio="x")
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "User does not exist"


async def test_update_profile_raises_422_when_profile_does_not_exist(
    profile_service, user_repo, profile_repo
):
    user = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=user)
    profile_repo.get_one = AsyncMock(return_value=None)

    with pytest.raises(ServiceError) as exc_info:
        await profile_service.update_profile(
            user_id=user.id, data=make_update_schema(bio="x")
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Profile does not exist"


async def test_update_profile_only_applies_fields_explicitly_sent(
    profile_service, user_repo, profile_repo
):
    user = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=user)

    profile = make_fake_profile(
        user_id=user.id, bio="old bio", country="Poland", phone_number="+111"
    )
    profile_repo.get_one = AsyncMock(return_value=profile)

    await profile_service.update_profile(
        user_id=user.id, data=make_update_schema(bio="new bio")
    )

    assert profile.bio == "new bio"
    assert profile.country == "Poland"
    assert profile.phone_number == "+111"
    profile_repo.session.commit.assert_awaited_once()


async def test_update_profile_explicit_null_clears_field(
    profile_service, user_repo, profile_repo
):
    user = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=user)

    profile = make_fake_profile(user_id=user.id, bio="old bio")
    profile_repo.get_one = AsyncMock(return_value=profile)

    await profile_service.update_profile(
        user_id=user.id, data=make_update_schema(bio=None)
    )

    assert profile.bio is None


async def test_update_visibility_raises_422_when_user_does_not_exist(
    profile_service, user_repo
):
    user_repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(ServiceError) as exc_info:
        await profile_service.update_visibility(
            user_id=uuid.uuid4(),
            data=ProfileVisibilityUpdateSchema(bio=False),
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "User does not exist"


async def test_update_visibility_raises_422_when_profile_does_not_exist(
    profile_service, user_repo, profile_repo
):
    user = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=user)
    profile_repo.get_one = AsyncMock(return_value=None)

    with pytest.raises(ServiceError) as exc_info:
        await profile_service.update_visibility(
            user_id=user.id,
            data=ProfileVisibilityUpdateSchema(bio=False),
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Profile does not exist"


async def test_update_visibility_merges_not_replaces(
    profile_service, user_repo, profile_repo
):
    user = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=user)

    profile = make_fake_profile(
        user_id=user.id,
        visible_fields={
            "email": False,
            "phone_number": False,
            "birth_date": False,
            "bio": True,
            "country": True,
        },
    )
    profile_repo.get_one = AsyncMock(return_value=profile)

    await profile_service.update_visibility(
        user_id=user.id,
        data=ProfileVisibilityUpdateSchema(bio=False),
    )

    assert profile.visible_fields["bio"] is False
    assert profile.visible_fields["country"] is True
    assert profile.visible_fields["email"] is False
    profile_repo.session.commit.assert_awaited_once()


async def test_update_visibility_leaves_untouched_fields_alone_when_all_unset(
    profile_service, user_repo, profile_repo
):
    user = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=user)
    profile = make_fake_profile(
        user_id=user.id, visible_fields={"bio": True, "country": True}
    )
    profile_repo.get_one = AsyncMock(return_value=profile)

    await profile_service.update_visibility(
        user_id=user.id, data=ProfileVisibilityUpdateSchema()
    )

    assert profile.visible_fields == {"bio": True, "country": True}


async def test_update_visibility_rejects_unknown_field_at_schema_level():
    with pytest.raises(Exception):
        ProfileVisibilityUpdateSchema(password=False)


async def test_upload_photo_raises_422_when_user_does_not_exist(
    profile_service, user_repo
):
    user_repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(ServiceError) as exc_info:
        await profile_service.upload_photo(
            user_id=uuid.uuid4(), photo_file=make_upload_file()
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "User does not exist"


async def test_upload_photo_succeeds_with_no_profile_row(
    profile_service, user_repo, profile_repo, fake_bucket_manager
):
    user = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=user)
    profile_repo.get_one = AsyncMock(return_value=None)

    await profile_service.upload_photo(user_id=user.id, photo_file=make_upload_file())

    fake_bucket_manager.upload_file.assert_awaited_once()
    assert user.photo_url.startswith(f"profile/{user.id}/")


async def test_upload_photo_rejects_invalid_content_type(
    profile_service, user_repo, fake_bucket_manager
):
    user = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=user)

    with pytest.raises(ServiceError) as exc_info:
        await profile_service.upload_photo(
            user_id=user.id,
            photo_file=make_upload_file(content_type="application/pdf"),
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Invalid image file type"
    fake_bucket_manager.upload_file.assert_not_awaited()


async def test_upload_photo_rejects_oversized_file_by_reported_size(
    profile_service, user_repo, fake_bucket_manager
):
    user = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=user)

    with pytest.raises(ServiceError) as exc_info:
        await profile_service.upload_photo(
            user_id=user.id,
            photo_file=make_upload_file(size=PFPSizeLimit.MAX_PHOTO_SIZE + 1),
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Photo file is too big"
    fake_bucket_manager.upload_file.assert_not_awaited()


async def test_upload_photo_rejects_oversized_stream_when_size_header_absent(
    profile_service, user_repo, fake_bucket_manager
):

    fake_bucket_manager.upload_file = AsyncMock(
        side_effect=FileSizeLimitExceeded("too big")
    )
    user = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=user)

    with pytest.raises(ServiceError) as exc_info:
        await profile_service.upload_photo(
            user_id=user.id, photo_file=make_upload_file(size=None)
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Photo file is too big"


async def test_upload_photo_success_sets_new_key_and_cleans_up_old_photo(
    profile_service, user_repo, fake_bucket_manager
):
    user = make_fake_user(photo_url="profile/old/key")
    user_repo.get_by_id = AsyncMock(return_value=user)

    await profile_service.upload_photo(user_id=user.id, photo_file=make_upload_file())

    fake_bucket_manager.upload_file.assert_awaited_once()
    assert user.photo_url.startswith(f"profile/{user.id}/")
    assert user.photo_url != "profile/old/key"
    fake_bucket_manager.delete_file.assert_awaited_once_with(key="profile/old/key")
    user_repo.session.commit.assert_awaited_once()


async def test_upload_photo_success_skips_cleanup_when_no_old_photo(
    profile_service, user_repo, fake_bucket_manager
):
    user = make_fake_user(photo_url=None)
    user_repo.get_by_id = AsyncMock(return_value=user)

    await profile_service.upload_photo(user_id=user.id, photo_file=make_upload_file())

    fake_bucket_manager.delete_file.assert_not_awaited()


async def test_upload_photo_succeeds_even_if_old_photo_cleanup_fails(
    profile_service, user_repo, fake_bucket_manager
):
    user = make_fake_user(photo_url="profile/old/key")
    user_repo.get_by_id = AsyncMock(return_value=user)
    fake_bucket_manager.delete_file = AsyncMock(side_effect=RuntimeError("S3 down"))

    result = await profile_service.upload_photo(
        user_id=user.id, photo_file=make_upload_file()
    )

    assert result is not None


async def test_delete_photo_raises_422_when_user_does_not_exist(
    profile_service, user_repo
):
    user_repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(ServiceError) as exc_info:
        await profile_service.delete_photo(user_id=uuid.uuid4())

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "User does not exist"


async def test_delete_photo_raises_422_when_no_photo_set(
    profile_service, user_repo, fake_bucket_manager
):
    user = make_fake_user(photo_url=None)
    user_repo.get_by_id = AsyncMock(return_value=user)

    with pytest.raises(ServiceError) as exc_info:
        await profile_service.delete_photo(user_id=user.id)

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "No photo set for this user"
    fake_bucket_manager.delete_file.assert_not_awaited()


async def test_delete_photo_succeeds_with_no_profile_row(
    profile_service, user_repo, profile_repo, fake_bucket_manager
):
    user = make_fake_user(photo_url="profile/x/y")
    user_repo.get_by_id = AsyncMock(return_value=user)
    profile_repo.get_one = AsyncMock(return_value=None)

    await profile_service.delete_photo(user_id=user.id)

    assert user.photo_url is None


async def test_delete_photo_success_clears_photo_url_and_deletes_from_s3(
    profile_service, user_repo, fake_bucket_manager
):
    user = make_fake_user(photo_url="profile/x/y")
    user_repo.get_by_id = AsyncMock(return_value=user)

    result = await profile_service.delete_photo(user_id=user.id)

    assert user.photo_url is None
    fake_bucket_manager.delete_file.assert_awaited_once_with(key="profile/x/y")
    user_repo.session.commit.assert_awaited_once()
    assert result is not None


async def test_delete_photo_deletes_s3_after_db_commit(
    profile_service, user_repo, fake_bucket_manager
):
    call_order = []
    user_repo.session.commit = AsyncMock(
        side_effect=lambda: call_order.append("commit")
    )
    fake_bucket_manager.delete_file = AsyncMock(
        side_effect=lambda key: call_order.append("s3_delete")
    )

    user = make_fake_user(photo_url="profile/x/y")
    user_repo.get_by_id = AsyncMock(return_value=user)

    await profile_service.delete_photo(user_id=user.id)

    assert call_order == ["commit", "s3_delete"]


async def test_delete_photo_succeeds_even_if_s3_delete_fails(
    profile_service, user_repo, fake_bucket_manager
):
    user = make_fake_user(photo_url="profile/x/y")
    user_repo.get_by_id = AsyncMock(return_value=user)
    fake_bucket_manager.delete_file = AsyncMock(side_effect=RuntimeError("S3 down"))

    result = await profile_service.delete_photo(user_id=user.id)

    assert result is not None
    assert user.photo_url is None