from src.modules.auth.router import user_router
from src.modules.grades.router import grade_router
from src.modules.health.router import health_router
from src.modules.music.router import music_router
from src.modules.profile.router import profile_router

__all__ = [
    "grade_router",
    "health_router",
    "music_router",
    "profile_router",
    "user_router",
]
