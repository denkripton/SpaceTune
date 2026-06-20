import uuid
from unittest.mock import AsyncMock

import pytest

from src.exceptions import ServiceError
from src.modules.grades.service import GradeService
from tests.conftest import make_fake_grade, make_fake_track, make_fake_user


@pytest.fixture
def grade_service(track_repo, user_repo, grade_repo):
    return GradeService(
        track_repo=track_repo, user_repo=user_repo, grade_repo=grade_repo
    )


async def test_grade_track_raises_422_when_user_does_not_exist(
    grade_service, user_repo
):
    user_repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(ServiceError) as exc_info:
        await grade_service.grade_track(
            user_id=uuid.uuid4(), track_id=uuid.uuid4(), user_grade=8
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "User does not exist"


async def test_grade_track_raises_422_when_track_does_not_exist(
    grade_service, user_repo, track_repo
):
    user = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=user)
    track_repo.get_one = AsyncMock(return_value=None)

    with pytest.raises(ServiceError) as exc_info:
        await grade_service.grade_track(
            user_id=user.id, track_id=uuid.uuid4(), user_grade=8
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Track does not exist"


async def test_grade_track_creates_new_grade_when_none_exists(
    grade_service, user_repo, track_repo, grade_repo
):
    user = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=user)

    track = make_fake_track(name="Fresh Track", artists=["denkripton"])
    track_repo.get_one = AsyncMock(return_value=track)

    grade_repo.get_one = AsyncMock(return_value=None)
    created_grade = make_fake_grade(user_id=user.id, track_id=track.id, grade=9)
    grade_repo.create = AsyncMock(return_value=created_grade)

    result = await grade_service.grade_track(
        user_id=user.id, track_id=track.id, user_grade=9
    )

    grade_repo.create.assert_awaited_once()
    _, create_kwargs = grade_repo.create.call_args
    assert create_kwargs["grade"] == 9
    assert create_kwargs["user_id"] == user.id
    assert create_kwargs["track_id"] == track.id

    grade_repo.session.commit.assert_awaited_once()
    assert "9" in result
    assert "Fresh Track" in result


async def test_grade_track_updates_existing_grade_instead_of_creating_new_one(
    grade_service, user_repo, track_repo, grade_repo
):
    user = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=user)

    track = make_fake_track(name="Already Rated Track")
    track_repo.get_one = AsyncMock(return_value=track)

    existing_grade = make_fake_grade(user_id=user.id, track_id=track.id, grade=5)
    grade_repo.get_one = AsyncMock(return_value=existing_grade)

    result = await grade_service.grade_track(
        user_id=user.id, track_id=track.id, user_grade=10
    )

    grade_repo.create.assert_not_called()
    assert existing_grade.grade == 10

    grade_repo.session.commit.assert_awaited_once()
    assert "10" in result
    assert "Already Rated Track" in result


async def test_grade_track_rolls_back_on_create_failure(
    grade_service, user_repo, track_repo, grade_repo
):
    user = make_fake_user()
    user_repo.get_by_id = AsyncMock(return_value=user)

    track = make_fake_track()
    track_repo.get_one = AsyncMock(return_value=track)
    grade_repo.get_one = AsyncMock(return_value=None)

    grade_repo.create = AsyncMock(return_value=make_fake_grade())
    grade_repo.session.commit = AsyncMock(
        side_effect=Exception("check constraint violated")
    )

    await grade_service.grade_track(user_id=user.id, track_id=track.id, user_grade=99)

    grade_repo.session.rollback.assert_awaited_once()
