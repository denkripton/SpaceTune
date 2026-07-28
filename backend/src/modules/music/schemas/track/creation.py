from typing import List

from pydantic import Field, field_validator

from src.utils.schemas.base_schema import BaseSchema


class TrackCreationSchema(BaseSchema):
    name: str = Field(min_length=1, max_length=50, default="About Life")
    artists: List[str] = Field(default=[])

    @field_validator("artists", mode="before")
    @classmethod
    def clean_artists(cls, value):
        if value is None or value == "":
            return []
        result = []
        for artist in value:
            if artist and str(artist).strip():
                result.append(artist)
        return result