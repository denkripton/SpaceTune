from fastapi import Depends
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter

from src.modules.health.dependencies import get_health_service
from src.modules.health.schemas import HealthReadSchema
from src.modules.health.service import HealthService
from src.utils.routing.error_handling import ErrorHandlingRoute

health_router = APIRouter(route_class=ErrorHandlingRoute)


@health_router.get(
    "/health",
    summary="Health check",
    description="Liveness/readiness probe used by Docker HEALTHCHECK and orchestrators",
    tags=["Health"],
    response_model=HealthReadSchema,
    responses={503: {"model": HealthReadSchema}},
)
async def health_check(service: HealthService = Depends(get_health_service)):
    result = await service.check()

    if result.status == "unhealthy":
        return JSONResponse(status_code=503, content=result.model_dump())

    return result
