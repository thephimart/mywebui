"""Audit logging service."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from mywebui.db.models import AuditEvent


async def log_event(
    db: AsyncSession,
    event_type: str,
    user_id: uuid.UUID | None = None,
    details: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> AuditEvent:
    """Log an audit event."""
    event = AuditEvent(
        id=uuid.uuid4(),
        timestamp=datetime.utcnow(),
        user_id=user_id,
        event_type=event_type,
        details=details or {},
        request_id=request_id,
    )

    db.add(event)
    await db.commit()
    await db.refresh(event)

    return event


async def log_login(
    db: AsyncSession,
    user_id: uuid.UUID,
    request_id: str | None = None,
) -> AuditEvent:
    """Log a login event."""
    return await log_event(
        db,
        event_type="login",
        user_id=user_id,
        request_id=request_id,
    )


async def log_logout(
    db: AsyncSession,
    user_id: uuid.UUID,
    request_id: str | None = None,
) -> AuditEvent:
    """Log a logout event."""
    return await log_event(
        db,
        event_type="logout",
        user_id=user_id,
        request_id=request_id,
    )


async def log_session_refresh(
    db: AsyncSession,
    user_id: uuid.UUID,
    request_id: str | None = None,
) -> AuditEvent:
    """Log a session refresh event."""
    return await log_event(
        db,
        event_type="session_refresh",
        user_id=user_id,
        request_id=request_id,
    )


async def log_tool_execution(
    db: AsyncSession,
    user_id: uuid.UUID,
    tool_name: str,
    success: bool,
    duration_ms: int,
    request_id: str | None = None,
) -> AuditEvent:
    """Log a tool execution event."""
    return await log_event(
        db,
        event_type="tool_execution",
        user_id=user_id,
        details={
            "tool_name": tool_name,
            "success": success,
            "duration_ms": duration_ms,
        },
        request_id=request_id,
    )


async def log_chat_message(
    db: AsyncSession,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    request_id: str | None = None,
) -> AuditEvent:
    """Log a chat message event."""
    return await log_event(
        db,
        event_type="chat_message",
        user_id=user_id,
        details={"session_id": str(session_id)},
        request_id=request_id,
    )
