from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.exceptions import ServiceError
from src.modules.auth.repository import UserRepository
from src.modules.grades.repository import GradeRepository
from src.modules.music.repository import TrackRepository
from src.modules.music.schemas.track.creation import TrackCreationSchema
from src.modules.music.service import TrackService
from tests.integration.conftest import create_real_track, create_real_user

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
