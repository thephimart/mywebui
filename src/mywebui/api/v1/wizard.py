"""Wizard API routes for first-run setup."""

from pathlib import Path
from shutil import move
from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from mywebui import storage
from mywebui.db import connection

router = APIRouter()


class WizardStatusResponse(BaseModel):
    """Wizard status response."""

    state: str
    step: int | None = None
    existing_data: dict | None = None


class AdminCreateRequest(BaseModel):
    """Admin user creation request."""

    username: str
    password: str


class AdminCreateResponse(BaseModel):
    """Admin user creation response."""

    user_id: str
    username: str


class WizardCompleteRequest(BaseModel):
    """Request to complete wizard with existing data handling."""

    username: str
    password: str
    action: Literal["reuse", "backup", "abort"] = "reuse"


class WizardCompleteResponse(BaseModel):
    """Response for wizard completion."""

    user_id: str
    username: str
    action_taken: str
    backup_path: str | None = None


def _detect_existing_data() -> dict | None:
    """Detect existing data in the storage directory."""
    storage_dir = storage.get_storage_dir()

    if not storage_dir.exists():
        return None

    existing = {}

    docs_db = storage.get_docs_db_path()
    if docs_db.exists():
        try:
            import sqlite3

            conn = sqlite3.connect(docs_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM documents")
            doc_count = cursor.fetchone()[0]
            conn.close()
            existing["users"] = user_count
            existing["documents"] = doc_count
            existing["docs_db_exists"] = True
        except Exception:
            existing["docs_db_exists"] = True

    audit_db = storage.get_audit_db_path()
    if audit_db.exists():
        existing["audit_db_exists"] = True

    users_dir = storage.get_storage_dir() / "users"
    if users_dir.exists():
        existing["user_dirs"] = len(list(users_dir.iterdir()))

    return existing if existing else None


def _is_initialized() -> bool:
    """Check if the system has been initialized."""
    config_path = storage.get_config_dir() / "system.yaml"
    return config_path.exists()


@router.get("/status", response_model=WizardStatusResponse)
async def get_wizard_status():
    """Get the current wizard state."""
    existing_data = _detect_existing_data()

    if not _is_initialized():
        if existing_data:
            return WizardStatusResponse(
                state="needs_setup_with_existing_data",
                step=1,
                existing_data=existing_data,
            )
        return WizardStatusResponse(
            state="not_started",
            step=None,
            existing_data=None,
        )

    return WizardStatusResponse(
        state="completed",
        step=None,
        existing_data=existing_data,
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

    from mywebui.core.users import create_user

    connection.init_docs_db()

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


@router.post("/complete", response_model=WizardCompleteResponse)
async def complete_wizard(request: WizardCompleteRequest):
    """Complete wizard with existing data handling.

    Actions:
    - reuse: Use existing data as-is (default)
    - backup: Backup existing data to ~/.mywebui.backup.{timestamp} and start fresh
    - abort: Do nothing, return error
    """
    existing_data = _detect_existing_data()

    if request.action == "abort":
        if existing_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Existing data detected. Use action=backup or action=reuse, or action=abort to cancel.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No action specified",
        )

    backup_dir: Path | None = None
    if request.action == "backup" and existing_data:
        from datetime import datetime

        backup_dir = storage.get_storage_dir().parent / f".mywebui.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        move(str(storage.get_storage_dir()), str(backup_dir))
        existing_data = None

    storage.init_storage()

    from mywebui.core.users import create_user

    connection.init_docs_db()

    factory = connection.get_docs_session_factory()
    async with factory() as db:
        user = await create_user(
            db,
            username=request.username,
            password=request.password,
            role="admin",
        )

    backup_path = str(backup_dir) if backup_dir else None

    return WizardCompleteResponse(
        user_id=str(user.id),
        username=request.username,
        action_taken=request.action,
        backup_path=backup_path,
    )
