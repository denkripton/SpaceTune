from enum import Enum


class FieldsVisibility(Enum):
    VISIBILITY_TOGGLEABLE_FIELDS = frozenset(
        {"email", "phone_number", "birth_date", "bio", "country"}
    )
    DEFAULT_VISIBLE_FIELDS = {
        "email": False,
        "phone_number": False,
        "birth_date": False,
        "bio": True,
        "country": True,
    }
