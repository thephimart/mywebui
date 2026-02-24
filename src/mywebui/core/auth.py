"""Authentication service with session management."""

import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from mywebui.config import get_config
from mywebui.db.user_models import Session as UserSession


def _get_session_config() -> dict[str, Any]:
    """Get session configuration."""
    config = get_config()
    return {
        "rolling_ttl_hours": config.security.session_rolling_ttl_hours,
        "absolute_max_days": config.security.session_absolute_max_days,
    }


async def create_session(
    db: AsyncSession,
    user_id: uuid.UUID,
    username: str,
) -> tuple[UserSession, str]:
    """Create a new session for a user."""
    config = _get_session_config()
    now = datetime.utcnow()

    session_token = str(uuid.uuid4())

    session = UserSession(
        session_id=uuid.uuid4(),
        session_token=session_token,
        user_id=user_id,
        issued_at=now,
        expires_at=now + timedelta(hours=config["rolling_ttl_hours"]),
        revoked=False,
        last_activity=now,
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)

    return session, session_token


async def get_session_by_token(
    db: AsyncSession,
    token: str,
) -> UserSession | None:
    """Get a session by token."""
    result = await db.execute(
        select(UserSession).where(
            and_(
                UserSession.session_token == token,
                UserSession.revoked == False,
            )
        )
    )
    return result.scalar_one_or_none()


async def refresh_session(
    db: AsyncSession,
    session: UserSession,
) -> UserSession:
    """Refresh a session's expiration time."""
    config = _get_session_config()
    now = datetime.utcnow()

    issued_at = session.issued_at
    absolute_max = issued_at + timedelta(days=config["absolute_max_days"])

    new_expires = now + timedelta(hours=config["rolling_ttl_hours"])

    if new_expires > absolute_max:
        new_expires = absolute_max

    session.last_activity = now
    session.expires_at = new_expires

    await db.commit()
    await db.refresh(session)

    return session


async def revoke_session(
    db: AsyncSession,
    session_id: uuid.UUID,
) -> bool:
    """Revoke a session."""
    result = await db.execute(
        select(UserSession).where(UserSession.session_id == session_id)
    )
    session = result.scalar_one_or_none()

    if session is None:
        return False

    session.revoked = True
    await db.commit()

    return True


async def revoke_all_user_sessions(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> int:
    """Revoke all sessions for a user."""
    result = await db.execute(
        select(UserSession).where(
            and_(
                UserSession.user_id == user_id,
                UserSession.revoked == False,
            )
        )
    )
    sessions = result.scalars().all()

    count = 0
    for session in sessions:
        session.revoked = True
        count += 1

    await db.commit()

    return count


async def list_user_sessions(
    db: AsyncSession,
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
) -> list[UserSession]:
    """List all sessions for a user."""
    result = await db.execute(
        select(UserSession)
        .where(UserSession.user_id == user_id)
        .order_by(UserSession.last_activity.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def cleanup_expired_sessions(db: AsyncSession) -> int:
    """Clean up expired sessions."""
    now = datetime.utcnow()

    result = await db.execute(
        select(UserSession).where(
            UserSession.expires_at < now
        )
    )
    sessions = result.scalars().all()

    count = 0
    for session in sessions:
        session.revoked = True
        count += 1

    await db.commit()

    return count
