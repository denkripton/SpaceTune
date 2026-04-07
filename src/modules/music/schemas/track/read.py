import uuid
from datetime import date

from pydantic import Field

from src.modules.music.schemas.track.creation import TrackCreationSchema


class TrackReadSchema(TrackCreationSchema):
    id: uuid.UUID
    duration: int
    grades: float = Field(default=0)
    released: date
