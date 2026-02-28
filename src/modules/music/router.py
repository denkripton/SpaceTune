from fastapi import APIRouter, Depends, Response, UploadFile, Form, File
from typing import Union, Annotated

from src.modules.music.service import TrackService
from src.modules.music.dependencies import get_track_service
from src.modules.auth.dependencies import get_current_user
from src.modules.music.schemas import TrackCreationSchema, TrackReadSchema

music_router = APIRouter(prefix="/music", tags=["Music"])


@music_router.post("/track/add", response_model=TrackReadSchema)
async def add_track(
    name: str = Form(),
    artists: list[str] = Form(),
    music_file: UploadFile = File(),
    image_file: UploadFile = File(),
    user_id: str = Depends(get_current_user),
    service: TrackService = Depends(get_track_service),
):
    data = TrackCreationSchema(name=name, artists=artists)
    return await service.create_track(
        user_id=user_id, data=data, music_file=music_file, image_file=image_file
    )
