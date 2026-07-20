from typing import Optional

from src.utils.schemas.base_schema import BaseSchema


class ProfileVisibilityUpdateSchema(BaseSchema):
    email: Optional[bool] = None
    phone_number: Optional[bool] = None
    birth_date: Optional[bool] = None
    bio: Optional[bool] = None
    country: Optional[bool] = None
