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

**Test Results**: 84 tests passing (34 RAG + 30 PDF + 16 VL + 4 benchmarks)

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

### Phase A1: Alembic Migrations (CRITICAL)

**Goal**: Make Alembic the authoritative schema. No ad-hoc schema changes after this.

**Status**: Migration files exist but not integrated as authoritative source.

**Tasks**:
- [ ] Integrate Alembic as sole authority for schema evolution
- [ ] Baseline current schema into migrations
- [ ] One migration per logical table group (docs, users, audit)
- [ ] Lock DB schema - no CREATE TABLE after this point
- [ ] Add embedding_model_id, dim, modality tracking to schema
- [ ] Enforce compatibility at query time
- [ ] Make re-embedding an explicit migration path

**Why?** Without Alembic:
- Every schema tweak = silent breakage
- Embedding model changes = undefined DB state
- Frontend work becomes guessy and fragile

---

### Phase A2: Stub Missing APIs

**Goal**: Return 501 Not Implemented with audit events for intentionally unsupported features.

**Tasks**:
- [ ] Stub exec_python - return 501, log audit event
- [ ] Stub exec_shell - return 501, log audit event
- [ ] Stub Attachment ingestion API - return 501 for internals, provide upload endpoint contract
- [ ] Document what is intentionally unsupported

**Rationale**: Frontend needs to know what states exist and what is intentionally unsupported.

---

### Phase A3: Wizard Flow

**Goal**: First-run setup for admin account and system configuration.

**Tasks**:
- [ ] Implement `/api/wizard/status` endpoint
- [ ] Implement `/api/wizard/complete` endpoint
- [ ] Add existing data detection (reuse/backup/abort)

---

### Phase A4: Full Audit Event Coverage (At Minimum Stubs)

**Goal**: Complete audit logging for all security-relevant events.

**Tasks**:
- [ ] Stub `tool_command` event (even if shallow)
- [ ] Stub `doc_ingest` / `doc_delete` events
- [ ] Stub `acl_change` event
- [ ] Stub `model_config_change` event
- [ ] Stub `session_compaction` event
- [ ] Stub `attachment_upload` event
- [ ] Stub `session_revoke` event

---

### Phase A5: FRONTEND_CONTRACT.md

**Goal**: Produce exhaustive contract document for frontend developers.

**Status**: New document to create after backend spine is complete.

**Contents**:
- Routes (all endpoints)
- Request/response schemas
- Streaming semantics
- Error codes
- Auth requirements
- Capability flags (what's enabled/disabled)

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
| Pydantic class-based config deprecation | Low | Use ConfigDict instead |
| Asyncio event loop in tests | Low | Use pytest-asyncio properly |
| YAML stubs missing | Low | `types-PyYAML` optional |
| SQLite UUID binding | Low | Convert UUIDs to strings before DB operations |
| SSL certificate issues | Low | Use system certs fallback (/usr/lib/ssl/cert.pem) |
| Alembic not authoritative | Critical | Must fix before frontend work |

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
| 1 | Alembic migrations as authoritative schema | 🔴 CRITICAL |
| 2 | Stub exec_python/exec_shell (501 + audit) | 🔴 CRITICAL |
| 3 | Stub attachment API | 🔴 CRITICAL |
| 4 | Wizard flow endpoints | 🔴 CRITICAL |
| 5 | Audit event stubs | 🔴 CRITICAL |
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
