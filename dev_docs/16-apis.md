# Backend APIs (Complete)

## API Versioning

- All APIs under `/api/v1/*`
- Current: `/api/v1/*`
- No version in URL implies v1

## Auth

```
POST /api/auth/login
Body: { "username": "...", "password": "..." }
Response: { "user": { "id": "...", "username": "...", "role": "..." } }

POST /api/auth/logout
Response: { "ok": true }

POST /api/auth/revoke-session
Body: { "session_id": "..." }
Response: { "ok": true }
```

## Sessions

```
GET  /api/sessions
Response: { "sessions": [...] }

POST /api/sessions
Body: { "title": "..." }
Response: { "session": { "id": "...", "title": "..." } }

DELETE /api/sessions/{id}
Response: { "ok": true }
```

## Chat

```
POST /api/chat/send
Body: { "message": "...", "session_id": "..." }
Response: { "reply": "..." }

GET  /api/chat/stream
Query: ?session_id=...
Response: Server-sent events stream
```

## WebSocket Chat

Endpoint: `WS /api/chat/ws`

### Message Types (Client → Server)

| Type | Payload |
|------|---------|
| `user_message` | `{ "content": "...", "session_id": "..." }` |
| `cancel` | `{}` |

### Event Types (Server → Client)

| Type | Payload |
|------|---------|
| `assistant_delta` | `{ "content": "..." }` |
| `tool_call` | `{ "tool": "...", "args": {...} }` |
| `tool_result` | `{ "tool": "...", "result": "..." }` |
| `error` | `{ "message": "..." }` |
| `done` | `{}` |

### Envelope Format

```json
{
  "type": "assistant_delta",
  "data": { ... }
}
```

Auth: Same HTTP-only cookie as REST APIs.

## Tools

```
POST /api/tool/run
Body: { "tool_name": "...", "arguments": {...} }
Response: { "success": true, "output": "...", "logs": {...} }
```

## Attachments

```
POST /api/attachments
Multipart: file + optional metadata
Response: { "attachment_id": "...", "status": "processing" }

GET /api/attachments/{id}
Response: { "attachment": {...}, "transcription": "..." }
```

## Docs

```
POST /api/docs/ingest
Body: { "title": "...", "category": "...", "visibility": "...", "attachment_id": "..." }
Response: { "doc_id": "..." }

GET /api/docs
Query: ?category=...&visibility=...
Response: { "docs": [...] }

PATCH /api/docs/{id}
Body: { "title": "...", "categories": [...], "visibility": "...", "allowed_users": [...] }
Response: { "doc": {...} }
```

## ComfyUI

```
POST /api/comfyui/run
Body: { "workflow": {...}, "input": {...} }
Response: { "job_id": "..." }

GET /api/comfyui/status/{job_id}
Response: { "status": "running|completed|failed", "outputs": {...} }
```

## Models

```
GET    /api/models
Response: { "models": { "main": {...}, "embedding": {...}, ... } }

GET    /api/models/{role}
Response: { "model": { "provider": "...", "url": "...", "model": "..." } }

PUT    /api/models/{role}
Body: { "provider": "...", "url": "...", "model": "...", "parameters": {...} }
Response: { "model": {...} }

POST   /api/models/{role}/test
Body: { "prompt": "test prompt" }
Response: { "ok": true, "response": "...", "latency_ms": 123 }
```

## Config

```
GET  /api/config
Response: { "config": {...} }

PUT  /api/config
Body: { "config": {...} }
Response: { "config": {...} }
```

## Users (Admin)

```
GET    /api/users
Response: { "users": [...] }

POST   /api/users
Body: { "username": "...", "password": "...", "role": "user|admin" }
Response: { "user": { "id": "..." } }

DELETE /api/users/{id}
Response: { "ok": true }
```

## Audit

```
GET /api/audit/events
Query: ?user_id=...&event_type=...&limit=100&offset=0
Response: { "events": [...], "total": 123 }
```

## Wizard

```
GET    /api/wizard/status
Response: { "state": "needs_admin|needs_config|complete", "next_step": "..." }

POST   /api/wizard/complete
Body: { "admin_username": "...", "admin_password": "...", "models": {...} }
Response: { "ok": true }
```
