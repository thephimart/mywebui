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


async def log_tool_command(
    db: AsyncSession,
    user_id: uuid.UUID,
    tool: str,
    status: str,
    reason: str | None = None,
    request_id: str | None = None,
) -> AuditEvent:
    """Log a tool command attempt (e.g., blocked exec_python/exec_shell)."""
    return await log_event(
        db,
        event_type="tool_command",
        user_id=user_id,
        details={
            "tool": tool,
            "status": status,
            "reason": reason,
        },
        request_id=request_id,
    )


async def log_doc_ingest(
    db: AsyncSession,
    user_id: uuid.UUID,
    document_id: uuid.UUID,
    title: str,
    request_id: str | None = None,
) -> AuditEvent:
    """Log a document ingestion event."""
    return await log_event(
        db,
        event_type="doc_ingest",
        user_id=user_id,
        details={
            "document_id": str(document_id),
            "title": title,
        },
        request_id=request_id,
    )


async def log_doc_delete(
    db: AsyncSession,
    user_id: uuid.UUID,
    document_id: uuid.UUID,
    request_id: str | None = None,
) -> AuditEvent:
    """Log a document deletion event."""
    return await log_event(
        db,
        event_type="doc_delete",
        user_id=user_id,
        details={"document_id": str(document_id)},
        request_id=request_id,
    )


async def log_acl_change(
    db: AsyncSession,
    user_id: uuid.UUID,
    target_type: str,
    target_id: str,
    changes: dict,
    request_id: str | None = None,
) -> AuditEvent:
    """Log an ACL (Access Control List) change event."""
    return await log_event(
        db,
        event_type="acl_change",
        user_id=user_id,
        details={
            "target_type": target_type,
            "target_id": target_id,
            "changes": changes,
        },
        request_id=request_id,
    )


async def log_model_config_change(
    db: AsyncSession,
    user_id: uuid.UUID,
    model_role: str,
    changes: dict,
    request_id: str | None = None,
) -> AuditEvent:
    """Log a model configuration change event."""
    return await log_event(
        db,
        event_type="model_config_change",
        user_id=user_id,
        details={
            "model_role": model_role,
            "changes": changes,
        },
        request_id=request_id,
    )


async def log_session_compaction(
    db: AsyncSession,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    messages_compacted: int,
    summary_id: str,
    request_id: str | None = None,
) -> AuditEvent:
    """Log a session compaction event."""
    return await log_event(
        db,
        event_type="session_compaction",
        user_id=user_id,
        details={
            "session_id": str(session_id),
            "messages_compacted": messages_compacted,
            "summary_id": summary_id,
        },
        request_id=request_id,
    )


async def log_attachment_upload(
    db: AsyncSession,
    user_id: uuid.UUID,
    attachment_id: uuid.UUID,
    filename: str,
    content_type: str,
    size: int,
    request_id: str | None = None,
) -> AuditEvent:
    """Log an attachment upload event."""
    return await log_event(
        db,
        event_type="attachment_upload",
        user_id=user_id,
        details={
            "attachment_id": str(attachment_id),
            "filename": filename,
            "content_type": content_type,
            "size": size,
        },
        request_id=request_id,
    )


async def log_session_revoke(
    db: AsyncSession,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    revoked_by: uuid.UUID,
    reason: str | None = None,
    request_id: str | None = None,
) -> AuditEvent:
    """Log a session revocation event."""
    return await log_event(
        db,
        event_type="session_revoke",
        user_id=user_id,
        details={
            "session_id": str(session_id),
            "revoked_by": str(revoked_by),
            "reason": reason,
        },
        request_id=request_id,
    )
