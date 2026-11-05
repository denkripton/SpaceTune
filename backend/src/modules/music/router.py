import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile

from src.modules.auth.dependencies import get_current_user_obj
from src.modules.auth.models import User
from src.modules.auth.schemas.exceptions.user_401 import User401
from src.modules.auth.schemas.exceptions.user_404 import User404
from src.modules.music.dependencies import get_track_service
from src.modules.music.schemas.exceptions.track_404 import Track404
from src.modules.music.schemas.exceptions.track_409 import Track409
from src.modules.music.schemas.exceptions.track_413 import Track413
from src.modules.music.schemas.track.creation import TrackCreationSchema
from src.modules.music.schemas.track.metadata import TrackMetadataReadShema
from src.modules.music.schemas.track.read import TrackReadSchema
from src.modules.music.service import TrackService
from src.utils.routing.error_handling import ErrorHandlingRoute

music_router = APIRouter(prefix="/music", route_class=ErrorHandlingRoute)


@music_router.get(
    "/track/{track_id}",
    summary="Get track",
    tags=["Track CRUD's"],
    description="Get track with metadata",
    response_model=TrackMetadataReadShema,
    responses={
        404: {"model": Track404},
    },
)
async def track_get(
    track_id: uuid.UUID, service: TrackService = Depends(get_track_service)
):
    return await service.get_track(track_id=track_id)


@music_router.get(
    "/tracks/my",
    summary="Get your tracks (Protected)",
    tags=["Track CRUD's"],
    description="Get your tracks with their metadata",
    response_model=list[TrackMetadataReadShema],
    responses={
        401: {"model": User401},
    },
)
async def my_tracks_get(
    user: User = Depends(get_current_user_obj),
    service: TrackService = Depends(get_track_service),
):
    return await service.get_my_tracks(user=user)


@music_router.post(
    "/track/add",
    summary="Create track (Protected)",
    tags=["Track CRUD's"],
    description="Create track",
    response_model=TrackReadSchema,
    responses={
        401: {"model": User401},
        404: {"model": User404},
        409: {"model": Track409},
        413: {"model": Track413},
    },
)
async def add_track(
    name: str = Form(),
    artists: list = Form(default=[]),
    music_file: UploadFile = File(),
    image_file: UploadFile = File(),
    user: User = Depends(get_current_user_obj),
    service: TrackService = Depends(get_track_service),
):
    data = TrackCreationSchema(name=name, artists=artists)
    return await service.create_track(
        user=user,
        data=data,
        music_file=music_file,
        image_file=image_file,
    )


@music_router.delete(
    "/track/{track_id}/delete",
    summary="Delete track (Protected)",
    tags=["Track CRUD's"],
    description="Delete your track",
    responses={
        401: {"model": User401},
        404: {"model": User404 | Track404},
    },
)
async def track_delete(
    track_id: uuid.UUID,
    user: User = Depends(get_current_user_obj),
    service: TrackService = Depends(get_track_service),
):
    return await service.delete_track(user=user, track_id=track_id)
