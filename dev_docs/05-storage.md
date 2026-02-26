# Storage Layout

## Libraries

- **Migrations**: Alembic
- **Config**: PyYAML

```
~/.mywebui/
  users/<username>/
    history.db          # messages, summaries, sessions (per-user)
    attachments/        # user uploads
    profile.yaml        # user settings

  docs/
    docs.db             # shared documents + embeddings (ACL-controlled)
    media/              # document media

  audit/
    events.db           # append-only

  logs/                 # application logs (rotated daily)
    mywebui.log
    access.log

  config/
    system.yaml        # system-wide config
    workflows/         # ComfyUI workflow definitions
```

**Embedding storage:**
- Document embeddings → `docs.db` (shared, ACL-filtered)
- Memory/summary embeddings → per-user `history.db`

## Config Files

### system.yaml

```yaml
version: "1.0"

server:
  host: "0.0.0.0"
  port: 8000

security:
  session_rolling_ttl_hours: 24
  session_absolute_max_days: 7

models:
  main:
    provider: openai-compatible
    url: "http://localhost:11434"
    model: "llama3"
  summarizer:
    provider: openai-compatible
    url: "http://localhost:11434"
    model: "llama3"
  embedding:
    provider: openai-compatible
    url: "http://localhost:11434"
    model: "nomic-embed-text"

tools:
  filesystem:
    enabled: true
    allowed_paths:
      - "/home/user/data"
  web:
    enabled: false

comfyui:
  mode: local
  url: "http://localhost:8188"
  limits:
    max_steps: 100
    max_resolution: 1024
```

### profile.yaml (per user)

```yaml
username: "user"
display_name: "User"
preferences:
  theme: "dark"
  default_model: "main"
  tts_voice: "af_sarah"
```

## Migrations

- No auto-migrate on startup
- Migrations are explicit user actions
- Schema version checked on boot

## Database Initialization

### System Databases (created on first run)

1. `~/.mywebui/docs/docs.db` - Schema version table + documents/chunks/embeddings
2. `~/.mywebui/audit/events.db` - Schema version table + events

### Per-User Databases (created on first login)

1. `~/.mywebui/users/<username>/history.db` - messages, summaries, sessions

### First Run Flow

1. Create system DBs (docs.db, audit.events.db)
2. Run initial migration (Alembic)
3. Start wizard at `/api/wizard/status`
4. User creates admin account
5. System is operational
