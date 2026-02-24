# Model Roles (Independently Configurable)

## Libraries

- **HTTP Client**: httpx (async, timeout support)
- **TTS**: Kokoro

| Role                  | Purpose                        |
| --------------------- | ------------------------------ |
| Main Agent Model      | Chat, reasoning, tool planning |
| Summarizer Model      | Session & doc summaries        |
| Text Embedding Model  | Text → vectors                 |
| Image Embedding Model | Image → vectors                |
| TTS Model             | Text → Speech (Text-to-Speech) |

Each role configurable via WebUI:

- Endpoint URL
- Model name
- Parameters
- Test connection button

---

## Internal Model API (Canonical)

All model interactions use a single internal protocol. External providers are adapted.

### Chat Interface

```python
class ChatModel:
    def generate(
        self,
        messages: list[Message],
        *,
        temperature: float,
        max_tokens: int,
        tools: list[Tool] | None = None,
        stream: bool = False,
    ) -> ChatResult: ...
```

### Embedding Interface

```python
class EmbeddingModel:
    def embed(
        self,
        texts: list[str],
    ) -> list[list[float]]: ...
```

### TTS Interface

```python
class TTSModel:
    def speak(
        self,
        text: str,
        voice: str | None = None,
    ) -> bytes: ...  # Audio bytes (MP3/WAV)
```

### Providers (Adapters)

| Priority | Provider | Notes |
|----------|----------|-------|
| 1 | **OpenAI-compatible** | Default backbone (Ollama, LM Studio, vLLM, OpenRouter) |
| 2 | Anthropic | Convert to internal format (don't leak upstream) |
| 3 | Ollama (native) | Thin adapter if not OpenAI-compatible |

**Key principle**: Internal code never knows which provider is used. Adapters translate at the boundary.
