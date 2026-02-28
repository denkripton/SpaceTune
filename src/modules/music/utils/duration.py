import ffmpeg
import tempfile
import os

async def count_duration(file):
    readed_file = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        tmp.write(readed_file)
        tmp_path = tmp.name
    try:
        probe = ffmpeg.probe(tmp_path)
        return int(float(probe["format"]["duration"])) * 1000
    finally:
        os.unlink(tmp_path)