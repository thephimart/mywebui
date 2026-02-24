"""Storage initialization and directory management."""

from pathlib import Path


def get_storage_dir() -> Path:
    """Get the storage directory path."""
    return Path.home() / ".mywebui"


def get_user_dir(username: str) -> Path:
    """Get the user-specific directory."""
    return get_storage_dir() / "users" / username


def get_docs_dir() -> Path:
    """Get the docs directory."""
    return get_storage_dir() / "docs"


def get_audit_dir() -> Path:
    """Get the audit directory."""
    return get_storage_dir() / "audit"


def get_logs_dir() -> Path:
    """Get the logs directory."""
    return get_storage_dir() / "logs"


def get_config_dir() -> Path:
    """Get the config directory."""
    return get_storage_dir() / "config"


def get_workflows_dir() -> Path:
    """Get the workflows directory."""
    return get_config_dir() / "workflows"


def get_media_dir() -> Path:
    """Get the media directory."""
    return get_docs_dir() / "media"


def get_attachments_dir(username: str) -> Path:
    """Get the user attachments directory."""
    return get_user_dir(username) / "attachments"


def ensure_dirs() -> None:
    """Ensure all storage directories exist."""
    storage = get_storage_dir()

    dirs = [
        storage / "users",
        get_docs_dir(),
        get_audit_dir(),
        get_logs_dir(),
        get_config_dir(),
        get_workflows_dir(),
        get_media_dir(),
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def ensure_user_dir(username: str) -> Path:
    """Ensure user-specific directory exists."""
    user_dir = get_user_dir(username)
    user_dir.mkdir(parents=True, exist_ok=True)

    (user_dir / "attachments").mkdir(parents=True, exist_ok=True)

    return user_dir


def get_docs_db_path() -> Path:
    """Get the docs database path."""
    return get_docs_dir() / "docs.db"


def get_audit_db_path() -> Path:
    """Get the audit database path."""
    return get_audit_dir() / "events.db"


def get_user_db_path(username: str) -> Path:
    """Get the user history database path."""
    return get_user_dir(username) / "history.db"


def get_docs_db_url() -> str:
    """Get the docs database URL."""
    return f"sqlite+aiosqlite:///{get_docs_db_path()}"


def get_audit_db_url() -> str:
    """Get the audit database URL."""
    return f"sqlite+aiosqlite:///{get_audit_db_path()}"


def get_user_db_url(username: str) -> str:
    """Get the user history database URL."""
    return f"sqlite+aiosqlite:///{get_user_db_path(username)}"


def init_storage() -> None:
    """Initialize storage - create directories and default config."""
    ensure_dirs()

    config_dir = get_config_dir()
    system_config = config_dir / "system.yaml"

    if not system_config.exists():
        default_config = """version: "1.0"

server:
  host: "0.0.0.0"
  port: 8000

security:
  session_rolling_ttl_hours: 24
  session_absolute_max_days: 7

models:
  main:
    provider: openai-compatible
    url: "http://localhost:11434"
    model: "llama3"
  summarizer:
    provider: openai-compatible
    url: "http://localhost:11434"
    model: "llama3"
  embedding:
    provider: openai-compatible
    url: "http://localhost:11434"
    model: "nomic-embed-text"

tools:
  filesystem:
    enabled: true
    allowed_paths: []
  web:
    enabled: false

comfyui:
  mode: local
  url: "http://localhost:8188"
  limits:
    max_steps: 100
    max_resolution: 1024
"""
        with open(system_config, "w") as f:
            f.write(default_config)
