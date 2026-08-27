from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings

password_hasher = PasswordHasher()


def hash_password(plain_password: str) -> str:
    return password_hasher.hash(plain_password)


def verify_password(hashed_password: str, plain_password: str) -> bool:
    try:
        return password_hasher.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False


def create_access_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])