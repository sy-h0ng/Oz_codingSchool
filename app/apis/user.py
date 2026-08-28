from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db.databases import async_get_db
from app.core.deps import get_current_admin, get_current_user
from app.models.user import User
from app.schemas.user import (
    AdminUserListItem,
    PasswordChangeRequest,
    RoleUpdateRequest,
    TokenResponse,
    UserResponse,
    UserSignupRequest,
    UserUpdateRequest,
)
from app.services.user import (
    change_password,
    delete_me,
    list_users,
    login,
    refresh_access_token,
    signup,
    update_me,
    update_user_role,
)

router = APIRouter(prefix="/api/v1/users", tags=["users"])
admin_router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup_api(data: UserSignupRequest, db: AsyncSession = Depends(async_get_db)):
    return await signup(db, data)


@router.post("/login", response_model=TokenResponse)
async def login_api(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(async_get_db),
):
    access_token, refresh_token = await login(db, form_data.username, form_data.password)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        samesite="lax",
    )
    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_api(
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(async_get_db),
):
    if refresh_token is None:
        raise HTTPException(status_code=401, detail="Refresh Token이 없습니다.")
    access_token = await refresh_access_token(db, refresh_token)
    return TokenResponse(access_token=access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_api(response: Response):
    response.delete_cookie("refresh_token")


@router.get("/me", response_model=UserResponse)
async def get_me_api(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me_api(
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    return await update_me(db, current_user, data)


@router.patch("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password_api(
    data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    await change_password(db, current_user, data)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me_api(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    await delete_me(db, current_user)


@admin_router.get("/users", response_model=list[AdminUserListItem])
async def list_users_api(
    query: str | None = None,
    department: str | None = None,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(async_get_db),
):
    return await list_users(db, query, department)


@admin_router.patch("/users/role", response_model=UserResponse)
async def update_user_role_api(
    data: RoleUpdateRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(async_get_db),
):
    return await update_user_role(db, current_admin, data)