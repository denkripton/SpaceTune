from fastapi import APIRouter, Depends
from src.auth.dependencies import get_user_service
from src.auth.service import UserService
from src.auth.schemas import UserCreate

router = APIRouter(prefix="/user")


@router.post("/register")
async def register_user(
    data: UserCreate,
    service: UserService = Depends(get_user_service),
):
    return await service.register(data)
