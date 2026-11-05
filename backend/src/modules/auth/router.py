from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse

from src.modules.auth import get_oauth_service, get_token_service, get_user_service
from src.modules.auth.dependencies import get_current_user_obj
from src.modules.auth.models import User
from src.modules.auth.schemas.auth.read import AuthReadSchema
from src.modules.auth.schemas.auth.refresh_read import TokenRefreshReadSchema
from src.modules.auth.schemas.exceptions.password_403 import Password403
from src.modules.auth.schemas.exceptions.user_401 import User401
from src.modules.auth.schemas.exceptions.user_404 import User404
from src.modules.auth.schemas.exceptions.user_409 import User409
from src.modules.auth.schemas.password import PasswordChangeSchema, PasswordCreateSchema
from src.modules.auth.schemas.user.creation import UserCreateSchema
from src.modules.auth.schemas.user.login import UserLoginSchema
from src.modules.auth.schemas.user.read import UserRead
from src.modules.auth.services import OAuthService, TokenService, UserService
from src.utils.exceptions import UnauthorizedError
from src.utils.routing.error_handling import ErrorHandlingRoute

user_router = APIRouter(prefix="/users", route_class=ErrorHandlingRoute)


@user_router.post(
    "/register",
    summary="Registration",
    tags=["User CRUD's"],
    description="Registrate user",
    response_model=UserRead,
    responses={
        409: {"model": User409},
    },
)
async def register_user(
    data: UserCreateSchema,
    service: UserService = Depends(get_user_service),
):
    return await service.register(data=data)


@user_router.post(
    "/login",
    summary="Authenticate",
    tags=["Authentication"],
    description="Login user",
    response_model=AuthReadSchema,
    responses={
        403: {"model": Password403},
    },
)
async def login_user(
    data: UserLoginSchema,
    response: Response,
    service: UserService = Depends(get_user_service),
):
    user = await service.login(data=data)

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
    "/refresh",
    summary="Refresh access token",
    tags=["Authentication"],
    description="Exchange a valid refresh token cookie for a new access token",
    response_model=TokenRefreshReadSchema,
    responses={
        401: {"model": User401},
    },
)
async def refresh_token(
    request: Request,
    service: TokenService = Depends(get_token_service),
):
    refresh_token_value = request.cookies.get("refresh_token")

    if refresh_token_value is None:
        raise UnauthorizedError(msg="Refresh token is missing")

    access = service.refresh_access_token(refresh_token=refresh_token_value)

    return {"access": access}


@user_router.get(
    "/oauth/google",
    summary="Google OAuth redirect",
    tags=["Authentication"],
    description="Redirect to Google login page",
)
async def google_login(
    response: Response, service: OAuthService = Depends(get_oauth_service)
):
    state = service.generate_state()
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=600,
    )
    url = service.get_redirect_url(state=state)
    return RedirectResponse(url=url, headers=response.headers)


@user_router.get(
    "/oauth/google/callback",
    summary="Google OAuth callback",
    tags=["Authentication"],
    description="Handle Google OAuth callback",
    response_model=AuthReadSchema,
    responses={
        400: {"description": "Invalid OAuth state or missing profile data"},
        422: {"description": "Email not verified or invalid OAuth response"},
        502: {"description": "Failed to reach Google"},
    },
)
async def google_callback(
    code: str,
    state: str,
    request: Request,
    response: Response,
    service: OAuthService = Depends(get_oauth_service),
):
    user = await service.login(
        code=code,
        state=state,
        expected_state=request.cookies.get("oauth_state"),
    )

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


@user_router.post(
    "/password/add",
    summary="Set Password",
    tags=["User CRUD's"],
    description="Set your password",
    responses={
        401: {"model": User401},
        404: {"model": User404},
        409: {"model": User409},
    },
)
async def add_password(
    data: PasswordCreateSchema,
    user: User = Depends(get_current_user_obj),
    service: UserService = Depends(get_user_service),
):
    return await service.set_password(user=user, data=data)


@user_router.put(
    "/password/change",
    summary="Change Password",
    tags=["User CRUD's"],
    description="Change existing password",
    responses={
        401: {"model": User401},
        403: {"model": Password403},
        404: {"model": User404},
    },
)
async def change_password(
    data: PasswordChangeSchema,
    user: User = Depends(get_current_user_obj),
    service: UserService = Depends(get_user_service),
):
    return await service.change_password(user=user, data=data)
