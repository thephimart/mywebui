"""Tools API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from mywebui.core import audit as audit_core
from mywebui.core.tools import get_tool_registry
from mywebui.db import connection

router = APIRouter()


class ToolRunRequest(BaseModel):
    """Tool execution request."""

    tool_name: str
    arguments: dict[str, Any] = {}


class ToolRunResponse(BaseModel):
    """Tool execution response."""

    success: bool
    output: str
    logs: dict[str, Any]
    error: str | None = None


class StubResponse(BaseModel):
    """Response for intentionally unsupported features."""

    status_code: int
    detail: str
    feature: str


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


@router.get("/list")
async def list_tools(
    request: Request,
    current: dict = Depends(get_current_user),
):
    """List all available tools."""
    registry = get_tool_registry()
    return {"tools": registry.list_tools()}


@router.post("/run", response_model=ToolRunResponse)
async def run_tool(
    request: ToolRunRequest,
    http_request: Request,
    current: dict = Depends(get_current_user),
):
    """Run a tool with given arguments."""
    registry = get_tool_registry()

    result = await registry.execute(
        request.tool_name,
        **request.arguments,
    )

    return ToolRunResponse(
        success=result.success,
        output=result.output,
        logs=result.logs,
        error=result.error,
    )


@router.post("/exec_python", response_model=StubResponse, status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def exec_python(
    request: Request,
    current: dict = Depends(get_current_user),
    db: AsyncSession = Depends(connection.get_audit_db),
):
    """Stub for Python execution - intentionally not implemented.

    Code execution is a significant security risk and is not supported.
    All execution attempts are logged.
    """
    await audit_core.log_tool_command(
        db,
        user_id=current["user_id"],
        tool="exec_python",
        status="blocked",
        reason="intentionally_not_implemented",
    )
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="exec_python is intentionally not implemented for security reasons",
    )


@router.post("/exec_shell", response_model=StubResponse, status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def exec_shell(
    request: Request,
    current: dict = Depends(get_current_user),
    db: AsyncSession = Depends(connection.get_audit_db),
):
    """Stub for shell command execution - intentionally not implemented.

    Shell execution is a significant security risk and is not supported.
    All execution attempts are logged.
    """
    await audit_core.log_tool_command(
        db,
        user_id=current["user_id"],
        tool="exec_shell",
        status="blocked",
        reason="intentionally_not_implemented",
    )
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="exec_shell is intentionally not implemented for security reasons",
    )
