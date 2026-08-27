from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_user_by_email_or_phone(
    db: AsyncSession,
    email: str,
    phone_number: str,
) -> Optional[User]:
    result = await db.execute(
        select(User).where(
            or_(
                User.email == email,
                User.phone_number == phone_number,
            )
        )
    )
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user: User) -> User:
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
