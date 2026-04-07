from src.utils.schemas.base_schema import BaseSchema


class MediaURLsSchema(BaseSchema):
    audio: str
    image: str
