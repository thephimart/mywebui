# Trust & Security Model

## Trust Boundary

```
Windows Host
  └── Hardened WSL Instance  ← SECURITY BOUNDARY
        └── mywebui (ALL services, data, execution)
```

**Assumptions (enforced by base image):**

- No Windows filesystem interop
- No process interop
- No inherited credentials
- Explicitly configured networking
- All persistent data stored inside WSL

Inside this boundary, the agent is **deliberately powerful** with user level access.
However we must prevent system destruction and data deletion.

Security is:

- coarse-grained
- explicit
- auditable
- non-illusory

---

## Data Protection Model

### Core Guarantees

1. **Explicit ownership**

   - Every document, chunk, embedding, attachment, session, and history record has a clear owner.

2. **ACL-first access**

   - ACL filtering happens *before*:
     - vector retrieval
     - summarization
     - embedding
     - UI listing

3. **No cross-user leakage**

   - History, memory, sessions, attachments are per-user.

4. **No implicit promotion**

   - Session data stays session-scoped unless explicitly promoted.

5. **No hidden execution**

   - All tool calls are visible, logged, and attributable.
   - Tool iteration is bounded (see 09-tools.md)
   - Agent cannot "think silently" between tool calls

### ACL Implementation

**Pattern**: Query-time modifiers in Python (NOT SQL views/stored procedures)

```python
def apply_acl(query, user):
    if user.is_admin:
        return query
    return query.where(owner_id=user.id)
```

Why:
- Debuggable and testable
- Model-aware
- Visible and reviewable
- Agent-aware

### Security Principles

- Never expose secrets in logs or responses
- Always hash passwords with salt (bcrypt)
- Validate all inputs with Pydantic models
- Enforce ACL filtering before any data access
- Log all tool executions for auditability
