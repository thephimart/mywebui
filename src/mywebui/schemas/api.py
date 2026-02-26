"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class UserRole(StrEnum):
    """User role enum."""

    ADMIN = "admin"
    USER = "user"


class UserCreate(BaseModel):
    """User creation request."""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.USER


class UserUpdate(BaseModel):
    """User update request."""

    username: str | None = Field(None, min_length=3, max_length=50)
    password: str | None = Field(None, min_length=8)
    role: UserRole | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    """User response."""

    id: str
    username: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """Login request."""

    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class LogoutResponse(BaseModel):
    """Logout response."""

    success: bool


class SessionResponse(BaseModel):
    """Session response."""

    session_id: str
    user_id: str
    issued_at: datetime
    expires_at: datetime
    last_activity: datetime
    revoked: bool

    class Config:
        from_attributes = True


class ListSessionsResponse(BaseModel):
    """List sessions response."""

    sessions: list[SessionResponse]
    total: int


class AuditEventResponse(BaseModel):
    """Audit event response."""

    id: str
    timestamp: datetime
    user_id: str | None
    event_type: str
    details: dict
    request_id: str | None

    class Config:
        from_attributes = True


class ListAuditEventsResponse(BaseModel):
    """List audit events response."""

    events: list[AuditEventResponse]
    total: int
