from enum import Enum

class MediaTypes(Enum):
    AUDIO_TYPES: frozenset[str] = frozenset({"audio/mpeg"})
    IMAGE_TYPES: frozenset[str] = frozenset({"image/jpeg", "image/png"})