# Implementation Task Graph

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
