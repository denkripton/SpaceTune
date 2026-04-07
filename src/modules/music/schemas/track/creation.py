from pydantic import Field

from src.utils.schemas.base_schema import BaseSchema


class TrackCreationSchema(BaseSchema):
    name: str = Field(min_length=1, max_length=50, default="About Life")
    artists: list[str]
