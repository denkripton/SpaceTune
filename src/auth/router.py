from fastapi import APIRouter, Depends
from src.auth.dependencies import get_user_service, get_auth_service, get_current_user
from src.auth.service import UserService
from src.auth.schemas import UserCreateSchema, UserLoginSchema

router = APIRouter(prefix="/users")


@router.post("/register")
async def register_user(
    data: UserCreateSchema,
    service: UserService = Depends(get_user_service),
):
    return await service.register(data)


@router.post("/login")
async def login_user(
    data: UserLoginSchema, service: UserService = Depends(get_auth_service)
):
    return await service.login(data)


@router.get("/profile")
async def profile(user_id: str = Depends(get_current_user)):
    return {"user_id": user_id}
