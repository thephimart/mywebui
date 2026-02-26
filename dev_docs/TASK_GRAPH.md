# Implementation Task Graph

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
| 6 | Tools Implementation | ✅ Complete |

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
- **web_search**: DuckDuckGo search
- **web_fetch**: URL fetching with BeautifulSoup, SSL fallback to system certs
- **web_crawl**: crawl4ai with CrawlResultContainer handling
- **filesystem**: Read files from allowed paths (/home/phil, /tmp)

### Chat API
- **StreamRequest**: Added images field for base64 images
- **AgentOrchestrator**: Added image_inputs parameter for multimodal

---

## Phase 1: Foundation (Can be parallelized after storage)

```
storage (05-storage)
    │
    ├──► migrations (Alembic)
    │
    └──► users_table (04-auth)
              │
              ├──► auth (04-auth)
              │        │
              │        └──► sessions (04-auth)
              │
              └──► audit (14-audit)
```

## Phase 2: API Skeleton (Depends on: auth)

```
auth (04-auth)
    │
    ├──► API routes (16-apis)
    │        │
    │        ├──► /api/v1/auth/*
    │        ├──► /api/v1/sessions/*
    │        ├──► /api/v1/users/* (admin)
    │        ├──► /api/v1/audit/* (admin)
    │        └──► /api/v1/wizard/*
    │
    └──► WebSocket protocol (16-apis)
```

## Phase 3: Core Features (Depends on: API skeleton)

```
API skeleton
    │
    ├──► chat (16-apis)
    │        │
    │        └──► agent orchestrator
    │                 │
    │                 ├──► tools (09-tools)
    │                 │
    │                 └──► models (08-models)
    │
    ├──► docs (16-apis)
    │        │
    │        └──► rag (06-rag)
    │                 │
    │                 └──► retrieval (11-retrieval)
    │
    ├──► attachments (16-apis)
    │        │
    │        └──► ingestion (10-attachments)
    │
    └──► config (16-apis)
```

## Phase 4: Integrations (Depends on: core features)

```
core features
    │
    ├──► comfyui (12-comfyui)
    │
    └──► webui (13-webui)
```

---

## Execution Order (Boring Spine First)

| Step | Task | Dependencies | Can Parallelize With |
|------|------|--------------|---------------------|
| 1 | Storage layout + migrations | - | - |
| 2 | Users table | storage | - |
| 3 | Auth (login/logout) | users | - |
| 4 | Sessions | auth | - |
| 5 | Audit logging | auth | - |
| 6 | API routes skeleton | auth | - |
| 7 | WebSocket plumbing | auth | - |
| 8 | Chat endpoint | API skeleton | tools, docs |
| 9 | Tools system | chat | docs |
| 10 | Models/Agents | tools | chat |
| 11 | Docs + RAG | API skeleton | chat |
| 12 | Retrieval | docs | - |
| 13 | Attachments + ingestion | API skeleton | docs |
| 14 | Config management | API skeleton | - |
| 15 | ComfyUI integration | core features | - |
| 16 | WebUI | core features | - |

---

## Key Dependencies Summary

```
storage → users → auth → sessions → audit → API → chat → tools → models
                                            ↓
                                           docs → retrieval
                                            ↓
                                         attachments
                                            ↓
                                          config
                                            ↓
                                           comfyui
                                             ↓
                                            webui
```

---

## Future Tasks

### Phase 7: Ollama Provider (Optional)

**Goal**: Complete ollama provider implementation.

**Tasks**:
- [ ] Implement OllamaChatModel for local ollama endpoints
- [ ] Implement OllamaEmbeddingModel for ollama embeddings
- [ ] Test with local ollama installation

**Notes**: Currently only llama-server provider is implemented. Ollama can be added for users who prefer that interface.

---

### Phase 8: UI & Frontend (Future)

**Goal**: Build the web UI for the application.

**Tasks**:
- [ ] Create React/Next.js frontend
- [ ] Implement chat interface with streaming
- [ ] Add document upload and management UI
- [ ] Build RAG query interface
- [ ] Add user settings and preferences

---

### Phase 3.6: Cross-Modal Similarity (Optional Enhancement)

**Goal**: Enable meaningful cross-modality similarity scoring.

**Tasks**:
- [ ] Implement `_cross_modality_similarity()` with learned joint space
- [ ] Add CLIP-style encoder for joint text-image embeddings
- [ ] Consider learned weighting instead of static 0.7/0.3

**Notes**: This is optional. Current implementation returns 0.0 for cross-modality similarity, which is a safe placeholder.

---

### Phase 4: Storage Layer Optimization

**Goal**: Separate text and image vector storage with hybrid ANN indexes.

**Tasks**:
- [ ] Add separate tables/indexes for image embeddings
- [ ] Implement hybrid ANN (Approximate Nearest Neighbor) indexes
- [ ] Add query-time budget allocation (e.g., "search 5 text, 3 images")
- [ ] Optimize for combined text+image queries

---

### Phase 5: UI & Explainability

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
