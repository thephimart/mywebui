"""Wizard API routes for first-run setup."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from mywebui import storage

router = APIRouter()


class WizardStatusResponse(BaseModel):
    """Wizard status response."""
    state: str
    step: int | None = None


class AdminCreateRequest(BaseModel):
    """Admin user creation request."""
    username: str
    password: str


class AdminCreateResponse(BaseModel):
    """Admin user creation response."""
    user_id: str
    username: str


def _is_initialized() -> bool:
    """Check if the system has been initialized."""
    config_path = storage.get_config_dir() / "system.yaml"
    return config_path.exists()


@router.get("/status", response_model=WizardStatusResponse)
async def get_wizard_status():
    """Get the current wizard state."""
    if not _is_initialized():
        return WizardStatusResponse(
            state="not_started",
            step=None,
        )
    
    return WizardStatusResponse(
        state="completed",
        step=None,
    )


@router.post("/admin", response_model=AdminCreateResponse)
async def create_admin_user(request: AdminCreateRequest):
    """Create the first admin user (only available during setup)."""
    config_path = storage.get_config_dir() / "system.yaml"
    
    if config_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="System already initialized",
        )
    
    storage.init_storage()
    
    from mywebui.db import connection
    from mywebui.db.models import Base
    from mywebui.core.users import create_user
    
    engine = connection.get_docs_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    factory = connection.get_docs_session_factory()
    async with factory() as db:
        user = await create_user(
            db,
            username=request.username,
            password=request.password,
            role="admin",
        )
    
    return AdminCreateResponse(
        user_id=str(user.id),
        username=user.username,
    )
