from enum import Enum


class ProfileMediaTypes(Enum):
    PHOTO_TYPES: frozenset[str] = frozenset({"image/jpeg", "image/png"})
