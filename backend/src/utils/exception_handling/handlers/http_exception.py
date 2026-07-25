from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.utils.exception_handling import build_problem
from src.utils.exception_handling.constants import PROBLEM_CONTENT_TYPE


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=build_problem(
            status_code=exc.status_code,
            detail=str(exc.detail),
            instance=str(request.url.path),
        ),
        media_type=PROBLEM_CONTENT_TYPE,
        headers=exc.headers,
    )
