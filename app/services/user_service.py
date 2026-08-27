import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import DepartmentEnum, RoleEnum
from app.models.user import User
from app.repositories.user_repository import (
    create_user,
    delete_user,
    get_user_by_email,
    get_user_by_email_or_phone,
    get_user_by_id,
    get_user_by_phone_number,
    get_users,
    save_user,
)
from app.schemas.user_schema import (
    PasswordChangeRequest,
    UserLoginRequest,
    UserProfileUpdateRequest,
    UserRoleUpdateRequest,
    UserSignupRequest,
)


JWT_SECRET_KEY = "ai-health-assignment-secret-key"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


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


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        algorithm, iterations, salt, digest = hashed_password.split("$")
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    new_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        int(iterations),
    ).hex()
    return hmac.compare_digest(new_digest, digest)


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _base64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_token(user_id: int, expires_delta: timedelta, token_type: str) -> str:
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    expire_at = datetime.now(timezone.utc) + expires_delta
    payload = {
        "user_id": user_id,
        "type": token_type,
        "exp": int(expire_at.timestamp()),
    }

    header_part = _base64url_encode(json.dumps(header).encode("utf-8"))
    payload_part = _base64url_encode(json.dumps(payload).encode("utf-8"))
    signing_input = f"{header_part}.{payload_part}"
    signature = hmac.new(
        JWT_SECRET_KEY.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return f"{signing_input}.{_base64url_encode(signature)}"


def decode_token(token: str, expected_type: str) -> dict:
    credentials_exception = HTTPException(status_code=401, detail="인증 정보가 올바르지 않습니다.")
    try:
        header_part, payload_part, signature_part = token.split(".")
        signing_input = f"{header_part}.{payload_part}"
        expected_signature = hmac.new(
            JWT_SECRET_KEY.encode("utf-8"),
            signing_input.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(
            _base64url_encode(expected_signature),
            signature_part,
        ):
            raise credentials_exception

        payload = json.loads(_base64url_decode(payload_part))
    except Exception as exc:
        raise credentials_exception from exc

    if payload.get("type") != expected_type:
        raise credentials_exception

    if payload.get("exp", 0) < int(datetime.now(timezone.utc).timestamp()):
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다.")

    return payload


def create_access_token(user_id: int) -> str:
    return create_token(
        user_id=user_id,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type="access",
    )


def create_refresh_token(user_id: int) -> str:
    return create_token(
        user_id=user_id,
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        token_type="refresh",
    )


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


async def login_user(db: AsyncSession, login_data: UserLoginRequest) -> tuple[str, str]:
    user = await get_user_by_email(db, login_data.email)
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="비활성화된 계정입니다.")
    return create_access_token(user.id), create_refresh_token(user.id)


async def get_current_user(db: AsyncSession, access_token: str) -> User:
    payload = decode_token(access_token, expected_type="access")
    user = await get_user_by_id(db, int(payload["user_id"]))
    if not user:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")
    return user


def check_admin(user: User) -> None:
    if user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="관리자만 사용할 수 있는 기능입니다.")


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> str:
    payload = decode_token(refresh_token, expected_type="refresh")
    user = await get_user_by_id(db, int(payload["user_id"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="다시 로그인해주세요.")
    return create_access_token(user.id)


async def list_users(
    db: AsyncSession,
    current_user: User,
    search: Optional[str] = None,
    department: Optional[DepartmentEnum] = None,
) -> list[User]:
    check_admin(current_user)
    return await get_users(db, search=search, department=department)


async def update_user_role(
    db: AsyncSession,
    current_user: User,
    target_user_id: int,
    role_data: UserRoleUpdateRequest,
) -> User:
    check_admin(current_user)
    target_user = await get_user_by_id(db, target_user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="회원을 찾을 수 없습니다.")
    target_user.role = role_data.role
    return await save_user(db, target_user)


async def update_my_profile(
    db: AsyncSession,
    current_user: User,
    update_data: UserProfileUpdateRequest,
) -> User:
    if update_data.department is None and update_data.phone_number is None:
        raise HTTPException(status_code=400, detail="수정할 항목을 1개 이상 입력해주세요.")

    if update_data.phone_number is not None:
        existing_user = await get_user_by_phone_number(
            db,
            phone_number=update_data.phone_number,
            exclude_user_id=current_user.id,
        )
        if existing_user:
            raise HTTPException(status_code=400, detail="이미 사용 중인 휴대폰 번호입니다.")
        current_user.phone_number = update_data.phone_number

    if update_data.department is not None:
        current_user.department = update_data.department

    return await save_user(db, current_user)


async def change_my_password(
    db: AsyncSession,
    current_user: User,
    password_data: PasswordChangeRequest,
) -> None:
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="기존 비밀번호가 올바르지 않습니다.")
    current_user.hashed_password = hash_password(password_data.new_password)
    await save_user(db, current_user)


async def delete_my_account(db: AsyncSession, current_user: User) -> None:
    await delete_user(db, current_user)
