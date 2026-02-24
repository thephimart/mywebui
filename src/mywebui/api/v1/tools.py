"""Tools API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from mywebui.core.tools import get_tool_registry

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
