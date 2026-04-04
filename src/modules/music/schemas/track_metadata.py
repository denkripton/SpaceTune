from src.utils.schemas.base_schema import BaseSchema
from src.modules.music.schemas.track_read import TrackReadSchema


class TrackMetadataReadShema(BaseSchema):
    metadata: TrackReadSchema
    audio: str
    image: str
