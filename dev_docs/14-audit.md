# Audit & Observability

Append-only audit DB:

```
~/.mywebui/audit/events.db
```

## Libraries

- **ORM**: SQLAlchemy 2.0 (async)

## Events Table

| Field | Type | Description |
|-------|------|-------------|
| `event_id` | UUID | Primary key |
| `timestamp` | timestamp | Event time |
| `user_id` | UUID | Actor (nullable for system) |
| `event_type` | enum | See below |
| `details` | JSON | Event-specific data |
| `request_id` | string | For correlation |

## Event Types

| Type | Description |
|------|-------------|
| `tool_execution` | Tool was invoked |
| `tool_command` | Shell command executed |
| `doc_ingest` | Document uploaded/processed |
| `doc_delete` | Document deleted |
| `acl_change` | Permissions modified |
| `model_config_change` | Model settings updated |
| `session_compaction` | History compacted |
| `user_login` | User logged in |
| `user_logout` | User logged out |
| `session_revoke` | Admin revoked session |
| `attachment_upload` | File uploaded |

**Never used for inference.**

## Query API

- Admin-only access
- Filterable by user_id, event_type, date range
- Paginated results
