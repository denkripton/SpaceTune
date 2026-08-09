import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.utils.middleware.constants import RequestContextHeaders


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = (
            request.headers.get(RequestContextHeaders.REQUEST_ID.value)
            or str(uuid.uuid4())
        )

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        response = await call_next(request)
        response.headers[RequestContextHeaders.REQUEST_ID.value] = request_id

        return response