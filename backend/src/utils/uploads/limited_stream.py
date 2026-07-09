from src.utils.exceptions import FileSizeLimitExceeded


class SizeLimitedStream:
    def __init__(self, wrapped, max_bytes: int):
        self._wrapped = wrapped
        self._max_bytes = max_bytes
        self._total_read = 0

    def read(self, size=-1):
        chunk = self._wrapped.read(size)
        self._total_read += len(chunk)
        if self._total_read > self._max_bytes:
            raise FileSizeLimitExceeded(
                f"Stream exceeded {self._max_bytes} bytes"
            )
        return chunk