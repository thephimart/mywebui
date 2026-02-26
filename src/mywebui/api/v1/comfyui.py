"""ComfyUI API routes for workflow execution."""

import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from mywebui.config import get_config

router = APIRouter()


class WorkflowRunRequest(BaseModel):
    """Workflow run request."""
    workflow: dict
    input: dict = {}


class WorkflowRunResponse(BaseModel):
    """Workflow run response."""
    job_id: uuid.UUID
    status: str


class WorkflowStatusResponse(BaseModel):
    """Workflow status response."""
    job_id: uuid.UUID
    status: str
    progress: int | None = None
    output: dict | None = None


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
    if not hasattr(request.state, "role") or request.state.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return {
        "user_id": request.state.user_id,
        "username": request.state.username,
    }


@router.post("/run", response_model=WorkflowRunResponse)
async def run_workflow(
    request: WorkflowRunRequest,
    current: dict = Depends(get_current_user),
):
    """Run a ComfyUI workflow."""
    config = get_config()

    if config.comfyui.mode != "local":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ComfyUI is not enabled",
        )

    comfyui_url = config.comfyui.url

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{comfyui_url}/prompt",
                json={
                    "prompt": request.workflow,
                    "extra_data": {"extra_pnginfo": {"workflow": request.workflow}},
                },
                timeout=30.0,
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"ComfyUI error: {response.text}",
                )

            data = response.json()
            prompt_id = data.get("prompt_id")

            return WorkflowRunResponse(
                job_id=uuid.UUID(prompt_id) if prompt_id else uuid.uuid4(),
                status="queued",
            )

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to ComfyUI: {str(e)}",
        )


@router.get("/status/{job_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    job_id: uuid.UUID,
    current: dict = Depends(get_current_user),
):
    """Get workflow status."""
    config = get_config()

    if config.comfyui.mode != "local":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ComfyUI is not enabled",
        )

    comfyui_url = config.comfyui.url

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{comfyui_url}/history/{job_id}",
                timeout=10.0,
            )

            if response.status_code == 404:
                return WorkflowStatusResponse(
                    job_id=job_id,
                    status="queued",
                    progress=None,
                    output=None,
                )

            data = response.json()
            job_data = data.get(str(job_id), {})

            status_value = "running"
            if job_data.get("outputs"):
                status_value = "completed"
            elif job_data.get("status"):
                status_value = "running"

            return WorkflowStatusResponse(
                job_id=job_id,
                status=status_value,
                progress=job_data.get("status", {}).get("exec_info", {}).get("progress"),
                output=job_data.get("outputs"),
            )

    except httpx.RequestError:
        return WorkflowStatusResponse(
            job_id=job_id,
            status="unknown",
            progress=None,
            output=None,
        )
