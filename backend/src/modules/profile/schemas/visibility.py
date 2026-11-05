
from src.utils.schemas.base_schema import BaseSchema


class ProfileVisibilityUpdateSchema(BaseSchema):
    email: bool | None = None
    phone_number: bool | None = None
    birth_date: bool | None = None
    bio: bool | None = None
    country: bool | None = None
