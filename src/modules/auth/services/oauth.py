import httpx

from src.config import settings
from src.dependencies import ServiceError
from src.modules.auth.repository import UserRepository
from src.modules.auth.utils import JWT


class OAuthService:
    def __init__(self, repo: UserRepository, jwt: JWT):
        self.__repo = repo
        self.__jwt = jwt

    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

    def get_redirect_url(self):
        result = []

        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
        }
        for k, v in params.items():
            result.append(f"{k}={v}")

        query = "&".join(result)

        return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"

    async def _exchange_code(self, code: str):
        async with httpx.AsyncClient as client:
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
        async with httpx.AsyncClient as client:
            response = await client.get(
                settings.GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        if response.status_code != 200:
            raise ServiceError(code=422, msg="Failed to exchange OAuth code")
        return response.json()

    async def login(self, code: str):
        tokens = await self._exchange_code(code=code)
        user_info = await self._get_userinfo[tokens["access_token"]]

        sub = user_info["sub"]
        email = user_info["email"]
        username = user_info.get("name", email.split("@")[0])[:20]

        existing_user = await self.__repo.get_one(google_id=sub)

        if existing_user is None:
            email_in_db = await self.__repo.get_by_email(email=email)
            if email_in_db:
                email_in_db.google_id = sub
            else:
                user = await self.__repo.create(
                    username=username,
                    email=email,
                    password=None,
                    google_id=sub,
                )

            await self.__repo.session.commit()
            await self.__repo.session.refresh(user)

        access = self.jwt.create_access_token(existing_user.id)
        refresh = self.jwt.create_refresh_token(existing_user.id)

        return {
            "access": access,
            "refresh": refresh,
        }