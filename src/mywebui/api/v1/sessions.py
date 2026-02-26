"""Sessions API routes."""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from mywebui.core import auth as auth_service
from mywebui.db import connection
from mywebui.schemas.api import (
    ListSessionsResponse,
    SessionResponse,
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
    }


@router.get("", response_model=ListSessionsResponse)
async def list_sessions(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    current: dict = Depends(get_current_user),
):
    """List all sessions for the current user."""
    factory = connection.get_user_session_factory(current["username"])
    async with factory() as db:
        sessions = await auth_service.list_user_sessions(
            db,
            current["user_id"],
            skip=skip,
            limit=limit,
        )
        total = len(sessions)

    return ListSessionsResponse(
        sessions=[
            SessionResponse(
                session_id=s.session_id,
                user_id=s.user_id,
                issued_at=s.issued_at,
                expires_at=s.expires_at,
                last_activity=s.last_activity,
                revoked=s.revoked,
            )
            for s in sessions
        ],
        total=total,
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(
    session_id: str,
    request: Request,
    current: dict = Depends(get_current_user),
):
    """Revoke a specific session."""
    factory = connection.get_user_session_factory(current["username"])
    async with factory() as db:
        success = await auth_service.revoke_session(db, session_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_all_sessions(
    request: Request,
    current: dict = Depends(get_current_user),
):
    """Revoke all sessions for the current user."""
    factory = connection.get_user_session_factory(current["username"])
    async with factory() as db:
        await auth_service.revoke_all_user_sessions(db, current["user_id"])
