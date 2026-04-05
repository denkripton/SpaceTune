import uuid

from pydantic import Field

from src.modules.music.schemas.track.creation import TrackCreationSchema


class TrackReadSchema(TrackCreationSchema):
    id: uuid.UUID
    duration: int
    grades: float = Field(default=0)
