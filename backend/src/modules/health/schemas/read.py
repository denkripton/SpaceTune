from typing import Literal

from src.utils.schemas import BaseSchema


class HealthReadSchema(BaseSchema):
    status: Literal["healthy", "unhealthy"]
    database: Literal["connected", "disconnected"]

    @property
    def http_status_code(self) -> int:
        if self.status == "healthy":
            return 200
        else:
            return 503
