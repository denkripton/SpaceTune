from src.modules.music.router import music_router
from src.modules.auth.router import user_router
from src.modules.profile.router import profile_router
from src.modules.grades.router import grade_router

__all__ = ["profile_router", "music_router", "user_router", "grade_router"]