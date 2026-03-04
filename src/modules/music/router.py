from fastapi import APIRouter, Depends, Response, UploadFile, Form, File
from typing import Union, Annotated, List

from src.modules.music.service import TrackService
from src.modules.music.dependencies import get_track_service
from src.modules.auth.dependencies import get_current_user
from src.modules.music.schemas import TrackCreationSchema, TrackReadSchema, TrackMetadataReadShema

music_router = APIRouter(prefix="/music", tags=["Music"])


@music_router.get("/track/{track_name}", response_model=TrackMetadataReadShema)
async def track_get(
    track_name: str, service: TrackService = Depends(get_track_service)
):
    return await service.get_track(track_name=track_name)


@music_router.get("/tracks/my", response_model=list[TrackMetadataReadShema])
async def my_tracks_get(
    user_id: str = Depends(get_current_user), service: TrackService = Depends(get_track_service)
):
    return await service.get_my_tracks(user_id=user_id)


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


@music_router.delete("/track/delete")
async def track_delete(
    track_name: str,
    password: str,
    user_id: str = Depends(get_current_user),
    service: TrackService = Depends(get_track_service),
):
    return await service.delete_track(
        user_id=user_id, password=password, track_name=track_name
    )
