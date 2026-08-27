from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.databases import async_get_db
from app.schemas.user_schema import UserResponse, UserSignupRequest
from app.services.user_service import signup_user


router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    user_data: UserSignupRequest,
    db: AsyncSession = Depends(async_get_db),
):
    return await signup_user(db, user_data)
