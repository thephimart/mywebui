# History, Sessions & Memory (`history.db`)

Per-user database:

## Tables

**messages**

| Field | Type | Description |
|-------|------|-------------|
| `msg_id` | UUID | Primary key |
| `session_id` | UUID | Foreign key |
| `role` | enum | `user`, `assistant`, `system`, `tool` |
| `content` | text | Message content |
| `timestamp` | timestamp | Creation time |
| `raw_json` | JSON | Tool logs, metadata, function calls |

**summaries**

| Field | Type | Description |
|-------|------|-------------|
| `summary_id` | UUID | Primary key |
| `session_id` | UUID | Foreign key |
| `summary_text` | text | LLM-generated summary |
| `embedding` | vector | Summary embedding (for retrieval) |

**sessions**

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | UUID | Primary key |
| `metadata` | JSON | Session title, model used, etc. |
| `created_at` | timestamp | Creation time |

## Compaction Workflow

### Triggers:

- Manual
- Token limit
- Size threshold

### Process:

1. Extract messages
2. Summarize via summarizer model
3. Store summary
4. Embed summary
5. Archive raw messages

### Invariant:

- Only summaries participate in long-term memory
- Raw history is never silently reused
