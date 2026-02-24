"""Config API routes for system and user configuration."""

import uuid

import yaml
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from mywebui import storage
from mywebui.config import get_config

router = APIRouter()


class SystemConfigResponse(BaseModel):
    """System configuration response."""
    version: str
    server: dict
    security: dict
    models: dict
    tools: dict
    comfyui: dict


class ProfileConfigResponse(BaseModel):
    """User profile configuration response."""
    username: str
    display_name: str
    preferences: dict


class ProfileConfigUpdate(BaseModel):
    """User profile configuration update."""
    display_name: str | None = None
    preferences: dict | None = None


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


@router.get("/system", response_model=SystemConfigResponse)
async def get_system_config(
    current: dict = Depends(require_admin),
):
    """Get system configuration (admin only)."""
    config = get_config()
    
    return SystemConfigResponse(
        version="1.0",
        server=config.server.model_dump(),
        security=config.security.model_dump(),
        models=config.models.model_dump(),
        tools=config.tools.model_dump(),
        comfyui=config.comfyui.model_dump(),
    )


@router.patch("/system")
async def update_system_config(
    config_data: dict,
    current: dict = Depends(require_admin),
):
    """Update system configuration (admin only)."""
    config_path = storage.get_config_dir() / "system.yaml"
    
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)
    
    return {"success": True}


@router.get("/profile", response_model=ProfileConfigResponse)
async def get_profile_config(
    current: dict = Depends(get_current_user),
):
    """Get user profile configuration."""
    profile_path = storage.get_user_dir(current["username"]) / "profile.yaml"
    
    if profile_path.exists():
        with open(profile_path) as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {
            "username": current["username"],
            "display_name": current["username"],
            "preferences": {
                "theme": "dark",
            },
        }
    
    return ProfileConfigResponse(
        username=data.get("username", current["username"]),
        display_name=data.get("display_name", current["username"]),
        preferences=data.get("preferences", {}),
    )


@router.patch("/profile", response_model=ProfileConfigResponse)
async def update_profile_config(
    request: ProfileConfigUpdate,
    current: dict = Depends(get_current_user),
):
    """Update user profile configuration."""
    profile_path = storage.get_user_dir(current["username"]) / "profile.yaml"
    
    if profile_path.exists():
        with open(profile_path) as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {
            "username": current["username"],
            "display_name": current["username"],
            "preferences": {},
        }
    
    if request.display_name is not None:
        data["display_name"] = request.display_name
    
    if request.preferences is not None:
        data["preferences"] = request.preferences
    
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(profile_path, "w") as f:
        yaml.dump(data, f)
    
    return ProfileConfigResponse(
        username=data.get("username", current["username"]),
        display_name=data.get("display_name", current["username"]),
        preferences=data.get("preferences", {}),
    )
