import os
import tempfile

import ffmpeg

from src.modules.music.utils.enums import FileSizeLimit
from src.utils.exceptions import ServiceError

_CHUNK_SIZE = 1024 * 1024


async def count_duration(file):
    total_read = 0
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=os.path.splitext(file.filename)[1]
    ) as tmp:
        tmp_path = tmp.name

        try:
            while True:
                chunk = await file.read(_CHUNK_SIZE)
                if not chunk:
                    break

                total_read += len(chunk)
                if total_read > FileSizeLimit.MAX_AUDIO_SIZE.value:
                    tmp.close()
                    raise ServiceError(code=422, msg="Audio file exceeds size limit")

                tmp.write(chunk)

            tmp.close()

            probe = ffmpeg.probe(tmp_path)
            return float(probe["format"]["duration"]) * 1000

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            await file.seek(0)
