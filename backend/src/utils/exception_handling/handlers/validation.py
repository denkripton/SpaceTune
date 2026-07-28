from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.utils.exception_handling import build_problem
from src.utils.exception_handling.constants import PROBLEM_CONTENT_TYPE


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    problem = build_problem(
        status_code=422,
        detail="Request validation failed",
        instance=str(request.url.path),
    )

    problem["errors"] = exc.errors()
    return JSONResponse(
        status_code=422,
        content=problem,
        media_type=PROBLEM_CONTENT_TYPE,
    )
