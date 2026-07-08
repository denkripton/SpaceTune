import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError
from src.modules.music.service import TrackService
from src.utils.exceptions import ServiceError

from src.modules.music.utils.enums import FileSizeLimit

from tests.factories import make_fake_track, make_fake_user


@pytest.fixture
def track_service(track_repo, user_repo, grade_repo):
    return TrackService(
        track_repo=track_repo, user_repo=user_repo, grade_repo=grade_repo
    )


def make_upload_file(content_type="audio/mpeg", filename="track.mp3", size=1024):
    upload = MagicMock()
    upload.content_type = content_type
    upload.filename = filename
    upload.file = MagicMock()
    upload.size = size
    return upload


@pytest.mark.parametrize(
    "user_id_value",
    [str(uuid.uuid4()), str(uuid.uuid4())],
)
async def test_create_track_raises_422_when_user_does_not_exist(
    track_service, user_repo, user_id_value
):
    user_repo.get_by_id = AsyncMock(return_value=None)

    creation_data = MagicMock()
    creation_data.model_dump.return_value = {"name": "Test", "artists": []}

    with pytest.raises(ServiceError) as exc_info:
        await track_service.create_track(
            user_id=user_id_value,
            data=creation_data,
            music_file=make_upload_file(),
            image_file=make_upload_file(content_type="image/png"),
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "User does not exist"
    track_service._TrackService__track_repo.get_one.assert_not_called()


async def test_create_track_raises_422_when_track_name_already_taken_by_owner(
    track_service, user_repo, track_repo
):

    owner = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=owner)

    duplicate = make_fake_track(owner_id=owner.id, name="Duplicate")
    track_repo.get_one = AsyncMock(return_value=duplicate)

    creation_data = MagicMock()
    creation_data.model_dump.return_value = {"name": "Duplicate", "artists": []}

    with pytest.raises(ServiceError) as exc_info:
        await track_service.create_track(
            user_id=str(owner.id),
            data=creation_data,
            music_file=make_upload_file(),
            image_file=make_upload_file(content_type="image/png"),
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Track already exist"

    track_repo.get_one.assert_awaited_once()
    _, kwargs = track_repo.get_one.call_args
    assert kwargs["owner_id"] == owner.id
    assert kwargs["name"] == "Duplicate"


async def test_create_track_raises_422_on_invalid_audio_content_type(
    track_service, user_repo, track_repo
):

    owner = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=owner)
    track_repo.get_one = AsyncMock(return_value=None)

    creation_data = MagicMock()
    creation_data.model_dump.return_value = {"name": "Bad Audio", "artists": []}

    bad_music_file = make_upload_file(content_type="application/x-msdownload")

    with (
        patch(
            "src.modules.music.service.count_duration",
            new=AsyncMock(return_value=180_000),
        ),
        patch("src.modules.music.service.bucket_manager") as fake_bucket,
    ):
        with pytest.raises(ServiceError) as exc_info:
            await track_service.create_track(
                user_id=str(owner.id),
                data=creation_data,
                music_file=bad_music_file,
                image_file=make_upload_file(content_type="image/png"),
            )

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Invalid audio file type"
    fake_bucket.upload_file.assert_not_called()


async def test_create_track_raises_422_on_invalid_image_content_type(
    track_service, user_repo, track_repo
):
    owner = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=owner)
    track_repo.get_one = AsyncMock(return_value=None)

    creation_data = MagicMock()
    creation_data.model_dump.return_value = {"name": "Bad Image", "artists": []}

    bad_image_file = make_upload_file(content_type="application/pdf")

    with (
        patch(
            "src.modules.music.service.count_duration",
            new=AsyncMock(return_value=180_000),
        ),
        patch("src.modules.music.service.bucket_manager") as fake_bucket,
    ):
        with pytest.raises(ServiceError) as exc_info:
            await track_service.create_track(
                user_id=str(owner.id),
                data=creation_data,
                music_file=make_upload_file(),
                image_file=bad_image_file,
            )

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Invalid image file type"

    assert fake_bucket.upload_file.call_count == 0


async def test_create_track_raises_422_when_audio_exceeds_size_limit(
    track_service, user_repo, track_repo
):

    owner = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=owner)
    track_repo.get_one = AsyncMock(return_value=None)

    creation_data = MagicMock()
    creation_data.model_dump.return_value = {"name": "Too Big", "artists": []}

    oversized_music_file = make_upload_file(size=FileSizeLimit.MAX_AUDIO_SIZE.value + 1)

    with (
        patch(
            "src.modules.music.service.count_duration",
            new=AsyncMock(return_value=180_000),
        ),
        patch("src.modules.music.service.bucket_manager") as fake_bucket,
    ):
        with pytest.raises(ServiceError) as exc_info:
            await track_service.create_track(
                user_id=str(owner.id),
                data=creation_data,
                music_file=oversized_music_file,
                image_file=make_upload_file(content_type="image/png"),
            )

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Audio file is too big"
    fake_bucket.upload_file.assert_not_called()


async def test_create_track_raises_422_when_image_exceeds_size_limit(
    track_service, user_repo, track_repo
):

    owner = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=owner)
    track_repo.get_one = AsyncMock(return_value=None)

    creation_data = MagicMock()
    creation_data.model_dump.return_value = {"name": "Too Big Image", "artists": []}

    oversized_image_file = make_upload_file(
        content_type="image/png", size=FileSizeLimit.MAX_AUDIO_SIZE.value + 1
    )

    with (
        patch(
            "src.modules.music.service.count_duration",
            new=AsyncMock(return_value=180_000),
        ),
        patch("src.modules.music.service.bucket_manager") as fake_bucket,
    ):
        with pytest.raises(ServiceError) as exc_info:
            await track_service.create_track(
                user_id=str(owner.id),
                data=creation_data,
                music_file=make_upload_file(),
                image_file=oversized_image_file,
            )

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Image file is too big"
    fake_bucket.upload_file.assert_not_called()


async def test_create_track_allows_upload_when_size_is_none(
    track_service, user_repo, track_repo
):
    owner = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=owner)
    track_repo.get_one = AsyncMock(return_value=None)

    created_track = make_fake_track(owner_id=owner.id, name="Unknown Size")
    track_repo.create = AsyncMock(return_value=created_track)

    creation_data = MagicMock()
    creation_data.model_dump.return_value = {"name": "Unknown Size", "artists": []}

    music_file = make_upload_file(size=None)
    image_file = make_upload_file(content_type="image/png", size=None)

    with (
        patch(
            "src.modules.music.service.count_duration",
            new=AsyncMock(return_value=1000),
        ),
        patch("src.modules.music.service.bucket_manager"),
    ):
        result = await track_service.create_track(
            user_id=str(owner.id),
            data=creation_data,
            music_file=music_file,
            image_file=image_file,
        )

    assert result.id == created_track.id


async def test_create_track_validates_type_and_size_before_count_duration(
    track_service, user_repo, track_repo
):
    owner = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=owner)
    track_repo.get_one = AsyncMock(return_value=None)

    creation_data = MagicMock()
    creation_data.model_dump.return_value = {"name": "Order Check", "artists": []}

    bad_file = make_upload_file(content_type="application/x-msdownload")

    with patch(
        "src.modules.music.service.count_duration",
        new=AsyncMock(return_value=180_000),
    ) as fake_count_duration:
        with pytest.raises(ServiceError) as exc_info:
            await track_service.create_track(
                user_id=str(owner.id),
                data=creation_data,
                music_file=bad_file,
                image_file=make_upload_file(content_type="image/png"),
            )

    assert exc_info.value.message == "Invalid audio file type"
    fake_count_duration.assert_not_awaited()


async def test_create_track_success_places_owner_first_in_artists(
    track_service, user_repo, track_repo
):
    owner = make_fake_user(username="denkripton")
    user_repo.get_by_id = AsyncMock(return_value=owner)
    track_repo.get_one = AsyncMock(return_value=None)

    created_track = make_fake_track(
        owner_id=owner.id,
        name="About Life",
        artists=["denkripton", "Co-Artist"],
        duration=180_000,
    )
    track_repo.create = AsyncMock(return_value=created_track)

    creation_data = MagicMock()
    creation_data.model_dump.return_value = {
        "name": "About Life",
        "artists": ["Co-Artist"],
    }

    with (
        patch(
            "src.modules.music.service.count_duration",
            new=AsyncMock(return_value=180_000),
        ) as fake_count_duration,
        patch("src.modules.music.service.bucket_manager") as fake_bucket,
    ):
        result = await track_service.create_track(
            user_id=str(owner.id),
            data=creation_data,
            music_file=make_upload_file(),
            image_file=make_upload_file(content_type="image/png"),
        )
    track_repo.create.assert_awaited_once()
    _, create_kwargs = track_repo.create.call_args
    assert create_kwargs["artists"] == ["denkripton", "Co-Artist"]
    assert create_kwargs["owner_id"] == owner.id
    assert create_kwargs["duration"] == 180_000

    fake_count_duration.assert_awaited_once()

    assert fake_bucket.upload_file.call_count == 2

    assert result.id == created_track.id
    assert result.name == "About Life"
    assert result.artists == ["denkripton", "Co-Artist"]
    assert result.duration == 180_000


async def test_create_track_raises_service_error_when_db_write_fails():
    owner = make_fake_user()
    user_repo_mock = MagicMock()
    user_repo_mock.get_by_id = AsyncMock(return_value=owner)

    track_repo_mock = MagicMock()
    track_repo_mock.get_one = AsyncMock(return_value=None)
    track_repo_mock.create = AsyncMock(side_effect=Exception("duplicate key value"))
    track_repo_mock.session = MagicMock()
    track_repo_mock.session.commit = AsyncMock()
    track_repo_mock.session.rollback = AsyncMock()
    track_repo_mock.session.refresh = AsyncMock()

    service = TrackService(
        track_repo=track_repo_mock, user_repo=user_repo_mock, grade_repo=MagicMock()
    )

    creation_data = MagicMock()
    creation_data.model_dump.return_value = {"name": "Crashy", "artists": []}

    with (
        patch(
            "src.modules.music.service.count_duration",
            new=AsyncMock(return_value=1000),
        ),
        patch("src.modules.music.service.bucket_manager") as fake_bucket,
    ):
        with pytest.raises(ServiceError) as exc_info:
            await service.create_track(
                user_id=str(owner.id),
                data=creation_data,
                music_file=make_upload_file(),
                image_file=make_upload_file(content_type="image/png"),
            )

    assert exc_info.value.status_code == 500
    assert exc_info.value.message == "Failed to save track"
    assert isinstance(exc_info.value.__cause__, Exception)

    track_repo_mock.session.rollback.assert_awaited_once()
    assert fake_bucket.delete_file.call_count == 2


async def test_create_track_raises_422_when_db_unique_constraint_violated():
    owner = make_fake_user()
    user_repo_mock = MagicMock()
    user_repo_mock.get_by_id = AsyncMock(return_value=owner)

    track_repo_mock = MagicMock()
    track_repo_mock.get_one = AsyncMock(return_value=None)
    track_repo_mock.create = AsyncMock(
        side_effect=IntegrityError(
            "duplicate key value", {}, Exception("duplicate key value")
        )
    )
    track_repo_mock.session = MagicMock()
    track_repo_mock.session.commit = AsyncMock()
    track_repo_mock.session.rollback = AsyncMock()
    track_repo_mock.session.refresh = AsyncMock()

    service = TrackService(
        track_repo=track_repo_mock, user_repo=user_repo_mock, grade_repo=MagicMock()
    )

    creation_data = MagicMock()
    creation_data.model_dump.return_value = {"name": "Crashy", "artists": []}

    with (
        patch(
            "src.modules.music.service.count_duration",
            new=AsyncMock(return_value=1000),
        ),
        patch("src.modules.music.service.bucket_manager") as fake_bucket,
    ):
        with pytest.raises(ServiceError) as exc_info:
            await service.create_track(
                user_id=str(owner.id),
                data=creation_data,
                music_file=make_upload_file(),
                image_file=make_upload_file(content_type="image/png"),
            )

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Track already exist"
    assert isinstance(exc_info.value.__cause__, IntegrityError)

    track_repo_mock.session.rollback.assert_awaited_once()
    assert fake_bucket.delete_file.call_count == 2


async def test_delete_track_raises_422_when_user_does_not_exist(
    track_service, user_repo
):
    user_repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(ServiceError) as exc_info:
        await track_service.delete_track(
            user_id=str(uuid.uuid4()), track_id=uuid.uuid4()
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "User does not exist"


async def test_delete_track_raises_422_when_track_does_not_exist(
    track_service, user_repo, track_repo
):
    owner = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=owner)
    track_repo.get_one = AsyncMock(return_value=None)

    with pytest.raises(ServiceError) as exc_info:
        await track_service.delete_track(user_id=str(owner.id), track_id=uuid.uuid4())

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Track does not exist"


async def test_delete_track_removes_both_files_from_s3_and_deletes_row(
    track_service, user_repo, track_repo
):

    owner = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=owner)

    existing_track = make_fake_track(owner_id=owner.id, name="To Delete")
    track_repo.get_one = AsyncMock(return_value=existing_track)
    track_repo.delete_obj = AsyncMock(return_value=existing_track)

    with patch("src.modules.music.service.bucket_manager") as fake_bucket:
        result = await track_service.delete_track(
            user_id=str(owner.id), track_id=existing_track.id
        )

    fake_bucket.delete_file.assert_any_call(key=existing_track.track_url)
    fake_bucket.delete_file.assert_any_call(key=existing_track.photo_url)
    assert fake_bucket.delete_file.call_count == 2

    track_repo.delete_obj.assert_awaited_once_with(id=existing_track.id)
    track_repo.session.commit.assert_awaited_once()

    assert result == "Track has been deleted succesfuly"


async def test_get_track_raises_422_when_track_not_found(track_service, track_repo):
    track_repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(ServiceError) as exc_info:
        await track_service.get_track(track_id=uuid.uuid4())

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Track does not exist"


async def test_get_track_returns_zero_average_when_no_grades_exist(
    track_service, track_repo, grade_repo
):

    existing_track = make_fake_track(name="No Grades Yet")
    track_repo.get_by_id = AsyncMock(return_value=existing_track)
    grade_repo.get_aggregates_by_track_ids = AsyncMock(return_value={})

    with patch("src.modules.music.service.bucket_manager") as fake_bucket:
        fake_bucket.presigned_url.return_value = "https://s3.fake/presigned"
        result = await track_service.get_track(track_id=existing_track.id)

    assert result["metadata"].average_grade == 0
    assert result["metadata"].number_of_ratings == 0
    assert result["media"].audio == "https://s3.fake/presigned"


async def test_get_track_computes_average_grade_correctly(
    track_service, track_repo, grade_repo
):
    existing_track = make_fake_track(name="Popular Track")
    track_repo.get_by_id = AsyncMock(return_value=existing_track)

    grade_repo.get_aggregates_by_track_ids = AsyncMock(
        return_value={existing_track.id: (9.0, 3)}
    )

    with patch("src.modules.music.service.bucket_manager") as fake_bucket:
        fake_bucket.presigned_url.return_value = "https://s3.fake/presigned"
        result = await track_service.get_track(track_id=existing_track.id)

    assert result["metadata"].average_grade == 9.0
    assert result["metadata"].number_of_ratings == 3


async def test_get_track_calls_grade_aggregation_exactly_once(
    track_service, track_repo, grade_repo
):
    existing_track = make_fake_track(name="Query Count Check")
    track_repo.get_by_id = AsyncMock(return_value=existing_track)
    grade_repo.get_aggregates_by_track_ids = AsyncMock(
        return_value={existing_track.id: (7.0, 2)}
    )

    with patch("src.modules.music.service.bucket_manager") as fake_bucket:
        fake_bucket.presigned_url.return_value = "https://s3.fake/presigned"
        await track_service.get_track(track_id=existing_track.id)

    grade_repo.get_aggregates_by_track_ids.assert_awaited_once_with([existing_track.id])


async def test_get_my_tracks_returns_empty_list_when_user_has_no_tracks(
    track_service, track_repo, grade_repo
):

    track_repo.get_many = AsyncMock(return_value=[])
    grade_repo.get_aggregates_by_track_ids = AsyncMock(return_value={})

    result = await track_service.get_my_tracks(user_id=uuid.uuid4())

    assert result == []
    grade_repo.get_aggregates_by_track_ids.assert_awaited_once_with([])


async def test_get_my_tracks_assembles_metadata_and_media_for_each_track(
    track_service, track_repo, grade_repo
):

    owner_id = uuid.uuid4()
    track_one = make_fake_track(owner_id=owner_id, name="Track One")
    track_two = make_fake_track(owner_id=owner_id, name="Track Two")

    track_repo.get_many = AsyncMock(return_value=[track_one, track_two])
    grade_repo.get_aggregates_by_track_ids = AsyncMock(
        return_value={track_one.id: (5.0, 1)}
    )

    with patch("src.modules.music.service.bucket_manager") as fake_bucket:
        fake_bucket.presigned_url.return_value = "https://s3.fake/presigned"
        result = await track_service.get_my_tracks(user_id=owner_id)

    assert len(result) == 2
    assert result[0].metadata.name == "Track One"
    assert result[0].metadata.average_grade == 5.0
    assert result[0].metadata.number_of_ratings == 1

    assert result[1].metadata.name == "Track Two"
    assert result[1].metadata.average_grade == 0
    assert result[1].metadata.number_of_ratings == 0


async def test_get_my_tracks_calls_grade_aggregation_exactly_once(
    track_service, track_repo, grade_repo
):
    owner_id = uuid.uuid4()
    tracks = [make_fake_track(owner_id=owner_id, name=f"Track {i}") for i in range(5)]

    track_repo.get_many = AsyncMock(return_value=tracks)
    grade_repo.get_aggregates_by_track_ids = AsyncMock(return_value={})

    with patch("src.modules.music.service.bucket_manager") as fake_bucket:
        fake_bucket.presigned_url.return_value = "https://s3.fake/presigned"
        await track_service.get_my_tracks(user_id=owner_id)

    assert grade_repo.get_aggregates_by_track_ids.await_count == 1
    called_with = grade_repo.get_aggregates_by_track_ids.await_args.args[0]
    assert set(called_with) == {t.id for t in tracks}
