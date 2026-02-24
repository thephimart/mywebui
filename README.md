![mywebui logo](mywebui.png)

# mywebui

**Local-first Web UI for AI and automation workloads — pure Python.**

`mywebui` is a **local AI workbench** designed to run entirely on your machine, with a strong security model, explicit data ownership, and powerful but observable agents.

No cloud dependencies.  
No telemetry.  
No hidden execution.

---

## Status

🚧 **Alpha**

APIs, architecture, and data models are evolving.

---

## What this is

- A **local-first** AI workbench
- **Multi-user** with explicit authentication and roles
- **Secure-by-design**, running inside a hardened WSL boundary
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

- Web UI (local)
- Python backend (FastAPI)
- Agent runtime with tool orchestration
- SQLite-based storage (docs, vectors, history, audit)
- Local model endpoints (configurable)

All components communicate via **explicit JSON APIs**.

---

## Documentation

The complete, authoritative system design lives in:

- `implementation_plan.md`

This document defines:
- security model
- data ownership rules
- storage layout
- RAG and ACL invariants
- tool execution constraints

The README intentionally stays minimal.

---

## License

MIT © Phimart Consulting
