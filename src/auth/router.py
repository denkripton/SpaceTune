from fastapi import APIRouter, Depends, Response
from src.auth.dependencies import get_user_service, get_current_user
from src.auth.service import UserService
from src.auth.schemas import (
    UserCreateSchema,
    UserLoginSchema,
    ProfileCreationSchema,
    UserProfileReadSchema,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register")
async def register_user(
    data: UserCreateSchema,
    service: UserService = Depends(get_user_service),
):
    return await service.register(data)


@router.post("/login")
async def login_user(
    data: UserLoginSchema, response: Response, service: UserService = Depends(get_user_service)
):
    user = await service.login(data)
    
    response.set_cookie(
            key="refresh_token",
            value=user["refresh"],
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=60 * 60 * 24 * 30,
        )

    return user


@router.post("/me/profile/create")
async def create_my_profile(
    data: ProfileCreationSchema,
    service: UserService = Depends(get_user_service),
    user_id: str = Depends(get_current_user),
):
    return await service.create_profile(user_id=user_id, data=data)


@router.get("/me/profile", response_model=UserProfileReadSchema)
async def get_my_profile(
    user_id: str = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    return await service.get_my_profile(user_id=user_id)


@router.get("/{username}/profile", response_model=UserProfileReadSchema)
async def get_user_profile(
    username: str, service: UserService = Depends(get_user_service)
):
    return await service.get_user_profile(username=username)
