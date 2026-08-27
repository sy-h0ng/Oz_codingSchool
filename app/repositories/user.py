from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_phone_number(db: AsyncSession, phone_number: str) -> User | None:
    result = await db.execute(select(User).where(User.phone_number == phone_number))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, **kwargs) -> User:
    user = User(**kwargs)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def update_user(db: AsyncSession, user: User, **fields) -> User:
    for key, value in fields.items():
        setattr(user, key, value)
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user: User) -> None:
    await db.delete(user)
    await db.commit()

async def list_users(db: AsyncSession, query: str | None, department: str | None) -> list[User]:
    stmt = select(User)
    if query:
        pattern = f"%{query}%"
        stmt = stmt.where(or_(User.email.ilike(pattern), User.name.ilike(pattern)))
    if department:
        stmt = stmt.where(User.department == department)
    result = await db.execute(stmt)
    return list(result.scalars().all())