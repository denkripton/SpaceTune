from fastapi import APIRouter, Depends
from src.auth import schemas
from src.auth import service
from sqlalchemy.ext.asyncio import AsyncSession
from src.dependencies import get_session

router = APIRouter()


@router.post("/user", response_model=schemas.UserReadSchema)
async def reqistration(user_creds: schemas.UsersCreationSchema, db: AsyncSession = Depends(get_session)):
    return await service.create_user(creds=user_creds, session=db)


@router.post("/user/profile", response_model=schemas.ProfileCreationSchema)
async def profile_creation(username: str, profile_params: schemas.ProfileCreationSchema, db: AsyncSession = Depends(get_session)):
    return await service.create_profile(user=username, profile=profile_params, session=db)