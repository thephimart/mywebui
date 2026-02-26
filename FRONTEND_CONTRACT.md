# FRONTEND_CONTRACT.md

**Version**: 0.1.0-alpha  
**Last Updated**: 2026-02-26  
**Purpose**: Binding interface contract for frontend development. A frontend developer should be able to build without reading backend code.

---

## 1. Global Semantics

| Rule | Value |
|------|-------|
| Auth Model | HTTP-only cookie, session-based |
| Session Cookie | `session_token`, `HttpOnly`, `SameSite=lax` |
| CSRF | Same-site policy; no explicit CSRF token required |
| All Timestamps | ISO-8601 UTC (Python: `datetime.now(timezone.utc)`) |
| All IDs | UUIDv4 strings |
| All 501 Responses | "Planned but unavailable" - intentional feature stubs |
| Base URL | `/api/v1` |

### Excluded Paths (No Auth Required)
- `GET /api/v1/health`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/register`
- `GET /api/v1/wizard/status`
- `POST /api/v1/wizard/admin`
- Swagger/OpenAPI docs

---

## 2. Capability Flags

**Frontend Capabilities Endpoint**: `GET /api/v1/config/capabilities` (authenticated users)

**Admin System Config**: `GET /api/v1/config/system` (admin only)

Capabilities are embedded in the `tools` and `comfyui` sections of the system config response.

### Capabilities Endpoint (All Authenticated Users)

```json
{
  "capabilities": {
    "filesystem": { "enabled": true, "allowed_paths": [] },
    "web": { "enabled": false, "interact_enabled": false },
    "comfyui": { "enabled": false },
    "tts": { "enabled": false },
    "multimodal": { "enabled": false },
    "tools": {
      "exec_python": "blocked",
      "exec_shell": "blocked",
      "web_search": "available|disabled",
      "web_fetch": "available|disabled",
      "web_crawl": "available|disabled"
    }
  }
}
```

`"blocked"` = intentional 501, `"disabled"` = not configured, `"available"` = enabled and functional.

**Stability Guarantee**: Capability state values (`"blocked"`, `"disabled"`, `"available"`) are stable enums and will not change without a major version bump. Frontend may safely hardcode conditional logic against these values.

### System Config Response Schema
```json
{
  "version": "1.0",
  "server": { "host": "0.0.0.0", "port": 8000 },
  "security": { "session_rolling_ttl_hours": 24, "session_absolute_max_days": 7 },
  "models": {
    "main": { "provider": "openai-compatible", "url": "", "model": "" },
    "summarizer": { "provider": "openai-compatible", "url": "", "model": "" },
    "embedding": { "provider": "openai-compatible", "url": "", "model": "" },
    "image_embedding": { "provider": "openai-compatible", "url": "", "model": "" },
    "tts": { "provider": "openai-compatible", "url": "", "model": "" }
  },
  "tools": {
    "filesystem": { "enabled": true, "allowed_paths": [] },
    "web": { "enabled": false, "interact_enabled": false }
  },
  "comfyui": {
    "mode": "local",
    "url": "http://localhost:8188",
    "limits": {}
  }
}
```

### Capability Gating Rules

| Feature | Flag Location | Enabled When |
|---------|---------------|---------------|
| exec_python | `tools` section | Never (always 501) |
| exec_shell | `tools` section | Never (always 501) |
| filesystem | `tools.filesystem.enabled` | `true` |
| web search | `tools.web.enabled` | `true` |
| ComfyUI | `comfyui.mode` | `"local"` |
| TTS | `models.tts.model` | Non-empty string |
| Image Embedding | `models.image_embedding.model` | Non-empty string |
| Multimodal Chat | `models.main` + `models.image_embedding` | Both configured |

---

## 3. Error Contract

### Canonical Error Envelope

All errors MUST conform to this shape:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {}
  }
}
```

Error codes:

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `UNAUTHORIZED` | Not authenticated | 401 |
| `INVALID_CREDENTIALS` | Login failed | 401 |
| `SESSION_EXPIRED` | Session no longer valid | 401 |
| `FORBIDDEN` | Admin access required | 403 |
| `ACCESS_DENIED` | Resource access denied | 403 |
| `NOT_FOUND` | Resource not found | 404 |
| `NOT_IMPLEMENTED` | Feature stub (501) | 501 |
| `VALIDATION_ERROR` | Request validation failed | 422 |
| `BAD_REQUEST` | Generic client error | 400 |

**Note**: FastAPI currently returns `{"detail": "..."}` for some errors. This will be normalized to the canonical envelope. Frontend should handle both shapes during transition.

### Error Codes by Endpoint

| Code | Endpoint(s) | Retryable |
|------|-------------|-----------|
| `UNAUTHORIZED` | All protected | No |
| `INVALID_CREDENTIALS` | `/auth/login` | No |
| `SESSION_EXPIRED` | All protected | No (re-login needed) |
| `FORBIDDEN` | Admin endpoints | No |
| `ACCESS_DENIED` | `/docs/{id}` | No |
| `NOT_FOUND` | `/docs/{id}`, `/attachments/{id}`, `/sessions/{id}` | No |
| `VALIDATION_ERROR` | All Pydantic-validated | No |
| `NOT_IMPLEMENTED` | `/tools/exec_python`, `/tools/exec_shell`, `/attachments/{id}/ingest` | N/A |

**Pagination**: All list endpoints use `skip` (offset) and `limit`. Default limit is 100. Ordering is stable by `created_at` DESC (newest first) unless otherwise documented.

### Streaming Errors

SSE format:
```
data: {"type": "error", "data": {"message": "Error description"}}

data: {"type": "done", "data": {}}
```

---

## 4. Auth & Session Lifecycle

### Registration
```
POST /api/v1/auth/register
Request: { "username": "string", "password": "string", "role": "user|admin" }
Response: { "id": "uuid", "username": "...", "role": "...", "is_active": true, "created_at": "ISO8601" }
```

### Login
```
POST /api/v1/auth/login
Request: { "username": "string", "password": "string" }
Response: { "access_token": "string", "token_type": "bearer", "user": {...} }
Cookie: session_token=...; HttpOnly; SameSite=lax
```

### Session Refresh
- **Rolling TTL**: 24 hours (configurable via `security.session_rolling_ttl_hours`)
- **Absolute Max**: 7 days (configurable via `security.session_absolute_max_days`)
- Sessions are auto-refreshed on each authenticated request

### Logout
```
POST /api/v1/auth/logout
Response: { "success": true }
Cookie: session_token deleted
```

### Get Current User
```
GET /api/v1/auth/me
Response: { "id": "uuid", "username": "...", "role": "...", "is_active": true, "created_at": "ISO8601" }
```

### Session Management
```
GET /api/v1/sessions
Response: {
  "sessions": [
    {
      "session_id": "uuid",
      "user_id": "uuid",
      "issued_at": "ISO8601",
      "expires_at": "ISO8601",
      "last_activity": "ISO8601",
      "revoked": false
    }
  ],
  "total": 1
}
DELETE /api/v1/sessions/{session_id}
DELETE /api/v1/sessions  (revoke all)
```

---

## 5. Chat + Streaming

### REST Fallback
```
POST /api/v1/chat/message
Request: { "content": "string", "session_id": "uuid|null" }
Response: { "msg_id": "uuid", "session_id": "uuid", "role": "user", "content": "...", "timestamp": "ISO8601" }
```

### Server-Sent Events Streaming (Primary)
```
POST /api/v1/chat/stream
Request: { "message": "string", "session_id": "uuid|null", "images": ["base64...", ...]|null }

SSE Events:
data: {"type": "assistant_delta", "data": {"content": "partial response"}}
data: {"type": "done", "data": {}}
```

### WebSocket Streaming (Alternative)
```
WS /api/v1/chat/ws

Client → Server:
{ "type": "user_message", "data": { "content": "..." } }
{ "type": "cancel" }

Server → Client:
{ "type": "assistant_delta", "data": { "content": "..." } }
{ "type": "error", "data": { "message": "..." } }
{ "type": "done", "data": {} }
```

**Cancellation**: Sending `{ "type": "cancel" }` terminates the stream. Cancellation is best-effort; the server may still emit a final `done` event after the request is cancelled.

### Multimodal (Images)
- Pass base64-encoded images in `images` array
- Format: `"data:image/jpeg;base64,{base64}"`
- Requires both `main` and `image_embedding` models configured

---

## 6. Documents & RAG

### Ingest Document
```
POST /api/v1/docs/ingest
Request: { "title": "string", "content": "string", "visibility": "private|public", "categories": [], "source": "string|null" }
Response: { "id": "uuid", "title": "...", "visibility": "...", "categories": [], "source": "...", "created_at": "ISO8601", "updated_at": "ISO8601|null" }
```

### List Documents
```
GET /api/v1/docs?visibility=private&category=foo&skip=0&limit=100
Response: { "documents": [...], "total": 10 }
```

### Get Document
```
GET /api/v1/docs/{doc_id}
Response: { "id": "...", "title": "...", "visibility": "...", "categories": [], "source": "...", "created_at": "...", "updated_at": "..." }
```

### Update Document
```
PATCH /api/v1/docs/{doc_id}
Request: { "title": "string|null", "visibility": "string|null", "categories": []|null }
Response: Updated DocumentResponse
```

### Delete Document
```
DELETE /api/v1/docs/{doc_id}
Response: 204 No Content
```

### Search
```
POST /api/v1/docs/search
Request: { "query": "string", "limit": 5, "category": "string|null" }
Response: { "results": [{ "chunk_id": "uuid", "document_id": "uuid", "text": "...", "score": 0.95, "modality": "text|image" }] }
```

**Idempotency**: Document ingest (`POST /docs/ingest`) is idempotent based on title+owner. Retries with same title will update, not duplicate.

---

## 7. Tools Contract

| Tool | Endpoint | Status | Audit Event |
|------|----------|--------|-------------|
| filesystem | `/api/v1/tools/run` | ✅ Enabled | `tool_execution` |
| web_search | `/api/v1/tools/run` | ✅ Enabled (if configured) | `tool_execution` |
| web_fetch | `/api/v1/tools/run` | ✅ Enabled (if configured) | `tool_execution` |
| web_crawl | `/api/v1/tools/run` | ✅ Enabled (if configured) | `tool_execution` |
| exec_python | `/api/v1/tools/exec_python` | ❌ 501 | `tool_command` (blocked) |
| exec_shell | `/api/v1/tools/exec_shell` | ❌ 501 | `tool_command` (blocked) |

### List Tools
```
GET /api/v1/tools/list
Response: { "tools": [{ "name": "string", "description": "string", "parameters": {...} }] }
```

### Run Tool
```
POST /api/v1/tools/run
Request: { "tool_name": "string", "arguments": {} }
Response: { "success": true|false, "output": "string", "logs": {}, "error": "string|null" }
```

**Note**: `POST /tools/run` dispatches based on `tool_name`. Blocked tools (exec_python, exec_shell) MUST return 501 even if invoked via this endpoint.

---

## 8. Attachments & Media

### Upload Attachment
```
POST /api/v1/attachments
Content-Type: multipart/form-data
File: (binary)
Response: { "id": "uuid", "filename": "string", "content_type": "...", "size": 1234, "status": "uploaded", "created_at": "ISO8601" }
```

### Get Attachment Metadata
```
GET /api/v1/attachments/{attachment_id}
Response: { "id": "uuid", "filename": "...", "content_type": "...", "size": 1234, "status": "uploaded", "created_at": "ISO8601" }
```

### Delete Attachment
```
DELETE /api/v1/attachments/{attachment_id}
Response: 204 No Content
```

### Ingest Attachment (STUB)
```
POST /api/v1/attachments/{attachment_id}/ingest
Request: { "extract_text": true, "generate_thumbnail": false }
Response: 501 Not Implemented
Detail: "Attachment ingestion is not yet implemented. Uploaded files are stored but not processed."
```

---

## 9. Wizard (First-Run Setup)

### State Machine

```
                    ┌─────────────────────┐
                    │   not_started       │
                    │   (fresh install)   │
                    └──────────┬──────────┘
                               │ POST /wizard/complete
                               │ (action=reuse|backup)
                               ▼
                    ┌─────────────────────┐
                    │      completed       │
                    └─────────────────────┘
                               ▲
                               │ (system initialized)
                    ┌──────────┴──────────┐
                    │                     │
    ┌───────────────┴───────────────┐    │
    │ needs_setup_with_existing_data│    │
    │ (existing ~/.mywebui found)   │    │
    └───────────────┬───────────────┘    │
                    │ POST /wizard/complete
                    │ (action=abort)
                    └─────────────────────┘
```

**States**:
- `not_started`: No admin user, no config - fresh install
- `needs_setup_with_existing_data`: Existing data detected, must choose action
- `completed`: System initialized, admin user exists

### Get Wizard Status
```
GET /api/v1/wizard/status
Response: { "state": "not_started|needs_setup_with_existing_data|completed", "step": 1|null, "existing_data": { "users": N, "documents": N, "docs_db_exists": true, "audit_db_exists": true, "user_dirs": N }|null }
```

### Create Admin (First Time Only)
```
POST /api/v1/wizard/admin
Request: { "username": "string", "password": "string" }
Response: { "user_id": "uuid", "username": "..." }
Error: 400 "System already initialized"
```

### Complete Wizard (With Existing Data Handling)
```
POST /api/v1/wizard/complete
Request: { "username": "string", "password": "string", "action": "reuse|backup|abort" }
Actions:
  - reuse: Use existing data as-is
  - backup: Backup to ~/.mywebui.backup.{timestamp} and start fresh
  - abort: Cancel if existing data exists

Response: { "user_id": "uuid", "username": "...", "action_taken": "...", "backup_path": "path|string|null" }
Error: 400 "Existing data detected..." (if action=abort with existing data)
```

---

## 10. Users (Admin Only)

### List Users
```
GET /api/v1/users?skip=0&limit=100
Response: [{ "id": "uuid", "username": "...", "role": "...", "is_active": true, "created_at": "ISO8601" }]
```

### Get User
```
GET /api/v1/users/{user_id}
Response: { "id": "...", "username": "...", "role": "...", "is_active": true, "created_at": "..." }
```

### Update User
```
PATCH /api/v1/users/{user_id}
Request: { "username": "string|null", "password": "string|null", "role": "admin|user|null", "is_active": true|false|null }
Response: Updated UserResponse
```

### Delete User
```
DELETE /api/v1/users/{user_id}
Response: 204 No Content
```

---

## 11. Config

### Get Capabilities (All Authenticated Users)
```
GET /api/v1/config/capabilities
Response: See Section 2 - Capability Flags
```

### Get System Config (Admin Only)
```
GET /api/v1/config/system
Response: See Section 2 - Capability Flags
```

### Update System Config
```
PATCH /api/v1/config/system
Request: { ...config object... }
Response: { "success": true }
```

### Get Profile Config (STUB - Deferred)
```
GET /api/v1/config/profile
Response: 501 Not Implemented
Code: NOT_IMPLEMENTED
Reason: Per-user profile settings deferred (Phase B3)
```

### Update Profile Config (STUB - Deferred)
```
PATCH /api/v1/config/profile
Request: { "display_name": "string|null", "preferences": {}|null }
Response: 501 Not Implemented
Code: NOT_IMPLEMENTED
Reason: Per-user profile settings deferred (Phase B3)
```

---

## 12. Models (Admin Only)

### List Models
```
GET /api/v1/models/list
Response: { "models": { "main": {...}, "summarizer": {...}, "embedding": {...}, "image_embedding": {...}, "tts": {...} } }
```

### Test Model Connection
```
POST /api/v1/models/test
Request: { "url": "string", "model": "string", "api_key": "string|null" }
Response: { "success": true|false, "message": "...", "latency_ms": 123.45 }
```

### Update Model Config
```
POST /api/v1/models/update?role=main
Request: { "provider": "openai-compatible|llama-server|ollama", "url": "string", "model": "string", "api_key": "string|null" }
Response: { "success": true }
```

---

## 13. ComfyUI

### Run Workflow
```
POST /api/v1/comfyui/run
Request: { "workflow": {}, "input": {} }
Response: { "job_id": "uuid", "status": "queued" }
Error: 400 "ComfyUI is not enabled" (if mode != local)
```

### Get Workflow Status
```
GET /api/v1/comfyui/status/{job_id}
Response: { "job_id": "uuid", "status": "queued|running|completed|unknown", "progress": 0.5|null, "output": {}|null }
```

---

## 14. Audit (Admin Only)

### List Audit Events
```
GET /api/v1/audit?skip=0&limit=100&event_type=login&user_id=uuid
Response: { "events": [{ "id": "uuid", "timestamp": "ISO8601", "user_id": "uuid|null", "event_type": "string", "details": {}, "request_id": "uuid|null" }], "total": N }
```

### Audit Event Types
| Event Type | Description |
|------------|-------------|
| `login` | User login |
| `logout` | User logout |
| `session_refresh` | Session TTL refresh |
| `session_revoke` | Session revoked |
| `session_compaction` | Old sessions cleaned up |
| `tool_execution` | Tool ran successfully |
| `tool_command` | Tool command attempted (includes blocked) |
| `chat_message` | Chat message sent |
| `doc_ingest` | Document ingested |
| `doc_delete` | Document deleted |
| `acl_change` | Access control changed |
| `model_config_change` | Model config updated |
| `attachment_upload` | File uploaded |

---

## 15. Health Check

```
GET /api/v1/health
Response: { "status": "healthy", "version": "0.1.0a1" }
```

---

## 16. Non-Goals (Out of Scope for v1)

The following are intentionally not implemented and not in scope for v1 frontend:

- **exec_python tool**: Always returns 501 (security)
- **exec_shell tool**: Always returns 501 (security)
- **Attachment ingestion/processing**: Always returns 501 (OCR, transcription, thumbnails not implemented)
- **Profile settings**: Always returns 501 (per-user preferences deferred to Phase B3)
- **TTS (Text-to-Speech)**: Model config exists but no playback UI
- **STT (Speech-to-Text)**: Not implemented
- **Public user profiles**: Not exposed
- **Real-time collaboration**: Not implemented
- **Webhooks**: Not implemented
- **API rate limiting**: Not implemented
- **Multi-factor authentication**: Not implemented

---

## Definition of "Contract Complete"

This contract is complete when:
- ✅ No backend code needs to be read to build UI
- ✅ Every endpoint is documented or explicitly marked as absent
- ✅ Every 501 is intentional and named
- ✅ Capability flags cover all optional features
- ✅ A frontend dev could start tomorrow
