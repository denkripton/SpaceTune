from fastapi import Request
from fastapi.responses import JSONResponse

from src.utils.exception_handling import build_problem
from src.utils.exception_handling.constants import PROBLEM_CONTENT_TYPE


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=build_problem(
            status_code=500,
            detail="Internal server error",
            instance=str(request.url.path),
        ),
        media_type=PROBLEM_CONTENT_TYPE,
    )
