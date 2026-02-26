# System Overview & Intent

## Goal

Build a **local-first, multi-user, secure, auditable AI workbench** running entirely inside a **hardened WSL environment**, providing:

- Multi-user authentication (Admin + User)
- Powerful agent execution in a trusted but isolated environment
- Tool-augmented reasoning (search, crawl, execution, ComfyUI)
- ACL-enforced Retrieval-Augmented Generation (RAG)
- Multimodal ingestion & retrieval (text + images; audio/video supported)
- Per-user history, sessions, and long-term memory with compaction
- Clean, modern WebUI with streaming, attachments, and inspection
- Full configuration via WebUI (no manual config files)
- Auditability and observability by default

## Explicit Non-Goals

- No cloud dependencies
- No remote identity providers
- No inner "zero-trust" sandboxes
- No silent tool execution
- No hidden cross-user data sharing
