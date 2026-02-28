"""Audit API routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mywebui.db import connection
from mywebui.db.models import AuditEvent
from mywebui.schemas.api import (
    AuditEventResponse,
    ListAuditEventsResponse,
)

router = APIRouter()


async def get_current_user(request: Request) -> dict:
    """Get current authenticated user from request state."""
    if not hasattr(request.state, "user_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    return {
        "user_id": request.state.user_id,
        "username": request.state.username,
        "role": request.state.role,
    }


async def require_admin(request: Request) -> dict:
    """Require admin role."""
    user = await get_current_user(request)
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


@router.get("", response_model=ListAuditEventsResponse)
async def list_audit_events(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    event_type: str | None = None,
    user_id: uuid.UUID | None = None,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(connection.get_audit_db),
):
    """List audit events (admin only)."""
    try:
        query = select(AuditEvent).order_by(desc(AuditEvent.timestamp))

        if event_type:
            query = query.where(AuditEvent.event_type == event_type)

        if user_id:
            query = query.where(AuditEvent.user_id == str(user_id))

        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        events = list(result.scalars().all())

        count_query = select(func.count(AuditEvent.id))
        if event_type:
            count_query = count_query.where(AuditEvent.event_type == event_type)
        if user_id:
            count_query = count_query.where(AuditEvent.user_id == str(user_id))

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        return ListAuditEventsResponse(
            events=[
                AuditEventResponse(
                    id=e.id,
                    timestamp=e.timestamp,
                    user_id=e.user_id,
                    event_type=e.event_type,
                    details=e.details,
                    request_id=e.request_id,
                )
                for e in events
            ],
            total=total,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit error: {type(e).__name__}: {e}")
