from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_session
from src.modules.health.service import HealthService


class HealthServiceFactory:
    def __init__(self, service_cls: type[HealthService] = HealthService):
        self.service_cls = service_cls

    def create(self, session: AsyncSession) -> HealthService:
        return self.service_cls(session=session)


health_service_factory = HealthServiceFactory()


def get_health_service(
    session: AsyncSession = Depends(get_session),
) -> HealthService:
    return health_service_factory.create(session=session)
