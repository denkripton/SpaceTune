import secrets
from urllib.parse import urlencode

import httpx

from src.config import settings
from src.modules.auth.repository import UserRepository
from src.modules.auth.utils import JWT
from src.utils import UnitOfWork
from src.utils.exceptions import ServiceError


class OAuthService:
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    STATE_BYTES = 32

    def __init__(self, repo: UserRepository, jwt: JWT, uow: UnitOfWork):
        self.__repo = repo
        self.__jwt = jwt
        self.__uow = uow

    def generate_state(self) -> str:
        return secrets.token_urlsafe(self.STATE_BYTES)

    def _verify_state(self, received: str | None, expected: str | None) -> None:
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

    async def login(self, code: str, state: str | None, expected_state: str | None):
        self._verify_state(received=state, expected=expected_state)

        tokens = await self._exchange_code(code=code)

        access_token = tokens.get("access_token")
        if not access_token:
            raise ServiceError(code=422, msg="Failed to exchange OAuth code")

        user_info = await self._get_userinfo(access_token)

        sub = user_info.get("sub")
        email = user_info.get("email")
        email_verified = user_info.get("email_verified")

        if not sub or not email:
            raise ServiceError(
                code=422, msg="Google account is missing required profile data"
            )

        username = user_info.get("name", email.split("@")[0])[:20]

        user = await self.__repo.get_one(google_id=sub)

        if user is None:
            if email_verified is not True:
                raise ServiceError(
                    code=422,
                    msg="Email is not verified, cannot sign in with this Google account",
                )

            user = await self.__repo.get_by_email(email=email)
            if user is not None:
                user.google_id = sub
            else:
                user = await self.__repo.create(
                    username=username,
                    email=email,
                    password=None,
                    google_id=sub,
                )

            await self.__uow.commit(
                conflict_msg="Account with this email or Google ID was just created. Please try again"
            )
            await self.__uow.refresh(user)

        user_id = str(user.id)
        access = self.__jwt.create_access_token(user_id)
        refresh = self.__jwt.create_refresh_token(user_id)

        return {
            "access": access,
            "refresh": refresh,
        }