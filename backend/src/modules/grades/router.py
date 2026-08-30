import uuid
from typing import Union

from fastapi import APIRouter, Depends, Form

from src.modules.auth.dependencies import get_current_user_obj
from src.modules.auth.models import User
from src.modules.auth.schemas.exceptions.user_401 import User401
from src.modules.auth.schemas.exceptions.user_404 import User404
from src.modules.grades.dependencies import get_grade_service
from src.modules.grades.service import GradeService
from src.modules.music.schemas.exceptions.track_404 import Track404
from src.utils.routing.error_handling import ErrorHandlingRoute

grade_router = APIRouter(prefix="/grades", route_class=ErrorHandlingRoute)


@grade_router.post(
    "/{track_id}",
    summary="Place grade (Protected)",
    description="Give grade for a track",
    tags=["Grades CRUD's"],
    responses={
        401: {"model": User401},
        404: {"model": Union[User404, Track404]},
    },
)
async def place_grade(
    track_id: uuid.UUID,
    grade: int = Form(ge=1, le=10),
    user: User = Depends(get_current_user_obj),
    service: GradeService = Depends(get_grade_service),
):
    return await service.grade_track(
        user=user,
        track_id=track_id,
        user_grade=grade,
    )
