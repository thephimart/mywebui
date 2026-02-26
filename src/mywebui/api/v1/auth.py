"""Authentication API routes."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from mywebui.core import auth as auth_service
from mywebui.core import users as users_service
from mywebui.db import connection
from mywebui.schemas.api import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    UserCreate,
    UserResponse,
)

router = APIRouter()


async def get_current_user_from_cookie(
    request: Request,
    db: AsyncSession = Depends(connection.get_docs_db),
) -> UserResponse:
    """Get current user from session cookie."""
    token = request.cookies.get("session_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    if not hasattr(request.state, "username"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    factory = connection.get_user_session_factory(request.state.username)
    async with factory() as udb:
        session = await auth_service.get_session_by_token(udb, token)

        if session is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session",
            )

        if session.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired",
            )

        await auth_service.refresh_session(udb, session)

    return UserResponse(
        id=request.state.user_id,
        username=request.state.username,
        role=request.state.role,
        is_active=True,
        created_at=datetime.utcnow(),
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserCreate,
    db: AsyncSession = Depends(connection.get_docs_db),
):
    """Register a new user."""
    existing_user = await users_service.get_user_by_username(db, request.username)

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    user = await users_service.create_user(
        db,
        username=request.username,
        password=request.password,
        role=request.role.value,
    )

    connection.get_user_engine(request.username)

    return UserResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    http_response: JSONResponse,
    db: AsyncSession = Depends(connection.get_docs_db),
):
    """Login user and create session."""
    user = await users_service.authenticate_user(db, request.username, request.password)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    connection.get_user_engine(user.username)

    factory = connection.get_user_session_factory(user.username)
    async with factory() as udb:
        session, token = await auth_service.create_session(udb, user.id, user.username)

    http_response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        samesite="lax",
        expires=session.expires_at.replace(tzinfo=UTC),
    )

    return LoginResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            username=user.username,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
        ),
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    http_response: JSONResponse,
):
    """Logout user and revoke session."""
    token = request.cookies.get("session_token")

    if token and hasattr(request.state, "username"):
        factory = connection.get_user_session_factory(request.state.username)
        async with factory() as udb:
            session = await auth_service.get_session_by_token(udb, token)
            if session:
                await auth_service.revoke_session(udb, session.session_id)

    http_response.delete_cookie("session_token")

    return LogoutResponse(success=True)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: UserResponse = Depends(get_current_user_from_cookie),
):
    """Get current user info."""
    return current_user
