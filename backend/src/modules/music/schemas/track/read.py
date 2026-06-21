import uuid
from datetime import date

from pydantic import Field

from src.modules.music.schemas.track.creation import TrackCreationSchema


class TrackReadSchema(TrackCreationSchema):
    id: uuid.UUID
    duration: int
    average_grade: float = Field(default=0)
    number_of_ratings: int = Field(default=0)
    released: date
