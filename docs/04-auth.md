# Authentication, Users & Sessions

## Libraries

- **Password hashing**: bcrypt

## Roles

| Role  | Capabilities                                  |
| ----- | --------------------------------------------- |
| Admin | System config, models, tools, users, ACL docs |
| User  | Chat, sessions, attachments, personal docs    |

## Users Table

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `username` | string | Unique, indexed |
| `password_hash` | string | bcrypt hash |
| `role` | enum | `admin` or `user` |
| `is_active` | boolean | Account enabled |
| `created_at` | timestamp | Creation time |

## Authentication

- Local only
- Passwords: salted + hashed
- No OAuth / SSO

## Sessions (Per-user)

Sessions are stored in each user's `history.db`:

**sessions**

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | UUID | Primary key |
| `session_token` | string | UUID, opaque, indexed |
| `user_id` | UUID | Foreign key to users |
| `issued_at` | timestamp | Creation time |
| `expires_at` | timestamp | Expiration time |
| `revoked` | boolean | Revocation flag |
| `last_activity` | timestamp | Last request time |

### Features

- Token expiration
- Rolling refresh on activity
- Absolute max lifetime
- Admin-initiated revocation
- Forced logout
- Session enumeration (admin)
- HTTP-only cookie transport (NOT localStorage)
- WebSocket authentication via same cookie

## Session Refresh

| Property | Value |
|----------|-------|
| Rolling TTL | 24 hours (refreshed on activity) |
| Absolute max | 7 days |
| Refresh mechanism | Update `expires_at` on each request |

## Password Security

- Algorithm: **bcrypt** (salted + hashed)
- Never store plaintext
