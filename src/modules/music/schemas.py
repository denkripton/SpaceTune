from fastapi import UploadFile
from pydantic import BaseModel, field_validator, Field
from datetime import date
from typing import Optional
import uuid


class TrackCreationSchema(BaseModel):
    name: str = Field(min_length=1, max_length=50, default="baobab")
    artists: list[str]
    


class TrackReadSchema(TrackCreationSchema):
    id: uuid.UUID
    duration: int

