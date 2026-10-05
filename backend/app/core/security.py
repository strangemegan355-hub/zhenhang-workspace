from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"
REALTIME_TICKET_TYPE = "realtime"


def _encode(subject: str | Any, token_type: str, lifetime: timedelta) -> str:
    to_encode = {"sub": str(subject), "exp": datetime.now(UTC) + lifetime, "typ": token_type}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    lifetime = expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    return _encode(subject, ACCESS_TOKEN_TYPE, lifetime)


def create_refresh_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    lifetime = expires_delta or timedelta(minutes=settings.refresh_token_expire_minutes)
    return _encode(subject, REFRESH_TOKEN_TYPE, lifetime)


def create_realtime_ticket(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    """Mint the short-lived credential the header-less realtime transports use.

    The browser EventSource and WebSocket APIs cannot set request headers, so those
    transports select the user through the URL. A ticket bounds that exposure: it carries its
    own token type, so every header-authenticated endpoint rejects it, and it expires in
    minutes rather than hours.
    """
    lifetime = expires_delta or timedelta(seconds=settings.realtime_ticket_expire_seconds)
    return _encode(subject, REALTIME_TICKET_TYPE, lifetime)


def decode_token(token: str, expected_type: str) -> dict[str, Any] | None:
    """Decode a token and require its declared type.

    The type lives in this single function on purpose. Checking signatures only, as the first
    implementation did, let a refresh token be presented as an access token: it was validly
    signed and carried a subject, and nothing looked at `typ`.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None
    if payload.get("typ") != expected_type:
        return None
    return payload


def decode_access_token(token: str) -> dict[str, Any] | None:
    return decode_token(token, ACCESS_TOKEN_TYPE)


def decode_refresh_token(token: str) -> dict[str, Any] | None:
    return decode_token(token, REFRESH_TOKEN_TYPE)


def decode_realtime_ticket(token: str) -> dict[str, Any] | None:
    return decode_token(token, REALTIME_TICKET_TYPE)
