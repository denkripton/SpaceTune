from pydantic import BaseModel

from src.modules.music.schemas.track_read import TrackReadSchema


class TrackMetadataReadShema(BaseModel):
    metadata: TrackReadSchema
    audio: str
    image: str
