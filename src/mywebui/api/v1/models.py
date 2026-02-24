"""Models API routes for model management."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from mywebui.config import get_config

router = APIRouter()


class ModelConfig(BaseModel):
    """Model configuration."""
    provider: str
    url: str
    model: str
    api_key: str | None = None


class ModelTestRequest(BaseModel):
    """Model test request."""
    url: str
    model: str
    api_key: str | None = None


class ModelTestResponse(BaseModel):
    """Model test response."""
    success: bool
    message: str
    latency_ms: float | None = None


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


@router.get("/list")
async def list_models(
    current: dict = Depends(require_admin),
):
    """List configured models (admin only)."""
    config = get_config()
    
    return {
        "models": {
            "main": config.models.main,
            "summarizer": config.models.summarizer,
            "embedding": config.models.embedding,
            "image_embedding": config.models.image_embedding,
            "tts": config.models.tts,
        }
    }


@router.post("/test", response_model=ModelTestResponse)
async def test_model(
    request: ModelTestRequest,
    current: dict = Depends(require_admin),
):
    """Test a model connection (admin only)."""
    import httpx
    import time
    
    try:
        start = time.time()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{request.url}/v1/chat/completions",
                json={
                    "model": request.model,
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 10,
                },
                headers={"Authorization": f"Bearer {request.api_key}"} if request.api_key else {},
                timeout=30.0,
            )
            
            latency = (time.time() - start) * 1000
        
        if response.status_code == 200:
            return ModelTestResponse(
                success=True,
                message="Model connected successfully",
                latency_ms=latency,
            )
        else:
            return ModelTestResponse(
                success=False,
                message=f"Error: {response.status_code}",
                latency_ms=latency,
            )
    
    except Exception as e:
        return ModelTestResponse(
            success=False,
            message=str(e),
            latency_ms=None,
        )


@router.post("/update")
async def update_model_config(
    role: str,
    config: ModelConfig,
    current: dict = Depends(require_admin),
):
    """Update a model configuration (admin only)."""
    from mywebui import storage
    import yaml
    
    config_path = storage.get_config_dir() / "system.yaml"
    
    if config_path.exists():
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {"models": {}}
    
    data.setdefault("models", {})
    data["models"][role] = {
        "provider": config.provider,
        "url": config.url,
        "model": config.model,
    }
    
    if config.api_key:
        data["models"][role]["api_key"] = config.api_key
    
    with open(config_path, "w") as f:
        yaml.dump(data, f)
    
    return {"success": True}
