from typing import Union

from fastapi import APIRouter, Depends

from src.dependencies import get_error
from src.modules.profile.dependencies import get_profile_service
from src.modules.auth.dependencies import get_current_user
from src.modules.profile.service import ProfileService

from src.modules.profile.schemas.creation import ProfileCreationSchema
from src.modules.profile.schemas.read import ProfileReadSchema

from src.modules.auth.schemas.user.read import UserRead

from src.modules.auth.schemas.exceptions.user_401 import User401
from src.modules.auth.schemas.exceptions.password_403 import Password403
from src.modules.auth.schemas.exceptions.user_422 import User422
from src.modules.profile.schemas.exceptions.profile_422 import Profile422


profile_router = APIRouter(prefix="/profile")


@profile_router.post(
    "/me/create",
    summary="Profile creation (Protected)",
    tags=["Profile CRUD's"],
    description="Create your profile",
    response_model=ProfileCreationSchema,
    responses={
        401: {"model": User401},
        403: {"model": Password403},
        422: {"model": Union[Profile422, User422]},
    },
)
async def create_my_profile(
    data: ProfileCreationSchema,
    service: ProfileService = Depends(get_profile_service),
    user_id: str = Depends(get_current_user),
):
    return await get_error(service.create_profile, user_id=user_id, data=data)


@profile_router.get(
    "/me",
    summary="Read your profile (Protected)",
    tags=["Profile CRUD's"],
    description="Get your profile",
    response_model=Union[ProfileReadSchema, UserRead],
    responses={
        401: {"model": User401},
        422: {"model": User422},
    },
)
async def get_my_profile(
    user_id: str = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    return await get_error(service.get_my_profile, user_id=user_id)


@profile_router.get(
    "/{username}",
    summary="Read user profile",
    tags=["Profile CRUD's"],
    description="Get user profile",
    response_model=Union[ProfileReadSchema, UserRead],
    responses={
        422: {"model": User422},
    },
)
async def get_user_profile(
    username: str, service: ProfileService = Depends(get_profile_service)
):
    return await get_error(service.get_user_profile, username=username)


@profile_router.delete(
    "/me/delete",
    summary="Delete profile (Protected)",
    tags=["Profile CRUD's"],
    description="Delete your profile",
    responses={
        401: {"model": User401},
        403: {"model": Password403},
        422: {"model": Union[Profile422, User422]},
    },
)
async def delete_my_profile(
    password: str,
    user_id: str = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    return await get_error(service.delete_profile, user_id=user_id, password=password)
