from typing import Optional

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.databases import async_get_db
from app.models.enums import DepartmentEnum
from app.models.user import User
from app.schemas.user_schema import (
    MessageResponse,
    MyPageResponse,
    PasswordChangeRequest,
    TokenResponse,
    UserListResponse,
    UserLoginRequest,
    UserProfileUpdateRequest,
    UserResponse,
    UserRoleUpdateRequest,
    UserSignupRequest,
)
from app.services.user_service import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    change_my_password,
    delete_my_account,
    get_current_user,
    list_users,
    login_user,
    refresh_access_token,
    signup_user,
    update_my_profile,
    update_user_role,
)


router = APIRouter(prefix="/api/v1/users", tags=["users"])


def _get_bearer_token(authorization: Optional[str]) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization 헤더에 Bearer 토큰이 필요합니다.")
    return authorization.replace("Bearer ", "", 1)


async def current_user_dependency(
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(async_get_db),
) -> User:
    access_token = _get_bearer_token(authorization)
    return await get_current_user(db, access_token)


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    user_data: UserSignupRequest,
    db: AsyncSession = Depends(async_get_db),
):
    return await signup_user(db, user_data)


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLoginRequest,
    response: Response,
    db: AsyncSession = Depends(async_get_db),
):
    access_token, refresh_token = await login_user(db, login_data)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        samesite="lax",
    )
    response.headers["X-Access-Token-Expires-Minutes"] = str(ACCESS_TOKEN_EXPIRE_MINUTES)
    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token_cookie: Optional[str] = Cookie(default=None, alias="refresh_token"),
    db: AsyncSession = Depends(async_get_db),
):
    if not refresh_token_cookie:
        raise HTTPException(status_code=401, detail="리프레시 토큰이 필요합니다.")
    access_token = await refresh_access_token(db, refresh_token_cookie)
    return TokenResponse(access_token=access_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response):
    response.delete_cookie(key="refresh_token")
    return MessageResponse(message="로그아웃되었습니다.")


@router.get("", response_model=list[UserListResponse])
async def get_user_list(
    search: Optional[str] = None,
    department: Optional[DepartmentEnum] = None,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(current_user_dependency),
):
    return await list_users(db, current_user, search=search, department=department)


@router.patch("/{user_id}/role", response_model=UserResponse)
async def change_user_role(
    user_id: int,
    role_data: UserRoleUpdateRequest,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(current_user_dependency),
):
    return await update_user_role(db, current_user, user_id, role_data)


@router.get("/me", response_model=MyPageResponse)
async def get_my_page(current_user: User = Depends(current_user_dependency)):
    return current_user


@router.patch("/me", response_model=MyPageResponse)
async def update_my_page(
    update_data: UserProfileUpdateRequest,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(current_user_dependency),
):
    return await update_my_profile(db, current_user, update_data)


@router.patch("/me/password", response_model=MessageResponse)
async def change_password(
    password_data: PasswordChangeRequest,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(current_user_dependency),
):
    await change_my_password(db, current_user, password_data)
    return MessageResponse(message="비밀번호가 변경되었습니다.")


@router.delete("/me", response_model=MessageResponse)
async def withdraw(
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(current_user_dependency),
):
    await delete_my_account(db, current_user)
    return MessageResponse(message="회원탈퇴가 완료되었습니다.")
