from enum import Enum

class FileSizeLimit(Enum):
    MAX_AUDIO_SIZE = 50 * 1024 * 1024
    MAX_IMAGE_SIZE = 20 * 1024 * 1024