from typing import Union, List

from fastapi import APIRouter, Depends, UploadFile, Form, File

from src.modules.music.service import TrackService
from src.modules.music.dependencies import get_track_service
from src.dependencies import get_error
from src.modules.auth.dependencies import get_current_user

from src.modules.music.schemas.track.read import TrackReadSchema
from src.modules.music.schemas.track.metadata import TrackMetadataReadShema
from src.modules.music.schemas.track.creation import TrackCreationSchema

from src.modules.music.schemas.exceptions.track_422 import Track422
from src.modules.auth.schemas.exceptions.user_401 import User401
from src.modules.auth.schemas.exceptions.user_422 import User422

music_router = APIRouter(prefix="/music")


@music_router.get(
    "/track/{track_id}",
    summary="Get track",
    tags=["Track CRUD's"],
    description="Get track with metadata",
    response_model=TrackMetadataReadShema,
    responses={422: {"model": Track422}},
)
async def track_get(
    track_id: str, service: TrackService = Depends(get_track_service)
):
    return await get_error(service.get_track, track_id=track_id)


@music_router.get(
    "/tracks/my",
    summary="Get tracks (Protected)",
    tags=["Track CRUD's"],
    description="Get your tracks with their metadata",
    response_model=list[TrackMetadataReadShema],
    responses={
        401: {"model": User401},
    },
)
async def my_tracks_get(
    user_id: str = Depends(get_current_user),
    service: TrackService = Depends(get_track_service),
):
    return await get_error(service.get_my_tracks, user_id=user_id)


@music_router.post(
    "/track/add",
    summary="Create track (Protected)",
    tags=["Track CRUD's"],
    description="Create track",
    response_model=TrackReadSchema,
    responses={401: {"model": User401}, 422: {"model": Union[Track422, User422]}},
)
async def add_track(
    name: str = Form(),
    artists: List = Form(default=[]),
    music_file: UploadFile = File(),
    image_file: UploadFile = File(),
    user_id: str = Depends(get_current_user),
    service: TrackService = Depends(get_track_service),
):
    data = TrackCreationSchema(name=name, artists=artists)
    return await get_error(
        service.create_track,
        user_id=user_id,
        data=data,
        music_file=music_file,
        image_file=image_file,
    )


@music_router.delete(
    "/track/delete",
    summary="Delete track (Protected)",
    tags=["Track CRUD's"],
    description="Delete your track",
    responses={
        401: {"model": User401},
        422: {"model": Union[Track422, User422]},
    },
)
async def track_delete(
    track_name: str,
    user_id: str = Depends(get_current_user),
    service: TrackService = Depends(get_track_service),
):
    return await get_error(
        service.delete_track, user_id=user_id, track_name=track_name
    )
