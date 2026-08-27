from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import DepartmentEnum
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


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_phone_number(
    db: AsyncSession, phone_number: str, exclude_user_id: Optional[int] = None
) -> Optional[User]:
    query = select(User).where(User.phone_number == phone_number)
    if exclude_user_id is not None:
        query = query.where(User.id != exclude_user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_users(
    db: AsyncSession,
    search: Optional[str] = None,
    department: Optional[DepartmentEnum] = None,
) -> list[User]:
    query = select(User).order_by(User.id)
    if search:
        keyword = f"%{search}%"
        query = query.where(or_(User.email.like(keyword), User.name.like(keyword)))
    if department:
        query = query.where(User.department == department)
    result = await db.execute(query)
    return list(result.scalars().all())


async def save_user(db: AsyncSession, user: User) -> User:
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user: User) -> None:
    await db.delete(user)
    await db.commit()
