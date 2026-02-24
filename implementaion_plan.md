# `mywebui`

## ⭐ Local AI Workbench

**COMPLETE IMPLEMENTATION PLAN**

---

## 🧠 1. System Overview & Intent

### Goal

Build a **local-first, multi-user, secure, auditable AI workbench** running entirely inside a **hardened WSL environment**, providing:

* Multi-user authentication (Admin + User)
* Powerful agent execution in a trusted but isolated environment
* Tool-augmented reasoning (search, crawl, execution, ComfyUI)
* ACL-enforced Retrieval-Augmented Generation (RAG)
* Multimodal ingestion & retrieval (text + images; audio/video supported)
* Per-user history, sessions, and long-term memory with compaction
* Clean, modern WebUI with streaming, attachments, and inspection
* Full configuration via WebUI (no manual config files)
* Auditability and observability by default

### Explicit Non-Goals

* No cloud dependencies
* No remote identity providers
* No inner “zero-trust” sandboxes
* No silent tool execution
* No hidden cross-user data sharing

---

## 🧱 2. Trust & Security Model (Authoritative)

### Trust Boundary

```
Windows Host
  └── Hardened WSL Instance  ← SECURITY BOUNDARY
        └── mywebui (ALL services, data, execution)
```

**Assumptions (enforced by base image):**

* No Windows filesystem interop
* No process interop
* No inherited credentials
* Explicitly configured networking
* All persistent data stored inside WSL

Inside this boundary, the agent is **deliberately powerful** with user level access.
However we must prevent system destruction and dat deletion.

Security is:

* coarse-grained
* explicit
* auditable
* non-illusory

---

## 🔐 3. Data Protection Model (Non-Negotiable)

### Core Guarantees

1. **Explicit ownership**

   * Every document, chunk, embedding, attachment, session, and history record has a clear owner.
2. **ACL-first access**

   * ACL filtering happens *before*:

     * vector retrieval
     * summarization
     * embedding
     * UI listing
3. **No cross-user leakage**

   * History, memory, sessions, attachments are per-user.
4. **No implicit promotion**

   * Session data stays session-scoped unless explicitly promoted.
5. **No hidden execution**

   * All tool calls are visible, logged, and attributable.

---

## 📦 4. High-Level Architecture

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

## 👤 5. Authentication, Users & Sessions

### Roles

| Role  | Capabilities                                  |
| ----- | --------------------------------------------- |
| Admin | System config, models, tools, users, ACL docs |
| User  | Chat, sessions, attachments, personal docs    |

### Authentication

* Local only
* Passwords: salted + hashed
* No OAuth / SSO

### Sessions (Global)

```
/data/auth/sessions.db
```

**sessions**

* `session_token`
* `user_id`
* `issued_at`
* `expires_at`
* `revoked`

Features:

* Token expiration
* Admin-initiated revocation
* Forced logout
* Session enumeration (admin)

---

## 🗂️ 6. Storage Layout

```
/data/
  users/<username>/
    history.db
    sessions/
    attachments/
    profile.yaml

  docs/
    docs.db
    media/

  audit/
    events.db   (append-only)

  auth/
    sessions.db

config/
  system.yaml
```

---

## 📚 7. Knowledge Base & RAG (`docs.db`)

### Documents Table

* `doc_id`
* `owner`
* `visibility` (`public` | `restricted` | `private`)
* `allowed_users` (JSON array)
* `allowed_roles`
* `categories` (JSON array)
* `source`
* `hash`
* `created_at`

### ACL Rule (Hard Rule)

A document is visible iff:

```
visibility == public
OR owner == user
OR user ∈ allowed_users
OR user.role ∈ allowed_roles
```

Invisible documents:

* Do not appear in UI
* Do not participate in RAG
* Are never embedded
* Are never summarized

---

## 🧩 8. Chunks & Multimodal Embeddings

### Chunks Table

* `chunk_id`
* `doc_id`
* `modality` (`text` | `image` | `audio` | `video`)
* `text` (nullable)
* `media_ref` (nullable)

### Embeddings Table (sqlite-vec)

* `embedding_id`
* `chunk_id`
* `model_name`
* `modality` (`text` | `image`)
* `vector`

Supports:

* Text embeddings
* Image embeddings
* Multiple embeddings per chunk
* Model upgrades without re-ingestion

---

## 📊 9. Vector Engine (Locked)

* SQLite + sqlite-vec
* Metadata + vectors co-located
* SQL-level ACL filtering
* Category filtering
* Required indexes
* Chunk size: **400–800 tokens**

No external vector DBs.

---

## 💾 10. History, Sessions & Memory (`history.db`)

Per-user database:

### Tables

**messages**

* `msg_id`
* `session_id`
* `role`
* `content`
* `timestamp`
* `raw_json` (tool logs, metadata)

**summaries**

* `summary_id`
* `session_id`
* `summary_text`
* `embedding`

**sessions**

* `session_id`
* `metadata`
* `created_at`

### Compaction Workflow

Triggers:

* Manual
* Token limit
* Size threshold

Process:

1. Extract messages
2. Summarize via summarizer model
3. Store summary
4. Embed summary
5. Archive raw messages

Invariant:

* Only summaries participate in long-term memory
* Raw history is never silently reused

---

## 🧠 11. Model Roles (Independently Configurable)

| Role                  | Purpose                        |
| --------------------- | ------------------------------ |
| Main Agent Model      | Chat, reasoning, tool planning |
| Summarizer Model      | Session & doc summaries        |
| Text Embedding Model  | Text → vectors                 |
| Image Embedding Model | Image → vectors                |

Each role configurable via WebUI:

* Endpoint URL
* Model name
* Parameters
* Test connection button

---

## 🔌 12. Tool System

### Tool Invocation Rules (Hard)

* **At most one tool call per assistant turn**
* No recursive tool calls
* Tool output cannot trigger tools
* All tool calls visible to user
* All tool calls logged

### Tool API

```
POST /api/tool/run
{
  "tool_name": "...",
  "arguments": {...}
}
```

Response:

```
{
  "success": true,
  "output": "...",
  "logs": {...}
}
```

---

## 🧪 13. Execution Environment — Hardened Playground

* Entire system runs inside hardened WSL
* Full networking (explicit)
* No host access
* No nested sandbox
* No artificial syscall blocking

### Execution Phases

**Phase 1**

* Python execution
* Real libraries
* Used for analysis, scraping, transforms

**Phase 2**

* Shell execution
* Build tools, media tools, CLI utilities

Limits:

* CPU
* RAM
* Wall-clock time
* Optional disk quotas

All execution:

* Visible
* Logged
* Attributable

---

## 🖼️ 14. Attachments & Ingestion

### Supported

* Images → preview + image embedding + optional OCR
* Audio → STT
* Video → audio extraction + thumbnails
* Documents → chunked text

### Promotion Flow

1. Title
2. Categories
3. Visibility & ACLs
4. Confirmation
5. Ingest → chunk → embed

---

## 🧠 15. Multimodal Retrieval

* Text query → text embeddings
* Image query → image embeddings
* Mixed queries supported
* Score merging
* Source attribution shown in UI

---

## 🎨 16. ComfyUI Integration

* Workflows as JSON tools
* Admin-enabled workflows only
* Input schema validation
* Job polling
* Outputs returned as URLs or base64
* Resolution / steps / seeds limited by admin

---

## 🖥️ 17. WebUI (Fully Specified)

### Layout

```
┌ Sidebar (Sessions / Docs / Settings) ─┐
|                                      |
|              Chat Area               |
|                                      |
└── Input Bar (attach, STT, send) ─────┘
```

### Features

* Light / dark mode
* Streaming responses
* Drag-drop attachments
* Session list (search, pin, export, compact)
* Docs panel (categories, ACL indicators)
* Inspector panel:

  * active model
  * tools enabled
  * docs selected
  * token usage

---

## 👁️ 18. Audit & Observability

Append-only audit DB:

```
/data/audit/events.db
```

Records:

* Tool executions
* Execution commands
* Doc ingestion
* ACL changes
* Model config changes
* Session compaction

Never used for inference.

---

## ⚙️ 19. First-Run Wizard

1. Create admin account
2. Configure model roles
3. Enable tools
4. Confirm execution environment
5. Save config
6. Start system

No manual config editing required.

---

## 📡 20. Backend APIs (Complete)

### Auth

```
POST /api/auth/login
POST /api/auth/logout
POST /api/auth/revoke-session
```

### Sessions

```
GET  /api/sessions
POST /api/sessions
DELETE /api/sessions/{id}
```

### Chat

```
POST /api/chat/send
GET  /api/chat/stream
```

### Tools

```
POST /api/tool/run
```

### Attachments

```
POST /api/attachments
```

### Docs

```
POST /api/docs/ingest
GET  /api/docs
PATCH /api/docs/{id}
```

### ComfyUI

```
POST /api/comfyui/run
```

---

## ✅ 21. Final Positioning (for AI Coding Agents)

This document is **authoritative**.

Assumptions:

* Strong outer isolation
* Explicit data ownership
* Powerful but observable agents
* No security theater
* No hidden state
