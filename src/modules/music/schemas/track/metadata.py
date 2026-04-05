from src.utils.schemas.base_schema import BaseSchema
from src.modules.music.schemas.track.read import TrackReadSchema
from src.modules.music.schemas.track.media import MediaURLsSchema


class TrackMetadataReadShema(BaseSchema):
    metadata: TrackReadSchema
    media: MediaURLsSchema