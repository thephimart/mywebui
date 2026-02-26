"""Configuration management."""

from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class ProviderType(StrEnum):
    """Model provider types."""

    OPENAI_COMPATIBLE = "openai-compatible"
    LLAMA_SERVER = "llama-server"
    OLLAMA = "ollama"


class ModelConfig(BaseModel):
    """Individual model configuration."""

    provider: str = "openai-compatible"
    url: str = ""
    model: str = ""
    api_key: str | None = None


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

    main: ModelConfig = ModelConfig()
    summarizer: ModelConfig = ModelConfig()
    embedding: ModelConfig = ModelConfig()
    image_embedding: ModelConfig = ModelConfig()
    tts: ModelConfig = ModelConfig()


class ToolsConfig(BaseModel):
    """Tools configuration."""

    filesystem: dict = {"enabled": True, "allowed_paths": []}
    web: dict = {"enabled": False, "interact_enabled": False}


class RAGConfig(BaseModel):
    """RAG configuration."""

    chunk_size: int = 512
    chunk_overlap: int = 96
    embedding_ctx_size: int = 8192
    embedding_dimension: int = 2048
    mmr_lambda: float = 0.5
    text_weight: float = 0.7
    image_weight: float = 0.3


class ModalityConfig(BaseModel):
    """Modality gating configuration."""

    default_mode: str = "hybrid"
    text_only_enabled: bool = True
    image_only_enabled: bool = True
    hybrid_enabled: bool = True


class ComfyUIConfig(BaseModel):
    """ComfyUI configuration."""

    mode: str = "local"
    url: str = "http://localhost:8188"
    limits: dict = {}


class Config(BaseSettings):
    """Application configuration."""

    model_config = {"env_prefix": "MYWEBUI_"}

    debug: bool = False

    server: ServerConfig = ServerConfig()
    security: SecurityConfig = SecurityConfig()
    models: ModelsConfig = ModelsConfig()
    tools: ToolsConfig = ToolsConfig()
    rag: RAGConfig = RAGConfig()
    comfyui: ComfyUIConfig = ComfyUIConfig()
    modality: ModalityConfig = ModalityConfig()

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


@lru_cache
def get_config() -> Config:
    """Get the configuration."""
    config = Config()

    config_path = config.data_dir / "config" / "system.yaml"
    if config_path.exists():
        with open(config_path) as f:
            data = yaml.safe_load(f)
            if data:
                _merge_config(config, data)

    return config


def _merge_config(config: Config, data: dict[str, Any]) -> None:
    """Merge YAML data into config, properly instantiating nested models."""
    for key, value in data.items():
        if not hasattr(config, key):
            continue

        attr = getattr(config, key)
        if hasattr(attr, "model_dump") and isinstance(value, dict):
            merged = {**attr.model_dump(), **value}
            if hasattr(attr, "model_validate"):
                setattr(config, key, attr.model_validate(merged))
            else:
                setattr(config, key, type(attr)(**merged))
        else:
            setattr(config, key, value)
