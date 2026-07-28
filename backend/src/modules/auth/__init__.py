from src.modules.auth.dependencies import (
    user_repository,
    get_user_service,
    get_oauth_service,
    get_current_user,
)

from src.modules.auth.services import UserService, OAuthService

__all__ = [
    "user_repository",
    
    "get_user_service",
    "get_oauth_service"
    "get_current_user",

    "UserService",
    "OAuthService"
]
