"""Model adapters for different LLM providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Literal

import httpx

from mywebui.config import get_config


@dataclass
class Message:
    """Chat message."""

    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_call_id: str | None = None
    tool_calls: list[dict[str, Any]] | None = None


@dataclass
class ChatChoice:
    """Chat completion choice."""

    index: int
    message: Message
    finish_reason: str | None = None


@dataclass
class ChatUsage:
    """Token usage information."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class ChatResult:
    """Chat completion result."""

    id: str
    choices: list[ChatChoice]
    usage: ChatUsage
    model: str


@dataclass
class EmbeddingResult:
    """Embedding result."""

    embeddings: list[list[float]]
    model: str


@dataclass
class ImageInput:
    """Image input for VL embedding models."""

    bytes: bytes
    format: str | None = None


TextInput = str
EmbeddingInput = str | ImageInput


class BaseChatModel(ABC):
    """Base class for chat models."""

    @abstractmethod
    async def generate(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: list[dict[str, Any]] | None = None,
        stream: bool = False,
    ) -> ChatResult:
        """Generate chat completion."""
        pass


class OpenAICompatibleChatModel(BaseChatModel):
    """OpenAI-compatible chat model (Ollama, LM Studio, vLLM, OpenRouter)."""

    def __init__(self, url: str, model: str, api_key: str | None = None):
        self.url = url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.url,
                timeout=60.0,
            )
        return self._client

    async def generate(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: list[dict[str, Any]] | None = None,
        stream: bool = False,
    ) -> ChatResult:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if tools:
            payload["tools"] = tools

        if stream:
            payload["stream"] = True

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        response = await self.client.post(
            "/v1/chat/completions",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

        choices = [
            ChatChoice(
                index=choice["index"],
                message=Message(
                    role=choice["message"]["role"],
                    content=choice["message"].get("content", ""),
                ),
                finish_reason=choice.get("finish_reason"),
            )
            for choice in data["choices"]
        ]

        usage = data.get("usage", {})
        chat_usage = ChatUsage(
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )

        return ChatResult(
            id=data["id"],
            choices=choices,
            usage=chat_usage,
            model=data["model"],
        )


class BaseEmbeddingModel(ABC):
    """Base class for embedding models."""

    @abstractmethod
    async def embed(self, texts: list[str]) -> EmbeddingResult:
        """Generate embeddings for texts."""
        pass


class OpenAICompatibleEmbeddingModel(BaseEmbeddingModel):
    """OpenAI-compatible embedding model."""

    def __init__(
        self,
        url: str,
        model: str,
        api_key: str | None = None,
        dimension: int | None = None,
    ):
        self.url = url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.dimension = dimension
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.url,
                timeout=30.0,
            )
        return self._client

    async def embed(self, texts: list[str]) -> EmbeddingResult:
        payload = {
            "model": self.model,
            "input": texts,
        }

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        response = await self.client.post(
            "/v1/embeddings",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

        embeddings = [item["embedding"] for item in data["data"]]

        return EmbeddingResult(
            embeddings=embeddings,
            model=data["model"],
        )


class BaseVLEmbeddingModel(ABC):
    """Base class for vision-language embedding models."""

    @abstractmethod
    async def embed_images(self, images: list[bytes]) -> EmbeddingResult:
        """Generate embeddings for images."""
        pass


class OpenAICompatibleVLEmbeddingModel(BaseVLEmbeddingModel):
    """OpenAI-compatible vision-language embedding model.

    Supports multimodal embedding APIs that accept image URLs or base64.
    """

    def __init__(
        self,
        url: str,
        model: str,
        api_key: str | None = None,
        dimension: int | None = None,
    ):
        self.url = url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.dimension = dimension
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.url,
                timeout=60.0,
            )
        return self._client

    async def embed_images(self, images: list[bytes]) -> EmbeddingResult:
        import base64

        inputs: list[dict[str, Any]] = []
        for img_bytes in images:
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            inputs.append(
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
            )

        payload: dict[str, Any] = {
            "model": self.model,
            "input": inputs,
        }

        headers: dict[str, str] = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        response = await self.client.post(
            "/v1/embeddings",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

        embeddings = [item["embedding"] for item in data["data"]]

        return EmbeddingResult(
            embeddings=embeddings,
            model=data["model"],
        )


_chat_models: dict[str, BaseChatModel] = {}
_embedding_models: dict[str, BaseEmbeddingModel] = {}
_vl_embedding_models: dict[str, BaseVLEmbeddingModel] = {}


def get_chat_model(role: str = "main") -> BaseChatModel:
    """Get a chat model by role."""
    if role not in _chat_models:
        config = get_config()
        model_config = config.models.main if role == "main" else config.models.summarizer

        _chat_models[role] = OpenAICompatibleChatModel(
            url=model_config.get("url", "http://localhost:11434"),
            model=model_config.get("model", "llama3"),
            api_key=model_config.get("api_key"),
        )

    return _chat_models[role]


def get_embedding_model(role: str = "embedding") -> BaseEmbeddingModel:
    """Get an embedding model by role."""
    if role not in _embedding_models:
        config = get_config()
        model_config = config.models.embedding

        _embedding_models[role] = OpenAICompatibleEmbeddingModel(
            url=model_config.get("url", "http://localhost:11434"),
            model=model_config.get("model", "nomic-embed-text"),
            api_key=model_config.get("api_key"),
            dimension=config.rag.embedding_dimension,
        )

    return _embedding_models[role]


def get_vl_embedding_model(role: str = "image_embedding") -> BaseVLEmbeddingModel:
    """Get a vision-language embedding model by role."""
    if role not in _vl_embedding_models:
        config = get_config()
        model_config = config.models.image_embedding

        _vl_embedding_models[role] = OpenAICompatibleVLEmbeddingModel(
            url=model_config.get("url", "http://localhost:11434"),
            model=model_config.get("model", "qwen2-vl-2b"),
            api_key=model_config.get("api_key"),
            dimension=config.rag.embedding_dimension,
        )

    return _vl_embedding_models[role]
