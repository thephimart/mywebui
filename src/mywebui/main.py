"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mywebui import storage
from mywebui.api.v1 import (
    attachments,
    audit,
    auth,
    chat,
    comfyui,
    config,
    docs,
    models,
    sessions,
    tools,
    users,
    wizard,
)
from mywebui.middleware import AuthMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    storage.init_storage()
    from mywebui.db import connection

    connection.init_docs_db()
    yield


app = FastAPI(
    title="mywebui",
    description="Local-first Web UI for AI and automation workloads",
    version="0.1.0a1",
    lifespan=lifespan,
)

app.add_middleware(AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(tools.router, prefix="/api/v1/tools", tags=["tools"])
app.include_router(attachments.router, prefix="/api/v1/attachments", tags=["attachments"])
app.include_router(docs.router, prefix="/api/v1/docs", tags=["docs"])
app.include_router(comfyui.router, prefix="/api/v1/comfyui", tags=["comfyui"])
app.include_router(models.router, prefix="/api/v1/models", tags=["models"])
app.include_router(config.router, prefix="/api/v1/config", tags=["config"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["audit"])
app.include_router(wizard.router, prefix="/api/v1/wizard", tags=["wizard"])


@app.get("/api/v1/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0a1"}


def main() -> None:
    """Run the application."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
