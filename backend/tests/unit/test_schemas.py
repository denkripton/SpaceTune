import pytest
from pydantic import ValidationError

from src.modules.auth.schemas.password.change import PasswordChangeSchema
from src.modules.auth.schemas.password.create import PasswordCreateSchema
from src.modules.auth.schemas.user.creation import UserCreateSchema
from src.modules.music.schemas.track.creation import TrackCreationSchema


def test_user_create_schema_accepts_valid_data():
    schema = UserCreateSchema(
        username="John Doe", email="johndoe@gmail.com", password="Som3Th!ng"
    )
    assert schema.username == "John Doe"
    assert schema.email == "johndoe@gmail.com"


def test_user_create_schema_rejects_invalid_email():
    with pytest.raises(ValidationError):
        UserCreateSchema(
            username="John Doe", email="not-an-email", password="Som3Th!ng"
        )


def test_user_create_schema_rejects_weak_password():
    with pytest.raises(ValidationError) as exc_info:
        UserCreateSchema(
            username="John Doe", email="johndoe@gmail.com", password="weak"
        )
    assert "password" in str(exc_info.value).lower()


def test_user_create_schema_rejects_username_longer_than_twenty_chars():
    with pytest.raises(ValidationError):
        UserCreateSchema(
            username="A" * 21, email="johndoe@gmail.com", password="Som3Th!ng"
        )


def test_user_create_schema_rejects_extra_unknown_fields():
    with pytest.raises(ValidationError):
        UserCreateSchema(
            username="John Doe",
            email="johndoe@gmail.com",
            password="Som3Th!ng",
            is_admin=True,
        )


def test_password_create_schema_accepts_matching_passwords():
    schema = PasswordCreateSchema(password="Som3Th!ng", confirm_password="Som3Th!ng")
    assert schema.password == "Som3Th!ng"


def test_password_create_schema_rejects_mismatched_confirmation():
    with pytest.raises(ValidationError) as exc_info:
        PasswordCreateSchema(password="Som3Th!ng", confirm_password="Different1!")
    assert "confirmation" in str(exc_info.value).lower()


def test_password_create_schema_rejects_weak_password():
    with pytest.raises(ValidationError):
        PasswordCreateSchema(password="weak", confirm_password="weak")


def test_password_change_schema_accepts_valid_distinct_passwords():
    schema = PasswordChangeSchema(
        password="OldPass1!",
        new_password="NewPass1!",
        confirm_password="NewPass1!",
    )
    assert schema.new_password == "NewPass1!"


def test_password_change_schema_rejects_new_password_same_as_old():

    with pytest.raises(ValidationError) as exc_info:
        PasswordChangeSchema(
            password="SamePass1!",
            new_password="SamePass1!",
            confirm_password="SamePass1!",
        )
    assert "different" in str(exc_info.value).lower()


def test_password_change_schema_rejects_mismatched_confirmation():
    with pytest.raises(ValidationError) as exc_info:
        PasswordChangeSchema(
            password="OldPass1!",
            new_password="NewPass1!",
            confirm_password="TotallyDifferent1!",
        )
    assert "confirmation" in str(exc_info.value).lower()


def test_password_change_schema_rejects_weak_new_password():
    with pytest.raises(ValidationError):
        PasswordChangeSchema(
            password="OldPass1!", new_password="weak", confirm_password="weak"
        )


def test_track_creation_schema_accepts_valid_data():
    schema = TrackCreationSchema(name="My Track", artists=["Co-Artist"])
    assert schema.name == "My Track"
    assert schema.artists == ["Co-Artist"]


def test_track_creation_schema_uses_default_name_when_omitted():
    schema = TrackCreationSchema(artists=[])
    assert schema.name == "About Life"


def test_track_creation_schema_rejects_name_longer_than_fifty_chars():
    with pytest.raises(ValidationError):
        TrackCreationSchema(name="A" * 51, artists=[])


def test_track_creation_schema_rejects_empty_name():
    with pytest.raises(ValidationError):
        TrackCreationSchema(name="", artists=[])


@pytest.mark.parametrize(
    ("raw_artists", "expected"),
    [
        (None, []),
        ("", []),
        ([], []),
        (["Alice", "Bob"], ["Alice", "Bob"]),
        (["Alice", "", "  ", "Bob"], ["Alice", "Bob"]),
        (["", None], []),
    ],
)
def test_track_creation_schema_cleans_artists_field(raw_artists, expected):
    schema = TrackCreationSchema(artists=raw_artists)
    assert schema.artists == expected
