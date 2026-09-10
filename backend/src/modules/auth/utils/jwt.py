import uuid
from datetime import UTC, datetime, timedelta

from jwt import decode, encode
from jwt.exceptions import PyJWTError

from src.config import settings
from src.modules.auth.utils.enums import TokenLifetime, TokenType


class JWT:
    algorithm = "HS256"

    def create_token(self, payload: dict) -> str:
        token = encode(
            payload=payload, key=settings.JWT_SECRET_KEY, algorithm=self.algorithm
        )
        return token

    def decode_token(self, token: str) -> dict:
        decoded_token = decode(
            jwt=token, key=settings.JWT_SECRET_KEY, algorithms=[self.algorithm]
        )
        return decoded_token

    def create_access_token(self, id: str) -> str:
        now = datetime.now(UTC)
        iat = int(now.timestamp())
        exp = int(
            (now + timedelta(minutes=TokenLifetime.ACCESS_MINUTES.value)).timestamp()
        )
        payload = {
            "sub": id,
            "iat": iat,
            "exp": exp,
            "jti": str(uuid.uuid4()),
            "type": TokenType.ACCESS.value,
        }
        token = self.create_token(payload)
        return token

    def create_refresh_token(self, id: str, expiration: int | None = None) -> str:
        now = datetime.now(UTC)
        iat = int(now.timestamp())
        exp = (
            int((now + timedelta(days=TokenLifetime.REFRESH_DAYS.value)).timestamp())
            if not expiration
            else expiration
        )
        payload = {
            "sub": id,
            "iat": iat,
            "exp": exp,
            "jti": str(uuid.uuid4()),
            "type": TokenType.REFRESH.value,
        }
        token = self.create_token(payload)
        return token

    def validate_token(self, token: str | None) -> dict | None:
        if not token:
            return None
        try:
            payload = self.decode_token(token)
        except PyJWTError:
            return None
        if not payload.get("sub"):
            return None
        return payload

    def validate_access_token(self, token: str | None) -> dict | None:
        payload = self.validate_token(token)
        if payload is None or payload.get("type") != TokenType.ACCESS.value:
            return None
        return payload

    def validate_refresh_token(self, token: str | None) -> dict | None:
        payload = self.validate_token(token)
        if payload is None or payload.get("type") != TokenType.REFRESH.value:
            return None
        return payload
