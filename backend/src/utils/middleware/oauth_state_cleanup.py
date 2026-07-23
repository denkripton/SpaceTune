from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response




class OAuthStateCleanupMiddleware(BaseHTTPMiddleware):
    STATE_COOKIE_NAME = "oauth_state"

    def __init__(self, app, callback_path: str = "/users/oauth/google/callback"):
        super().__init__(app)
        self._callback_path = callback_path

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)

        if request.url.path == self._callback_path:
            response.delete_cookie(self.STATE_COOKIE_NAME)

        return response
