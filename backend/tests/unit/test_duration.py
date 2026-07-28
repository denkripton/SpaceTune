from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.music.utils.enums import FileSizeLimit
from src.modules.music.utils.duration import count_duration
from src.utils.exceptions import ServiceError


def make_streaming_file(total_bytes: int, chunk_size: int = 1024 * 1024):
    """Simulates UploadFile.read(n) yielding fixed-size chunks until exhausted."""
    remaining = total_bytes
    file = MagicMock()
    file.filename = "track.mp3"

    async def fake_read(n=-1):
        nonlocal remaining
        if remaining <= 0:
            return b""
        take = min(n, remaining) if n > 0 else remaining
        remaining -= take
        return b"\x00" * take

    file.read = AsyncMock(side_effect=fake_read)
    file.seek = AsyncMock()
    return file


async def test_count_duration_raises_422_when_stream_exceeds_limit():
    file = make_streaming_file(total_bytes=FileSizeLimit.MAX_AUDIO_SIZE.value + (1024 * 1024))

    with pytest.raises(ServiceError) as exc_info:
        await count_duration(file=file)

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Audio file exceeds size limit"


async def test_count_duration_stops_reading_once_limit_exceeded():
    file = make_streaming_file(total_bytes=FileSizeLimit.MAX_AUDIO_SIZE.value * 3)

    with pytest.raises(ServiceError):
        await count_duration(file=file)

    max_possible_calls = (FileSizeLimit.MAX_AUDIO_SIZE.value // (1024 * 1024)) + 2
    assert file.read.await_count <= max_possible_calls


async def test_count_duration_succeeds_for_file_within_limit():
    file = make_streaming_file(total_bytes=1024 * 1024)

    with patch("src.modules.music.utils.duration.ffmpeg") as fake_ffmpeg:
        fake_ffmpeg.probe.return_value = {"format": {"duration": "180.5"}}
        duration_ms = await count_duration(file=file)

    assert duration_ms == 180_500.0
    file.seek.assert_awaited_once_with(0)


async def test_count_duration_cleans_up_temp_file_on_size_violation():
    file = make_streaming_file(total_bytes=FileSizeLimit.MAX_AUDIO_SIZE.value + 1)

    with patch("src.modules.music.utils.duration.os.unlink") as fake_unlink:
        with pytest.raises(ServiceError):
            await count_duration(file=file)
        fake_unlink.assert_called_once()