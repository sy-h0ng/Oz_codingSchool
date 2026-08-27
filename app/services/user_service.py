import hashlib
import secrets

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import RoleEnum
from app.models.user import User
from app.repositories.user_repository import create_user, get_user_by_email_or_phone
from app.schemas.user_schema import UserSignupRequest


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    iterations = 100_000
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    ).hex()
    return f"pbkdf2_sha256${iterations}${salt}${digest}"


async def signup_user(db: AsyncSession, user_data: UserSignupRequest) -> User:
    existing_user = await get_user_by_email_or_phone(
        db,
        email=user_data.email,
        phone_number=user_data.phone_number,
    )
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="이미 사용 중인 이메일 또는 휴대폰 번호입니다.",
        )

    user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        name=user_data.name,
        department=user_data.department,
        gender=user_data.gender,
        phone_number=user_data.phone_number,
        role=RoleEnum.PENDING,
        is_active=True,
    )
    return await create_user(db, user)
