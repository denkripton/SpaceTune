import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.utils import UnitOfWork
from src.modules.auth.repository import UserRepository
from src.modules.grades.repository import GradeRepository
from src.modules.music.repository import TrackRepository
from src.modules.music.schemas.track.creation import TrackCreationSchema
from src.modules.music.service import TrackService
from src.utils.exceptions import ServiceError

from tests.factories import (
    create_real_grade,
    create_real_track,
    create_real_user,
)

pytestmark = pytest.mark.integration


def make_upload_file(content_type="audio/mpeg", filename="track.mp3"):
    upload = MagicMock()
    upload.content_type = content_type
    upload.filename = filename
    upload.file = MagicMock()
    return upload


@pytest.fixture
def track_service(db_session):
    return TrackService(
        track_repo=TrackRepository(session=db_session),
        user_repo=UserRepository(session=db_session),
        grade_repo=GradeRepository(session=db_session),
        uow=UnitOfWork(db_session),
    )


async def test_create_track_end_to_end_persists_to_real_database(
    db_session, track_service, mocked_bucket_manager
):
    owner = await create_real_user(db_session, username="denkripton")

    creation_data = TrackCreationSchema(name="Integration Track", artists=["Co-Artist"])

    with (
        patch(
            "src.modules.music.service.count_duration",
            new=AsyncMock(return_value=200_000),
        ),
        patch("src.modules.music.service.bucket_manager", mocked_bucket_manager),
    ):
        result = await track_service.create_track(
            user_id=str(owner.id),
            data=creation_data,
            music_file=make_upload_file(),
            image_file=make_upload_file(content_type="image/png"),
        )

    assert result.name == "Integration Track"
    assert result.artists == ["denkripton", "Co-Artist"]
    assert result.duration == 200_000

    track_repo = TrackRepository(session=db_session)
    persisted = await track_repo.get_one(owner_id=owner.id, name="Integration Track")

    assert persisted is not None
    assert persisted.artists == ["denkripton", "Co-Artist"]
    assert persisted.duration == 200_000
    assert persisted.owner_id == owner.id


async def test_create_track_raises_422_when_duplicate_name_for_same_owner(
    db_session, track_service, mocked_bucket_manager
):
    owner = await create_real_user(db_session)
    await create_real_track(db_session, owner_id=owner.id, name="Existing Track")

    creation_data = TrackCreationSchema(name="Existing Track", artists=[])

    with (
        patch(
            "src.modules.music.service.count_duration",
            new=AsyncMock(return_value=100_000),
        ),
        patch("src.modules.music.service.bucket_manager", mocked_bucket_manager),
    ):
        with pytest.raises(ServiceError) as exc_info:
            await track_service.create_track(
                user_id=str(owner.id),
                data=creation_data,
                music_file=make_upload_file(),
                image_file=make_upload_file(content_type="image/png"),
            )

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Track already exist"


async def test_create_track_allows_same_name_for_different_owners(
    db_session, track_service, mocked_bucket_manager
):

    owner_one = await create_real_user(
        db_session, username="owner_one", email="one@example.com"
    )
    owner_two = await create_real_user(
        db_session, username="owner_two", email="two@example.com"
    )

    await create_real_track(db_session, owner_id=owner_one.id, name="Shared Title")

    creation_data = TrackCreationSchema(name="Shared Title", artists=[])

    with (
        patch(
            "src.modules.music.service.count_duration",
            new=AsyncMock(return_value=100_000),
        ),
        patch("src.modules.music.service.bucket_manager", mocked_bucket_manager),
    ):
        result = await track_service.create_track(
            user_id=str(owner_two.id),
            data=creation_data,
            music_file=make_upload_file(),
            image_file=make_upload_file(content_type="image/png"),
        )

    assert result.name == "Shared Title"


async def test_create_track_raises_service_error_and_cleans_up_s3_when_db_write_fails(
    db_session, track_service, mocked_bucket_manager
):
    owner = await create_real_user(db_session)
    fixed_uuid = uuid.uuid4()
    colliding_track_url = f"track/{owner.id}/{fixed_uuid}"
    await create_real_track(
        db_session,
        owner_id=owner.id,
        name="Pre-existing",
        track_url=colliding_track_url,
    )

    creation_data = TrackCreationSchema(name="Will Collide", artists=[])

    with (
        patch(
            "src.modules.music.service.count_duration",
            new=AsyncMock(return_value=100_000),
        ),
        patch(
            "src.modules.music.service.uuid.uuid4",
            side_effect=[fixed_uuid, uuid.uuid4()],
        ),
    ):
        with pytest.raises(ServiceError) as exc_info:
            await track_service.create_track(
                user_id=str(owner.id),
                data=creation_data,
                music_file=make_upload_file(),
                image_file=make_upload_file(content_type="image/png"),
            )

    assert exc_info.value.status_code == 500
    assert exc_info.value.message == "Failed to save track"

    uploaded_keys = {
        call.kwargs["key"] for call in mocked_bucket_manager.upload_file.call_args_list
    }
    deleted_keys = {
        call.kwargs["key"] for call in mocked_bucket_manager.delete_file.call_args_list
    }
    assert uploaded_keys == deleted_keys
    assert len(uploaded_keys) == 2

    track_repo = TrackRepository(session=db_session)
    assert await track_repo.get_one(owner_id=owner.id, name="Will Collide") is None


async def test_delete_track_removes_track_and_existing_grades(
    db_session, track_service, mocked_bucket_manager
):
    owner = await create_real_user(db_session)
    track = await create_real_track(db_session, owner_id=owner.id, name="Rated Track")
    grade = await create_real_grade(db_session, user_id=owner.id, track_id=track.id)

    with patch("src.modules.music.service.bucket_manager", mocked_bucket_manager):
        result = await track_service.delete_track(
            user_id=str(owner.id),
            track_id=track.id,
        )

    assert result == "Track has been deleted succesfuly"

    track_repo = TrackRepository(session=db_session)
    grade_repo = GradeRepository(session=db_session)

    assert await track_repo.get_by_id(track.id) is None
    assert await grade_repo.get_by_id(grade.id) is None
