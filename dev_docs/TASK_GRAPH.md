# Implementation Task Graph

---

## Philosophy: Freeze Scope, Finish Backend, Then Frontend

**Short answer**: Freeze scope, finish the backend spine, then expose a clean contract for the frontend.

**Long answer**:
- Declare backend "structurally complete" (not feature-complete)
- Data models stable, migration strategy exists, API shapes fixed
- Side-effects (audit, auth, sessions) guaranteed
- Alembic is the authoritative schema - no ad-hoc CREATE TABLE after this

---

## Completed Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Config & Token-aware Chunking | ✅ Complete |
| 2.1 | MMR Re-ranking | ✅ Complete |
| 2.2 | Retrieval Benchmarking | ✅ Complete |
| 3.1 | PDF Text Extraction | ✅ Complete |
| 3.2 | PDF Image Metadata Extraction | ✅ Complete |
| 3.3 | PDF Image Bytes Extraction | ✅ Complete |
| 3.4 | VL Embedding Adapter | ✅ Complete |
| 3.5 | Mixed Text+Image Retrieval | ✅ Complete |
| 4 | Authentication System | ✅ Complete |
| 5 | Provider Configuration (llama-server) | ✅ Complete |
| 6.1 | Tools Implementation (filesystem, web) | ✅ Complete |
| A1 | Alembic Migrations (authoritative schema) | ✅ Complete |
| A2 | Stub Missing APIs (501 + audit) | ✅ Complete |
| A3 | Wizard Flow (existing data detection) | ✅ Complete |
| A4 | Audit Event Coverage (13 event types) | ✅ Complete |
| A5 | FRONTEND_CONTRACT.md | ✅ Complete |

**Test Results**: 84 tests passing

---

## Implemented Features

### RAG Core
- **Token-aware chunking**: 512 tokens, 96 overlap, tiktoken + word×1.3 fallback
- **MMR re-ranking**: Configurable λ (default 0.5)
- **Retrieval benchmarking**: Latency, recall, cosine vs MMR

### PDF Processing
- **Text extraction**: Per-page text, full text, page markers
- **Image metadata**: Page, bbox, dimensions, format
- **Image bytes**: Raw bytes extraction (PDFImageBytes)

### VL Embedding
- **BaseVLEmbeddingModel**: Abstract base class
- **OpenAICompatibleVLEmbeddingModel**: /v1/embeddings compatible
- **ImageInput**: Dataclass for image bytes + format

### Multimodal Retrieval
- **Modality enum**: TEXT, IMAGE, MIXED
- **RetrievalMode**: TEXT_ONLY, IMAGE_ONLY, HYBRID
- **Query-driven detection**: Auto-detects modality from query
- **Weighted merge**: text_weight (0.7) / image_weight (0.3)
- **Multimodal MMR**: Extended for images and hybrid

### Authentication System
- **Session-based auth**: Cookie-based sessions with secure httponly cookies
- **User database**: SQLite with user/session tables per user
- **Audit logging**: All tool executions logged to audit_events table
- **Middleware**: Session lookup and request state injection

### Provider Configuration
- **ProviderType enum**: openai-compatible, llama-server, ollama
- **ModelConfig**: provider, url, model, api_key fields
- **LlamaServerChatModel**: Handles multimodal messages with content arrays
- **LlamaServerEmbeddingModel**: Native /embedding endpoint
- **LlamaServerVLEmbeddingModel**: Image embeddings with image_data format
- **Config URL handling**: Removed /v1 suffix (provider adds it automatically)

### Tools Implementation
- **filesystem**: Read files from allowed paths (/home/phil, /tmp)
- **web_search**: DuckDuckGo search
- **web_fetch**: URL fetching with BeautifulSoup, SSL fallback to system certs
- **web_crawl**: crawl4ai with CrawlResultContainer handling
- **web_interact**: Playwright-based JS interaction (gated, admin-only)

### Chat API
- **StreamRequest**: Added images field for base64 images
- **AgentOrchestrator**: Added image_inputs parameter for multimodal

---

## Immediate Priority: Backend Spine (Must Finish First)

### Phase A1: Alembic Migrations (CRITICAL) ✅ COMPLETE

**Goal**: Make Alembic the authoritative schema. No ad-hoc schema changes after this.

**Status**: ✅ Complete - Alembic is now the authoritative schema source.

**Completed**:
- [x] Integrate Alembic as sole authority for schema evolution
- [x] Baseline current schema into migrations
- [x] One migration per logical table group (docs, users, audit)
- [x] Lock DB schema - no CREATE TABLE after this point
- [x] Add embedding_model_id, dim, modality tracking to schema

**Deferred (runtime/operational concerns, not schema authority)**:
- [ ] Embedding compatibility enforcement at query time (Phase B)
- [ ] Explicit re-embedding workflow (non-Alembic, Phase B/D)

**Changes**:
- Removed `Base.metadata.create_all()` from wizard.py
- Removed deprecated `create_user_tables_async()` and `create_audit_tables_async()` from connection.py
- Added migration `002_add_embedding_tracking.py` for embedding model tracking fields
- Renamed alembic env.py files to fix mypy duplicate module error (docs_env.py, users_env.py)

**Why?** Without Alembic:
- Every schema tweak = silent breakage
- Embedding model changes = undefined DB state
- Frontend work becomes guessy and fragile

---

### Phase A2: Stub Missing APIs ✅ COMPLETE

**Goal**: Return 501 Not Implemented with audit events for intentionally unsupported features.

**Completed**:
- [x] Stub exec_python - return 501, log audit event (`POST /api/tools/exec_python`)
- [x] Stub exec_shell - return 501, log audit event (`POST /api/tools/exec_shell`)
- [x] Stub Attachment ingestion API - return 501 (`POST /api/attachments/{id}/ingest`)

**Rationale**: Frontend needs to know what states exist and what is intentionally unsupported.

**Intentionally Unsupported**:
| Feature | Endpoint | Reason |
|---------|----------|--------|
| exec_python | POST /api/tools/exec_python | Security risk |
| exec_shell | POST /api/tools/exec_shell | Security risk |
| Attachment ingestion | POST /api/attachments/{id}/ingest | Not yet implemented (OCR, transcription, thumbnails) |

---

### Phase A3: Wizard Flow ✅ COMPLETE

**Goal**: First-run setup for admin account and system configuration.

**Completed**:
- [x] Implement `/api/wizard/status` endpoint
- [x] Implement `/api/wizard/complete` endpoint
- [x] Add existing data detection (reuse/backup/abort)

**Endpoints**:
| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/wizard/status | GET | Returns state: not_started, needs_setup_with_existing_data, completed |
| /api/wizard/admin | POST | Create admin user (legacy) |
| /api/wizard/complete | POST | Complete wizard with action: reuse, backup, abort |

**Existing Data Detection**:
- Detects users, documents, audit DB, user directories
- Action `reuse`: Use existing data as-is
- Action `backup`: Backup to `~/.mywebui.backup.{timestamp}` and start fresh
- Action `abort`: Cancel if existing data detected

---

### Phase A4: Full Audit Event Coverage ✅ COMPLETE

**Goal**: Complete audit logging for all security-relevant events.

**Completed**:
- [x] Stub `tool_command` event (`log_tool_command`)
- [x] Stub `doc_ingest` / `doc_delete` events (`log_doc_ingest`, `log_doc_delete`)
- [x] Stub `acl_change` event (`log_acl_change`)
- [x] Stub `model_config_change` event (`log_model_config_change`)
- [x] Stub `session_compaction` event (`log_session_compaction`)
- [x] Stub `attachment_upload` event (`log_attachment_upload`)
- [x] Stub `session_revoke` event (`log_session_revoke`)

**All Available Audit Events**:
| Event | Function | Description |
|-------|-----------|-------------|
| login | log_login | User login |
| logout | log_logout | User logout |
| session_refresh | log_session_refresh | Session token refresh |
| session_revoke | log_session_revoke | Session revocation |
| session_compaction | log_session_compaction | Session message compaction |
| tool_execution | log_tool_execution | Tool execution |
| tool_command | log_tool_command | Blocked tool command attempt |
| chat_message | log_chat_message | Chat message sent |
| doc_ingest | log_doc_ingest | Document ingested |
| doc_delete | log_doc_delete | Document deleted |
| acl_change | log_acl_change | ACL changes |
| model_config_change | log_model_config_change | Model config changed |
| attachment_upload | log_attachment_upload | Attachment uploaded |

---

### Phase A5: FRONTEND_CONTRACT.md ✅ COMPLETE

**Goal**: Produce exhaustive contract document for frontend developers.

**Status**: ✅ Complete - Document created at `/FRONTEND_CONTRACT.md`

**Contents**:
- Routes (all endpoints)
- Request/response schemas
- Streaming semantics (SSE + WebSocket)
- Error codes (canonical envelope)
- Auth requirements (cookie-based)
- Capability flags (`/config/capabilities` for frontend, `/config/system` for admin)
- Wizard state machine diagram
- Non-goals section

**Polished additions**:
- Stable enum guarantee for capability states
- Session response shape documented
- Wizard state diagram
- Streaming cancellation semantics
- Pagination ordering rules
- Document ingest idempotency note

---

## Future Tasks (After Backend Spine)

### Phase B1: Ollama Provider (Optional)

**Goal**: Complete ollama provider implementation.

**Status**: ProviderType enum exists, adapters not implemented.

**Tasks**:
- [ ] Implement OllamaChatModel for local ollama endpoints
- [ ] Implement OllamaEmbeddingModel for ollama embeddings
- [ ] Test with local ollama installation

---

### Phase B2: Attachment Processing

**Goal**: Full document ingestion pipeline (images, audio, video).

**Tasks**:
- [ ] Implement OCR (rapidocr) for image text extraction
- [ ] Implement STT (faster-whisper) for audio transcription
- [ ] Implement video processing (ffmpeg) with audio extraction
- [ ] Implement TTS (Kokoro) for text-to-speech
- [ ] Implement thumbnail generation (256px)
- [ ] Wire attachments to document ingestion

---

### Phase B3: Per-user Profile Settings

**Goal**: User-specific preferences and settings.

**Tasks**:
- [ ] Implement per-user `profile.yaml` storage
- [ ] Add profile API endpoints (/api/v1/users/{id}/profile)
- [ ] Add theme, default_model, preferences support

---

### Phase B4: Session Compaction

**Goal**: Compress old session messages into summaries.

**Triggers**: Manual, token limit, size threshold

**Tasks**:
- [ ] Implement compaction workflow
- [ ] Add summary generation via summarizer model
- [ ] Archive raw messages after summarization

---

### Phase B5: ComfyUI Workflow Execution

**Goal**: Complete integration with ComfyUI for image generation.

**Tasks**:
- [ ] Implement workflow definition storage
- [ ] Implement job queue and execution
- [ ] Add input validation against schema
- [ ] Enforce limits (steps, resolution, seeds)

---

### Phase C: Frontend UI

**Goal**: Build the web UI for the application.

**Status**: Backend APIs exist, frontend not started. Wait for FRONTEND_CONTRACT.md.

**Tasks**:
- [ ] Create React/Next.js frontend
- [ ] Implement chat interface with streaming
- [ ] Add document upload and management UI
- [ ] Build RAG query interface
- [ ] Add user settings and preferences

---

### Phase D1: Cross-Modal Similarity (Optional Enhancement)

**Goal**: Enable meaningful cross-modality similarity scoring.

**Tasks**:
- [ ] Implement `_cross_modality_similarity()` with learned joint space
- [ ] Add CLIP-style encoder for joint text-image embeddings
- [ ] Consider learned weighting instead of static 0.7/0.3

**Notes**: This is optional. Current implementation returns 0.0 for cross-modality similarity, which is a safe placeholder.

---

### Phase D2: Storage Layer Optimization

**Goal**: Separate text and image vector storage with hybrid ANN indexes.

**Tasks**:
- [ ] Add separate tables/indexes for image embeddings
- [ ] Implement hybrid ANN (Approximate Nearest Neighbor) indexes
- [ ] Add query-time budget allocation (e.g., "search 5 text, 3 images")
- [ ] Optimize for combined text+image queries

---

### Phase D3: UI & Explainability

**Goal**: Surface multimodal results with citations and explanations.

**Tasks**:
- [ ] Add image preview in retrieval results
- [ ] Implement "why this was retrieved" explanations
- [ ] Add confidence scores and relevance indicators
- [ ] Support mixed text+image result display

---

## Known Technical Debt

| Issue | Severity | Notes |
|-------|----------|-------|
| Pydantic class-based config deprecation | ✅ Fixed | Use ConfigDict instead |
| Asyncio event loop in tests | ✅ Fixed | Use pytest-asyncio properly |
| YAML stubs missing | Low | `types-PyYAML` optional |
| SQLite UUID binding | Low | Convert UUIDs to strings before DB operations |
| SSL certificate issues | Low | Use system certs fallback (/usr/lib/ssl/cert.pem) |
| Alembic not authoritative | ✅ Fixed | Now authoritative, migration added |
| Embedding compatibility at query time | Deferred | Runtime policy concern - Phase B |
| Re-embedding workflow | Deferred | Operational workflow - Phase B/D |

---

## Architecture Constraints (LOCKED)

| ✅ Do | ❌ Don't |
|-------|---------|
| Chunk size 512 / overlap 96 | Add joint embeddings prematurely |
| tiktoken with fallback | Skip modality gating |
| Embedding dimension 2048 | Hardcode scoring weights |
| Config-driven settings | Mix storage with retrieval |
| MMR λ=0.5 default | Skip benchmarking |
| Session-based auth with httponly cookies | Expose secrets in logs |
| ACL-first data filtering | Cross-user data leakage |
| Audit all tool executions | Skip audit logging |
| Alembic as schema authority | Ad-hoc CREATE TABLE |
| Freeze scope before frontend | Add new features |
| Migration + contract update in same PR | Schema snuck in through side door |

---

## PR Workflow (Enforced)

**Rule**: Any new persistent data requires a migration + FRONTEND_CONTRACT.md update in the same PR.

**Why**:
- Preuck in through avents "schema sn side door"
- Keeps FRONTEND_CONTRACT.md authoritative
- Forces thinking in terms of interfaces, not tables

**Practical execution**:
- A1 PR: Alembic init, baseline migration, remove runtime schema creation
- A2 PR: exec_python/exec_shell return 501, audit event fired
- A3 PR: Wizard endpoints, no UI, just state transitions
- A4 PR: Enumerate audit events, fire stubs
- A5 PR: FRONTEND_CONTRACT.md as deliverable (not notes)

**After A5**: Frontend becomes obvious.

---

## Execution Order (Recommended)

| Step | Task | Priority |
|------|------|----------|
| 1 | Alembic migrations as authoritative schema | ✅ Complete |
| 2 | Stub exec_python/exec_shell (501 + audit) | ✅ Complete |
| 3 | Stub attachment API | ✅ Complete |
| 4 | Wizard flow endpoints | ✅ Complete |
| 5 | Audit event stubs | ✅ Complete |
| 6 | Write FRONTEND_CONTRACT.md | 🟡 BLOCKS FRONTEND |
| 7 | Ollama provider (optional) | 🟢 Optional |
| 8 | Attachment processing | 🟢 Future |
| 9 | Profile settings | 🟢 Future |
| 10 | Session compaction | 🟢 Future |
| 11 | ComfyUI execution | 🟢 Future |
| 12 | Frontend UI | 🟢 After contract |

---

## Key Insight

> This is not a half-built backend — this is a serious system that's one discipline step away from being "attachable."

The hard part is done:
- Clear dependency graph
- No magical coupling
- No premature UI-driven compromises

Now it's time to formalize, not expand.
