"""Configuration management."""

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class ServerConfig(BaseModel):
    """Server configuration."""
    host: str = "0.0.0.0"
    port: int = 8000


class SecurityConfig(BaseModel):
    """Security configuration."""
    session_rolling_ttl_hours: int = 24
    session_absolute_max_days: int = 7


class ModelsConfig(BaseModel):
    """Models configuration."""
    main: dict = {}
    summarizer: dict = {}
    embedding: dict = {}
    image_embedding: dict = {}
    tts: dict = {}


class ToolsConfig(BaseModel):
    """Tools configuration."""
    filesystem: dict = {"enabled": True, "allowed_paths": []}
    web: dict = {"enabled": False}


class ComfyUIConfig(BaseModel):
    """ComfyUI configuration."""
    mode: str = "local"
    url: str = "http://localhost:8188"
    limits: dict = {}


class Config(BaseSettings):
    """Application configuration."""

    debug: bool = False

    server: ServerConfig = ServerConfig()
    security: SecurityConfig = SecurityConfig()
    models: ModelsConfig = ModelsConfig()
    tools: ToolsConfig = ToolsConfig()
    comfyui: ComfyUIConfig = ComfyUIConfig()

    @property
    def data_dir(self) -> Path:
        """Get the data directory."""
        return Path.home() / ".mywebui"

    @property
    def database_url(self) -> str:
        """Get the database URL."""
        return f"sqlite+aiosqlite:///{self.data_dir}/docs/docs.db"

    @property
    def audit_database_url(self) -> str:
        """Get the audit database URL."""
        return f"sqlite+aiosqlite:///{self.data_dir}/audit/events.db"

    class Config:
        env_prefix = "MYWEBUI_"


@lru_cache
def get_config() -> Config:
    """Get the configuration."""
    config = Config()

    config_path = config.data_dir / "config" / "system.yaml"
    if config_path.exists():
        with open(config_path) as f:
            data = yaml.safe_load(f)
            if data:
                for key, value in data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)

    return config
