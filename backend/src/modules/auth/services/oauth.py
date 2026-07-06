import secrets
from urllib.parse import urlencode

import httpx

from src.config import settings
from src.modules.auth.repository import UserRepository
from src.modules.auth.utils import JWT
from src.utils.exceptions import ServiceError


class OAuthService:
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    STATE_BYTES = 32

    def __init__(self, repo: UserRepository, jwt: JWT):
        self.__repo = repo
        self.__jwt = jwt

    def generate_state(self) -> str:
        return secrets.token_urlsafe(self.STATE_BYTES)

    def verify_state(self, received: str | None, expected: str | None) -> None:
        if (
            not received
            or not expected
            or not secrets.compare_digest(received, expected)
        ):
            raise ServiceError(code=422, msg="Invalid or missing OAuth state")

    def get_redirect_url(self, state: str) -> str:
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "state": state,
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    async def _exchange_code(self, code: str):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
        if response.status_code != 200:
            raise ServiceError(code=422, msg="Failed to exchange OAuth code")
        return response.json()

    async def _get_userinfo(self, access_token: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                settings.GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        if response.status_code != 200:
            raise ServiceError(code=422, msg="Failed to exchange OAuth code")
        return response.json()

    async def login(self, code: str):
        tokens = await self._exchange_code(code=code)
        user_info = await self._get_userinfo(tokens["access_token"])

        sub = user_info["sub"]
        email = user_info["email"]
        username = user_info.get("name", email.split("@")[0])[:20]

        user = await self.__repo.get_one(google_id=sub)

        if user is None:
            user = await self.__repo.get_by_email(email=email)
            if user:
                user.google_id = sub
            else:
                user = await self.__repo.create(
                    username=username,
                    email=email,
                    password=None,
                    google_id=sub,
                )

            await self.__repo.session.commit()
            await self.__repo.session.refresh(user)

        user.id = str(user.id)
        access = self.__jwt.create_access_token(user.id)
        refresh = self.__jwt.create_refresh_token(user.id)

        return {
            "access": access,
            "refresh": refresh,
        }
