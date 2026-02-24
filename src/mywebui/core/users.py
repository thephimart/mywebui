"""User service for user management."""

import uuid
from datetime import datetime

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mywebui.db.models import User


async def create_user(
    db: AsyncSession,
    username: str,
    password: str,
    role: str = "user",
) -> User:
    """Create a new user with hashed password."""
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    user = User(
        id=uuid.uuid4(),
        username=username,
        password_hash=password_hash,
        role=role,
        is_active=True,
        created_at=datetime.utcnow(),
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    """Get a user by username."""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """Get a user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    """Authenticate a user by username and password."""
    user = await get_user_by_username(db, username)

    if user is None:
        return None

    if not user.is_active:
        return None

    if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        return None

    return user


async def list_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[User]:
    """List all users."""
    result = await db.execute(select(User).offset(skip).limit(limit))
    return list(result.scalars().all())


async def update_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    username: str | None = None,
    password: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
) -> User | None:
    """Update a user."""
    user = await get_user_by_id(db, user_id)

    if user is None:
        return None

    if username is not None:
        user.username = username

    if password is not None:
        user.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    if role is not None:
        user.role = role

    if is_active is not None:
        user.is_active = is_active

    await db.commit()
    await db.refresh(user)

    return user


async def delete_user(db: AsyncSession, user_id: uuid.UUID) -> bool:
    """Delete a user."""
    user = await get_user_by_id(db, user_id)

    if user is None:
        return False

    await db.delete(user)
    await db.commit()

    return True
