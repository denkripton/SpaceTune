from pydantic import BaseModel, Field


class TrackCreationSchema(BaseModel):
    name: str = Field(min_length=1, max_length=50, default="baobab")
    artists: list[str]
