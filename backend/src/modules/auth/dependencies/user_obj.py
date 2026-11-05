import uuid

from fastapi import Depends, HTTPException

from src.modules.auth.dependencies.get_current_user import get_current_user
from src.modules.auth.dependencies.user_repo import user_repository
from src.modules.auth.models import User
from src.modules.auth.repository import UserRepository


async def get_current_user_obj(
    user_id: uuid.UUID = Depends(get_current_user),
    user_repo: UserRepository = Depends(user_repository),
) -> User:
    user = await user_repo.get_by_id(id=user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not authorized")
    return user
