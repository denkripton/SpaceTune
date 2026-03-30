from typing import Union

from fastapi import APIRouter, Depends, Response

from src.dependencies import get_error
from src.modules.auth.dependencies import get_user_service, get_current_user
from src.modules.auth.service import UserService

from src.modules.auth.schemas.profile.profile_creation import ProfileCreationSchema
from src.modules.auth.schemas.user.user_read import UserRead
from src.modules.auth.schemas.profile.profile_read import UserProfileReadSchema
from src.modules.auth.schemas.user.user_login import UserLoginSchema
from src.modules.auth.schemas.user.user_creation import UserCreateSchema
from src.modules.auth.schemas.user.user_update import UserUpdateSchema
from src.modules.auth.schemas.user.auth_read import AuthReadSchema

from src.modules.auth.schemas.exceptions.user_401 import User401
from src.modules.auth.schemas.exceptions.password_403 import Password403
from src.modules.auth.schemas.exceptions.user_422 import User422
from src.modules.auth.schemas.exceptions.profile_422 import Profile422

user_router = APIRouter(prefix="/users")


@user_router.post(
    "/register",
    summary="Registration",
    tags=["User CRUD's"],
    description="Registrate user",
    response_model=UserRead,
    responses={
        422: {"model": User422},
    },
)
async def register_user(
    data: UserCreateSchema,
    service: UserService = Depends(get_user_service),
):
    return await get_error(service.register, data=data)


@user_router.post(
    "/login",
    summary="Authenticate",
    tags=["Authentication"],
    description="Login user",
    response_model=AuthReadSchema,
    responses={
        403: {"model": Password403},
        422: {"model": User422},
    },
)
async def login_user(
    data: UserLoginSchema,
    response: Response,
    service: UserService = Depends(get_user_service),
):
    user = await get_error(service.login, data=data)

    response.set_cookie(
        key="refresh_token",
        value=user["refresh"],
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )

    return user


@user_router.post(
    "/me/profile/create",
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
    service: UserService = Depends(get_user_service),
    user_id: str = Depends(get_current_user),
):
    return await get_error(service.create_profile, user_id=user_id, data=data)


@user_router.get(
    "/me/profile",
    summary="Read your profile (Protected)",
    tags=["Profile CRUD's"],
    description="Get your profile",
    response_model=Union[UserProfileReadSchema, UserRead],
    responses={
        401: {"model": User401},
        422: {"model": User422},
    },
)
async def get_my_profile(
    user_id: str = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    return await get_error(service.get_my_profile, user_id=user_id)


@user_router.get(
    "/{username}/profile",
    summary="Read user profile",
    tags=["Profile CRUD's"],
    description="Get user profile",
    response_model=Union[UserProfileReadSchema, UserRead],
    responses={
        422: {"model": User422},
    },
)
async def get_user_profile(
    username: str, service: UserService = Depends(get_user_service)
):
    return await get_error(service.get_user_profile, username=username)


@user_router.patch(
    "/me/update",
    summary="Update username (Protected)",
    tags=["Profile CRUD's"],
    description="Change your username",
    response_model=Union[UserProfileReadSchema, UserRead],
    responses={
        401: {"model": User401},
        403: {"model": Password403},
        422: {"model": User422},
    },
)
async def update_me(
    data: UserUpdateSchema,
    user_id: str = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    return await get_error(service.update_username, user_id=user_id, data=data)


@user_router.delete(
    "/me/profile/delete",
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
    service: UserService = Depends(get_user_service),
):
    return await get_error(service.delete_profile, user_id=user_id, password=password)
