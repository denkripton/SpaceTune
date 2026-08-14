from enum import Enum


class HealthCheckTimeout(Enum):
    DB_PING_SECONDS = 2.0
    CACHE_SECONDS = 5.0
