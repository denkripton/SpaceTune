from typing import Literal

from src.utils.schemas import BaseSchema


class HealthReadSchema(BaseSchema):
    status: Literal["healthy", "unhealthy"]
    database: Literal["connected", "disconnected"]