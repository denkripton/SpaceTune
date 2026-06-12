from typing import Union

from fastapi import APIRouter, Depends, Response
from fastapi.responses import RedirectResponse

from src.dependencies import get_error
from src.modules.auth import get_current_user, get_oauth_service, get_user_service
from src.modules.auth.schemas.auth.read import AuthReadSchema
from src.modules.auth.schemas.exceptions.password_403 import Password403
from src.modules.auth.schemas.exceptions.user_401 import User401
from src.modules.auth.schemas.exceptions.user_422 import User422
from src.modules.auth.schemas.user.creation import UserCreateSchema
from src.modules.auth.schemas.user.login import UserLoginSchema
from src.modules.auth.schemas.user.read import UserRead
from src.modules.auth.services import OAuthService, UserService
from src.modules.profile.schemas.read import ProfileReadSchema

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
    "/oauth/google",
    summary="Google OAuth redirect",
    tags=["Authentication"],
    description="Redirect to Google login page",
)
async def google_login(service: OAuthService = Depends(get_oauth_service)):
    url = service.get_redirect_url()
    return RedirectResponse(url=url)


@user_router.get(
    "/oauth/google/callback",
    summary="Google OAuth callback",
    tags=["Authentication"],
    description="Handle Google OAuth callback",
    response_model=AuthReadSchema,
    responses={
        422: {"model": User422},
    },
)
async def google_callback(
    code: str, response: Response, service: OAuthService = Depends(get_oauth_service)
):
    user = await get_error(service.login, code=code)

    response.set_cookie(
        key="refresh_token",
        value=user["refresh"],
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )

    return user


@user_router.delete(
    "/logout",
    summary="Quit your account",
    tags=["Authentication"],
    description="Logout user",
)
async def logout_user(response: Response):
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=True,
        samesite="lax",
    )
    return {"message": "Loged out successfully"}


@user_router.patch(
    "/me/update",
    summary="Update username (Protected)",
    tags=["Profile CRUD's"],
    description="Change your username",
    response_model=Union[ProfileReadSchema, UserRead],
    responses={
        401: {"model": User401},
        403: {"model": Password403},
        422: {"model": User422},
    },
)
async def update_me(
    new_username: str,
    user_id: str = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    return await get_error(
        service.update_username, user_id=user_id, new_username=new_username
    )
