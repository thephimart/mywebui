"""Attachments API routes for file uploads."""

import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from mywebui.db import connection
from mywebui import storage

router = APIRouter()


class AttachmentResponse(BaseModel):
    """Attachment response."""
    id: uuid.UUID
    filename: str
    content_type: str
    size: int
    status: str
    created_at: datetime


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


@router.post("", response_model=AttachmentResponse)
async def upload_attachment(
    file: UploadFile = File(...),
    current: dict = Depends(get_current_user),
):
    """Upload an attachment."""
    attachment_id = uuid.uuid4()
    
    attachments_dir = storage.get_attachments_dir(current["username"])
    attachments_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = attachments_dir / f"{attachment_id}_{file.filename}"
    
    content = await file.read()
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    return AttachmentResponse(
        id=attachment_id,
        filename=file.filename,
        content_type=file.content_type,
        size=len(content),
        status="uploaded",
        created_at=datetime.utcnow(),
    )


@router.get("/{attachment_id}", response_model=AttachmentResponse)
async def get_attachment(
    attachment_id: uuid.UUID,
    current: dict = Depends(get_current_user),
):
    """Get attachment metadata."""
    attachments_dir = storage.get_attachments_dir(current["username"])
    
    for file_path in attachments_dir.glob(f"{attachment_id}_*"):
        return AttachmentResponse(
            id=attachment_id,
            filename=file_path.name.split("_", 1)[1],
            content_type="application/octet-stream",
            size=file_path.stat().st_size,
            status="uploaded",
            created_at=datetime.utcnow(),
        )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Attachment not found",
    )


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    attachment_id: uuid.UUID,
    current: dict = Depends(get_current_user),
):
    """Delete an attachment."""
    attachments_dir = storage.get_attachments_dir(current["username"])
    
    for file_path in attachments_dir.glob(f"{attachment_id}_*"):
        file_path.unlink()
        return
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Attachment not found",
    )
