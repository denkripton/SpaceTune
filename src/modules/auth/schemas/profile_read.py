from src.modules.auth.schemas.profile_creation import ProfileCreationSchema
from src.modules.auth.schemas.user_read import UserRead


class UserProfileReadSchema(ProfileCreationSchema, UserRead):
    pass
