import uuid
from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError
from src.modules.auth.repository import UserRepository
from src.modules.grades.repository import GradeRepository
from src.modules.music.repository import TrackRepository
from src.modules.profile.repository import ProfileRepository

from tests.factories import (
    create_real_grade,
    create_real_profile,
    create_real_track,
    create_real_user,
)

pytestmark = pytest.mark.integration


async def test_get_by_email_finds_existing_user(db_session):
    repo = UserRepository(session=db_session)
    await create_real_user(db_session, email="findme@example.com")

    found = await repo.get_by_email("findme@example.com")

    assert found is not None
    assert found.email == "findme@example.com"


async def test_get_by_email_returns_none_when_not_found(db_session):
    repo = UserRepository(session=db_session)

    found = await repo.get_by_email("nobody@example.com")

    assert found is None


async def test_user_email_uniqueness_is_enforced_by_database(db_session):
    repo = UserRepository(session=db_session)
    await create_real_user(db_session, email="duplicate@example.com")

    with pytest.raises(IntegrityError):
        await repo.create(
            id=uuid.uuid4(),
            username="another_username",
            email="duplicate@example.com",
            password=b"hash",
        )
        await db_session.commit()


async def test_user_username_uniqueness_is_enforced_by_database(db_session):
    repo = UserRepository(session=db_session)
    await create_real_user(db_session, username="taken_username")

    with pytest.raises(IntegrityError):
        await repo.create(
            id=uuid.uuid4(),
            username="taken_username",
            email="different@example.com",
            password=b"hash",
        )
        await db_session.commit()


async def test_track_artists_array_is_persisted_and_retrieved_correctly(db_session):
    repo = TrackRepository(session=db_session)
    owner = await create_real_user(db_session)
    await create_real_track(
        db_session, owner_id=owner.id, name="Array Test", artists=["A", "B", "C"]
    )

    found = await repo.get_one(owner_id=owner.id, name="Array Test")

    assert found is not None
    assert found.artists == ["A", "B", "C"]


async def test_get_track_by_owner_returns_track_for_correct_owner(db_session):
    repo = TrackRepository(session=db_session)
    owner = await create_real_user(db_session)
    other_owner = await create_real_user(
        db_session, username="other", email="other@example.com"
    )

    await create_real_track(db_session, owner_id=owner.id, name="Mine")
    await create_real_track(db_session, owner_id=other_owner.id, name="Not Mine")

    found = await repo.get_track_by_owner(owner.id)

    assert found is not None
    assert found.name == "Mine"


async def test_track_url_uniqueness_is_enforced_by_database(db_session):
    repo = TrackRepository(session=db_session)
    owner = await create_real_user(db_session)
    shared_url = f"track/{owner.id}/shared-key"

    await create_real_track(
        db_session, owner_id=owner.id, name="First", track_url=shared_url
    )

    with pytest.raises(IntegrityError):
        await repo.create(
            id=uuid.uuid4(),
            owner_id=owner.id,
            name="Second",
            artists=["x"],
            duration=1000,
            track_url=shared_url,
            photo_url=f"image/{owner.id}/{uuid.uuid4()}",
        )
        await db_session.commit()


async def test_track_owner_id_foreign_key_is_enforced(db_session):
    repo = TrackRepository(session=db_session)
    nonexistent_owner_id = uuid.uuid4()

    with pytest.raises(IntegrityError):
        await repo.create(
            id=uuid.uuid4(),
            owner_id=nonexistent_owner_id,
            name="Orphan Track",
            artists=["x"],
            duration=1000,
            track_url=f"track/{nonexistent_owner_id}/{uuid.uuid4()}",
            photo_url=f"image/{nonexistent_owner_id}/{uuid.uuid4()}",
        )
        await db_session.commit()


async def test_get_many_respects_skip_and_limit(db_session):
    repo = TrackRepository(session=db_session)
    owner = await create_real_user(db_session)

    for i in range(5):
        await create_real_track(db_session, owner_id=owner.id, name=f"Track {i}")

    page = await repo.get_many(owner_id=owner.id, skip=2, limit=2)

    assert len(page) == 2


async def test_grade_track_id_foreign_key_is_enforced(db_session):
    repo = GradeRepository(session=db_session)
    user = await create_real_user(db_session)
    nonexistent_track_id = uuid.uuid4()

    with pytest.raises(IntegrityError):
        await repo.create(
            id=uuid.uuid4(), user_id=user.id, track_id=nonexistent_track_id, grade=5
        )
        await db_session.commit()


async def test_get_one_finds_grade_by_user_and_track(db_session):
    repo = GradeRepository(session=db_session)
    user = await create_real_user(db_session)
    track_owner = await create_real_user(
        db_session, username="trackowner", email="owner@example.com"
    )
    track = await create_real_track(db_session, owner_id=track_owner.id)

    await create_real_grade(db_session, user_id=user.id, track_id=track.id, grade=9)

    found = await repo.get_one(user_id=user.id, track_id=track.id)

    assert found is not None
    assert found.grade == 9


async def test_profile_user_id_uniqueness_is_enforced(db_session):
    repo = ProfileRepository(session=db_session)
    user = await create_real_user(db_session)
    await create_real_profile(db_session, user_id=user.id)

    with pytest.raises(IntegrityError):
        await repo.create(
            id=uuid.uuid4(),
            user_id=user.id,
            birth_date=date(2000, 1, 1),
            bio="Duplicate profile attempt",
            country="Ukraine",
            phone_number="+380000000000",
        )
        await db_session.commit()


async def test_get_user_by_id_finds_profile_for_correct_user(db_session):
    repo = ProfileRepository(session=db_session)
    user = await create_real_user(db_session)
    await create_real_profile(db_session, user_id=user.id, bio="Real bio")

    found = await repo.get_user_by_id(user.id)

    assert found is not None
    assert found.bio == "Real bio"


async def test_get_aggregates_returns_correct_average_and_count(db_session):
    repo = GradeRepository(session=db_session)
    owner = await create_real_user(db_session)
    track = await create_real_track(db_session, owner_id=owner.id)

    rater_a = await create_real_user(
        db_session, username="rater_a", email="a@example.com"
    )
    rater_b = await create_real_user(
        db_session, username="rater_b", email="b@example.com"
    )
    rater_c = await create_real_user(
        db_session, username="rater_c", email="c@example.com"
    )
    await create_real_grade(db_session, user_id=rater_a.id, track_id=track.id, grade=8)
    await create_real_grade(db_session, user_id=rater_b.id, track_id=track.id, grade=9)
    await create_real_grade(db_session, user_id=rater_c.id, track_id=track.id, grade=10)

    aggregates = await repo.get_aggregates_by_track_ids([track.id])

    avg, count = aggregates[track.id]
    assert avg == 9.0
    assert count == 3


async def test_get_aggregates_groups_correctly_across_multiple_tracks(db_session):
    repo = GradeRepository(session=db_session)
    owner = await create_real_user(db_session)
    track_one = await create_real_track(db_session, owner_id=owner.id, name="Track One")
    track_two = await create_real_track(db_session, owner_id=owner.id, name="Track Two")

    rater = await create_real_user(db_session, username="rater", email="r@example.com")
    other_rater = await create_real_user(
        db_session, username="rater2", email="r2@example.com"
    )

    await create_real_grade(
        db_session, user_id=rater.id, track_id=track_one.id, grade=2
    )
    await create_real_grade(
        db_session, user_id=other_rater.id, track_id=track_one.id, grade=4
    )
    await create_real_grade(
        db_session, user_id=rater.id, track_id=track_two.id, grade=10
    )

    aggregates = await repo.get_aggregates_by_track_ids([track_one.id, track_two.id])

    assert aggregates[track_one.id] == (3.0, 2)
    assert aggregates[track_two.id] == (10.0, 1)


async def test_get_aggregates_omits_tracks_with_no_grades(db_session):
    repo = GradeRepository(session=db_session)
    owner = await create_real_user(db_session)
    ungraded_track = await create_real_track(db_session, owner_id=owner.id)

    aggregates = await repo.get_aggregates_by_track_ids([ungraded_track.id])

    assert ungraded_track.id not in aggregates


async def test_get_aggregates_returns_empty_dict_for_empty_input(db_session):
    repo = GradeRepository(session=db_session)

    aggregates = await repo.get_aggregates_by_track_ids([])

    assert aggregates == {}
