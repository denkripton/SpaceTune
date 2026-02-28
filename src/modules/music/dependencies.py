from fastapi import Depends

from src.modules.auth.dependencies import get_user_repo
from src.modules.music.service import TrackService
from src.modules.music.repository import TrackRepository
from src.repository import ABCRepository
from src.dependencies import get_session



async def get_track_repo(session=Depends(get_session)) -> ABCRepository:
    return TrackRepository(session)


async def get_track_service(session=Depends(get_session)):
    track_repo = TrackRepository(session=session)
    user_repo = await get_user_repo(session=session)
    return TrackService(track_repo=track_repo, user_repo=user_repo)
