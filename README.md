![mywebui logo](mywebui.png)

# mywebui

**Local-first Web UI for AI and automation workloads — pure Python.**

`mywebui` is a **local AI workbench** designed to run entirely on your machine, with a strong security model, explicit data ownership, and powerful but observable agents.

No cloud dependencies.  
No telemetry.  
No hidden execution.

---

## Status

🚧 **Alpha** — Backend complete, frontend pending.

**Current phase**: Backend spine frozen.
- Backend is **structurally complete** (not feature-complete)
- APIs stable, data models stable
- Alembic is the authoritative schema
- FRONTEND_CONTRACT.md defines the complete frontend boundary

---

## Philosophy

**Short answer**: Freeze scope, finish the backend spine, then expose a clean contract for the frontend.

**Long answer**:
- Declare backend "structurally complete" (not feature-complete)
- Data models stable, migration strategy exists, API shapes fixed
- Side-effects (audit, auth, sessions) guaranteed
- Alembic is the authoritative schema — no ad-hoc CREATE TABLE after this
- Any new persistent data requires migration + contract update in the same PR

---

## What this is

- A **local-first** AI workbench
- **Multi-user** with explicit authentication and roles
- **Secure-by-design**, running inside a local trusted boundary (e.g. WSL, bare metal, VM)
- **Auditable and observable** by default
- **Pure Python** backend

Designed for developers who want **real capability** without security theater.

---

## Core principles

- **Explicit trust boundaries**
- **ACL-first data access**
- **No cross-user data leakage**
- **No silent tool execution**
- **No implicit promotion of data**
- **Everything attributable and logged**

If something happens, you can see *who*, *when*, and *why*.

---

## Non-goals

- Cloud services
- Remote identity providers
- Hosted inference
- Hidden background automation
- Zero-trust theater inside a trusted boundary

---

## Architecture (high level)

- Python backend (FastAPI) — **complete**
- Agent runtime with tool orchestration — **complete**
- SQLite-based storage (docs, vectors, history, audit) — **complete**
- Local model endpoints (configurable) — **complete**
- Web UI (local) — **pending (contract finalized)**

All components communicate via **explicit JSON APIs**.

---

## Implemented Features

### RAG & Retrieval
- Token-aware chunking (512 tokens, 96 overlap)
- MMR re-ranking with configurable λ
- Multimodal retrieval (text, image, hybrid)
- PDF text and image extraction

### Authentication & Security
- Session-based auth with HTTP-only cookies
- Per-user SQLite databases
- Audit logging for all tool executions
- ACL-first data filtering

### Tools
- `filesystem` — Read files from allowed paths
- `web_search` — DuckDuckGo search
- `web_fetch` — URL fetching with BeautifulSoup
- `web_crawl` — crawl4ai web crawling
- `web_interact` — Playwright JS interaction (admin-only)

### Model Providers
- OpenAI-compatible (Ollama, LM Studio, vLLM, OpenRouter)
- Llama-server with multimodal support

---

## What's Pending

### Backend Milestones (Completed)
1. **Alembic migrations** — Authoritative schema
2. **Stubbed unsafe APIs** — Explicit 501 + audit
3. **Wizard flow** — First-run state machine
4. **Audit coverage** — 13 event types
5. **FRONTEND_CONTRACT.md** — Exhaustive frontend contract

### Next Milestone
- Implement frontend against the frozen contract

### Future Features
- Ollama provider (optional)
- Attachment processing (OCR, STT, TTS, thumbnails)
- Per-user profile settings
- Session compaction
- ComfyUI workflow execution

---

## Documentation

The complete, authoritative system design lives in:

- `dev_docs/` (see `dev_docs/README.md` for the index)

This directory contains:
- security model
- data ownership rules
- storage layout
- RAG and ACL invariants
- tool execution constraints
- API specifications
- Task graph with execution order

The README intentionally stays minimal.

---

## License

MIT © Phimart Consulting
