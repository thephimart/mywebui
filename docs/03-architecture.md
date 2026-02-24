# High-Level Architecture

## Libraries

- **Framework**: FastAPI
- **Server**: uvicorn (ASGI server)

```
WebUI (React / TypeScript)
     |
Python Backend (FastAPI)
  ├─ Auth & Sessions
  ├─ Chat & Streaming
  ├─ Agent Orchestrator
  ├─ Tool Router
  ├─ RAG / Retrieval
  ├─ Attachments & Ingestion
  ├─ Config & Admin APIs
     |
Agent Runtime
     |
Models (HTTP endpoints)
Tools (search, crawl, exec, ComfyUI)
SQLite (docs, vectors, history, audit)
```

All inter-component communication is **explicit JSON APIs**.

---

## Frontend Authentication Strategy

### Session Transport

- **HTTP-only cookies** (NOT localStorage or JS-managed headers)
- Same-origin protection, automatic sending with requests

```
Set-Cookie: session=<uuid>; HttpOnly; SameSite=Lax; Path=/
```

### WebSocket Auth

Same cookie is sent automatically when browser opens WebSocket connection. Backend reads `Cookie` header during WS handshake.

### Why This Approach

- No XSS token theft (HttpOnly blocks JS access)
- No frontend auth logic
- Works with fetch, forms, WebSockets automatically
- Stateless on wire, stateful in backend (explicit control)

### CSRF Protection

- `SameSite=Lax` is sufficient for most UIs
- For mutations: custom header `X-Requested-With` or double-submit token

### Backend Session Store

```python
class Session:
    user_id: str
    created: float
    expires: float
    scopes: set[str]
```

Storage: dict (single process), `multiprocessing.Manager().dict`, or Redis later if needed.

---

## API Routing Structure

```
/api/v1/
  /auth/          # Authentication (login, logout, revoke)
  /sessions/      # Session management
  /chat/          # Chat + WebSocket
  /tools/         # Tool execution
  /attachments/   # File uploads
  /docs/          # Document management
  /comfyui/       # ComfyUI integration
  /models/        # Model configuration
  /config/        # System configuration
  /users/         # User management (admin)
  /audit/         # Audit log (admin)
  /wizard/        # First-run wizard
```

---

## File Upload Limits

| Type | Limit | Rationale |
|------|-------|------------|
| Single file | 50 MB | Prevent memory issues |
| Total attachments | 1 GB per user | Disk quota |
| Image thumbnail | 256px | UI performance |

---

## Error Handling

All API errors follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message"
  }
}
```

Common error codes:

| Code | HTTP | Description |
|------|------|-------------|
| `UNAUTHORIZED` | 401 | Not logged in |
| `FORBIDDEN` | 403 | No permission |
| `NOT_FOUND` | 404 | Resource missing |
| `VALIDATION_ERROR` | 422 | Invalid input |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

- Never expose stack traces or internal paths in errors
- Log detailed errors server-side with request_id
