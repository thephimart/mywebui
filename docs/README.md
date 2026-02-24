# mywebui Implementation Docs

> **⚠️ FROZEN**: This documentation is read-only. Changes require an explicit issue with rationale and a version bump.

This directory contains the broken-down implementation plan. Start with the overview, then follow the numbered sequence.

## Contents

| # | File | Description |
|---|------|-------------|
| 01 | [01-overview.md](01-overview.md) | System Overview & Intent |
| 02 | [02-security.md](02-security.md) | Trust & Security Model, Data Protection |
| 03 | [03-architecture.md](03-architecture.md) | High-Level Architecture |
| 04 | [04-auth.md](04-auth.md) | Authentication, Users & Sessions |
| 05 | [05-storage.md](05-storage.md) | Storage Layout |
| 06 | [06-rag.md](06-rag.md) | Knowledge Base, RAG, Chunks, Vector Engine |
| 07 | [07-memory.md](07-memory.md) | History, Sessions & Memory |
| 08 | [08-models.md](08-models.md) | Model Roles |
| 09 | [09-tools.md](09-tools.md) | Tool System, Execution Environment |
| 10 | [10-attachments.md](10-attachments.md) | Attachments & Ingestion |
| 11 | [11-retrieval.md](11-retrieval.md) | Multimodal Retrieval |
| 12 | [12-comfyui.md](12-comfyui.md) | ComfyUI Integration |
| 13 | [13-webui.md](13-webui.md) | WebUI Specification |
| 14 | [14-audit.md](14-audit.md) | Audit & Observability |
| 15 | [15-wizard.md](15-wizard.md) | First-Run Wizard |
| 16 | [16-apis.md](16-apis.md) | Backend APIs |

## Key Principles

- **Trust Boundary**: System runs inside hardened WSL - no host access
- **ACL-first**: Filter data by ACL *before* retrieval/embedding
- **One tool call per turn**: No recursive tool execution
- **Explicit ownership**: Every record has a clear owner
- **Audit logging**: All tool executions must be logged
- **No implicit promotion**: Session data stays session-scoped unless explicitly promoted
