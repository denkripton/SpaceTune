import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from src.modules.auth.models import User
from src.modules.grades.models import Grade
from src.modules.music.models import Track
from src.modules.profile.models import Profile
from src.utils import UnitOfWork


def make_fake_user(
    user_id=None,
    username="denkripton",
    email="denkripton@example.com",
    password=b"$2b$12$fakefakefakefakefakefakefakefakefake",
    google_id=None,
    photo_url=None,
):
    user = MagicMock()
    user.id = user_id or uuid.uuid4()
    user.username = username
    user.email = email
    user.password = password
    user.google_id = google_id
    user.photo_url = photo_url
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
    visible_fields=None,
):
    from src.modules.profile.utils.enums import FieldsVisibility

    profile = MagicMock()
    profile.id = profile_id or uuid.uuid4()
    profile.user_id = user_id or uuid.uuid4()
    profile.birth_date = birth_date or datetime(2000, 1, 1).date()
    profile.bio = bio
    profile.country = country
    profile.phone_number = phone_number
    profile.visible_fields = (
        dict(visible_fields)
        if visible_fields is not None
        else dict(FieldsVisibility.DEFAULT_VISIBLE_FIELDS.value)
    )
    return profile


def make_fake_bucket_manager(**overrides) -> MagicMock:
    fake = MagicMock()
    fake.upload_file = AsyncMock(return_value=None)
    fake.delete_file = AsyncMock(return_value=None)
    fake.list_objects = AsyncMock(return_value=[])
    fake.presigned_url = MagicMock(return_value="https://fake-presigned-url")

    for attr, value in overrides.items():
        setattr(fake, attr, value)

    return fake


def make_async_repo_session():
    session = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    return session


def make_fake_uow(session=None) -> "UnitOfWork":
    return UnitOfWork(session or make_async_repo_session())


async def create_real_user(
    session,
    username="denkripton",
    email="denkripton@example.com",
    password=b"$2b$12$fakefakefakefakefakefakefakefakefake",
    google_id=None,
):
    user = User(
        id=uuid.uuid4(),
        username=username,
        email=email,
        password=password,
        google_id=google_id,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def create_real_track(
    session,
    owner_id,
    name="About Life",
    artists=None,
    duration=180_000,
    track_url=None,
    photo_url=None,
):
    track = Track(
        id=uuid.uuid4(),
        owner_id=owner_id,
        name=name,
        artists=artists if artists is not None else ["denkripton"],
        duration=duration,
        track_url=track_url or f"track/{owner_id}/{uuid.uuid4()}",
        photo_url=photo_url or f"image/{owner_id}/{uuid.uuid4()}",
    )
    session.add(track)
    await session.commit()
    await session.refresh(track)
    return track


async def create_real_grade(session, user_id, track_id, grade=8):
    obj = Grade(id=uuid.uuid4(), user_id=user_id, track_id=track_id, grade=grade)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def create_real_profile(
    session,
    user_id,
    birth_date=None,
    bio="bio",
    country="Ukraine",
    phone_number="+380999999999",
):
    profile = Profile(
        id=uuid.uuid4(),
        user_id=user_id,
        birth_date=birth_date or date(2000, 1, 1),
        bio=bio,
        country=country,
        phone_number=phone_number,
    )
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return profile
