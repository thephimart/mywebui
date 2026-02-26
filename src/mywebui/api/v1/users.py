"""Users API routes."""


from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from mywebui.core import users as users_service
from mywebui.db import connection
from mywebui.schemas.api import (
    UserResponse,
    UserUpdate,
)

router = APIRouter()


async def get_current_user(request: Request) -> UserResponse:
    """Get current authenticated user from request state."""
    if not hasattr(request.state, "user_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    factory = connection.get_docs_session_factory()
    async with factory() as db:
        user = await users_service.get_user_by_id(db, request.state.user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

    return UserResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


async def require_admin(request: Request) -> UserResponse:
    """Require admin role."""
    user = await get_current_user(request)
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


@router.get("", response_model=list[UserResponse])
async def list_users(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(connection.get_docs_db),
    admin: UserResponse = Depends(require_admin),
):
    """List all users (admin only)."""
    users = await users_service.list_users(db, skip=skip, limit=limit)
    return [
        UserResponse(
            id=u.id,
            username=u.username,
            role=u.role,
            is_active=u.is_active,
            created_at=u.created_at,
        )
        for u in users
    ]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(connection.get_docs_db),
    admin: UserResponse = Depends(require_admin),
):
    """Get a user by ID (admin only)."""
    user = await users_service.get_user_by_id(db, str(user_id))

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UserUpdate,
    request_state: Request,
    db: AsyncSession = Depends(connection.get_docs_db),
    admin: UserResponse = Depends(require_admin),
):
    """Update a user (admin only)."""
    user = await users_service.update_user(
        db,
        str(user_id),
        username=request.username,
        password=request.password,
        role=request.role.value if request.role else None,
        is_active=request.is_active,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(connection.get_docs_db),
    admin: UserResponse = Depends(require_admin),
):
    """Delete a user (admin only)."""
    success = await users_service.delete_user(db, str(user_id))

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
