from typing import Union

from fastapi import APIRouter, Depends, Form

from src.modules.grades.service import GradeService
from src.modules.grades.dependencies import get_grade_service
from src.dependencies import get_error
from src.modules.auth.dependencies import get_current_user

from src.modules.music.schemas.exceptions.track_422 import Track422
from src.modules.auth.schemas.exceptions.user_401 import User401
from src.modules.auth.schemas.exceptions.user_422 import User422
from src.modules.music.schemas.exceptions.grade_422 import Grade422


grade_router = APIRouter(prefix="/grades")


@grade_router.post(
    "/{track_id}",
    summary="Place grade (Protected)",
    description="Give grade for a track",
    tags=["Grades CRUD's"],
    responses={
        401: {"model": User401},
        422: {"model": Union[Track422, User422, Grade422]},
    },
)
async def place_grade(
    track_id: str,
    grade: int = Form(ge=1, le=10),
    user_id: str = Depends(get_current_user),
    service: GradeService = Depends(get_grade_service),
):
    return await get_error(
        service.grade_track,
        user_id=user_id,
        track_id=track_id,
        user_grade=grade,
    )
