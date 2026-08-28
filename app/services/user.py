from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.enums import RoleEnum
from app.models.user import User
from app.repositories.user import (
    create_user,
    delete_user,
    get_user_by_email,
    get_user_by_id,
    get_user_by_phone_number,
    list_users as repo_list_users,
    update_user,
)
from app.schemas.user import (
    PasswordChangeRequest,
    RoleUpdateRequest,
    UserSignupRequest,
    UserUpdateRequest,
)


async def signup(db: AsyncSession, data: UserSignupRequest):
    if await get_user_by_email(db, data.email):
        raise HTTPException(status_code=409, detail="이미 사용 중인 이메일입니다.")

    if await get_user_by_phone_number(db, data.phone_number):
        raise HTTPException(status_code=409, detail="이미 사용 중인 휴대폰 번호입니다.")

    hashed_password = hash_password(data.password)

    user = await create_user(
        db,
        email=data.email,
        hashed_password=hashed_password,
        name=data.name,
        department=data.department,
        gender=data.gender,
        phone_number=data.phone_number,
        role=RoleEnum.PENDING,
    )
    return user

async def login(db: AsyncSession, email: str, password: str) -> tuple[str, str]:
    user = await get_user_by_email(db, email)
    if user is None or not verify_password(user.hashed_password, password):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 일치하지 않습니다.")
    return create_access_token(user.id), create_refresh_token(user.id)


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> str:
    try:
        payload = decode_token(refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Refresh Token이 아닙니다.")

    user = await get_user_by_id(db, payload["user_id"])
    if user is None:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")
    return create_access_token(user.id)

async def update_me(db: AsyncSession, user: User, data: UserUpdateRequest) -> User:
    updates = data.model_dump(exclude_unset=True, exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="수정할 항목을 최소 하나 이상 입력해야 합니다.")
    return await update_user(db, user, **updates)


async def change_password(db: AsyncSession, user: User, data: PasswordChangeRequest) -> None:
    if not verify_password(user.hashed_password, data.current_password):
        raise HTTPException(status_code=400, detail="기존 비밀번호가 일치하지 않습니다.")
    await update_user(db, user, hashed_password=hash_password(data.new_password))


async def delete_me(db: AsyncSession, user: User) -> None:
    await delete_user(db, user)


async def list_users(db: AsyncSession, query: str | None, department: str | None) -> list[User]:
    return await repo_list_users(db, query, department)


async def update_user_role(db: AsyncSession, current_admin: User, data: RoleUpdateRequest) -> User:
    if data.user_id == current_admin.id:
        raise HTTPException(status_code=403, detail="본인의 권한은 변경할 수 없습니다.")

    target_user = await get_user_by_id(db, data.user_id)
    if target_user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    return await update_user(db, target_user, role=data.new_role)