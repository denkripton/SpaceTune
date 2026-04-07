from src.modules.music.dependencies import get_track_service
from src.modules.music.router import music_router
from src.modules.music.service import TrackService

__all__ = ["get_track_service", "music_router", "TrackService"]
