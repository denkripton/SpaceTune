from fastapi import Request
from fastapi.responses import JSONResponse

from src.utils.exception_handling import build_problem
from src.utils.exception_handling.constants import PROBLEM_CONTENT_TYPE
from src.utils.exceptions import ServiceError


async def service_error_handler(request: Request, exc: ServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=build_problem(
            status_code=exc.status_code,
            detail=exc.message,
            instance=str(request.url.path),
        ),
        media_type=PROBLEM_CONTENT_TYPE,
    )
