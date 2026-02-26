# Tool System

## Tool Invocation Rules

**Old rule (too restrictive)**: "One tool call per turn"

This prevents useful patterns:
- search → read → refine loops
- chunk expansion after partial recall
- ComfyUI workflows (prep → generate → post-process)

**New rule**: Bounded, explicit tool iteration per user turn

### Policy

Tool calls may be recursive, but:

| Rule | Value |
|------|-------|
| **Max iterations per turn** | 3 (configurable) |
| **Stop on error** | Yes |
| **Stop on repeat** | Yes (no identical inputs) |
| **State must advance** | Each call must produce new information |

### Requirements

1. **Iteration limits**
   - Maximum N iterations per user turn (default: 3)
   - Hard stop on error or no new information

2. **No repeat calls**
   - No repeated calls with identical inputs
   - No retry loops unless explicitly marked

3. **Visibility**
   - Tool calls logged
   - Partial results inspectable
   - Agent cannot "think silently" between calls

4. **No autonomous continuation**
   - Recursion ends at user turn boundary
   - Agent cannot schedule future tool calls without user input

### Configuration

```yaml
tools:
  max_iterations_per_turn: 3
  stop_on_repeat: true
  require_state_change: true
```

**Principle**: Agents may reason recursively, but they must fail fast and visibly.

---

## Available Tools

### search/filesystem.py
- **Default, always enabled**
- **Library**: Python stdlib (`pathlib`, `os`)
- **Purpose**: Read files from allowed directories
- **Capabilities**: List, read, glob search
- **Constraints**: Restricted to `allowed_paths` in config

### search/web.py
- **Optional, explicitly user-triggered**
- **Library**: httpx
- **Purpose**: Web search / crawling
- **Constraints**: User must explicitly request; not automatic

### exec/python.py
- **Execute Python code**
- **Library**: Python stdlib (`exec`, sandboxed)
- **Constraints**: 
  - CPU/RAM limits
  - No file system access
  - No network access
  - No subprocess

### exec/shell.py
- **Execute shell commands**
- **Library**: `subprocess` (restricted)
- **Constraints**:
  - `/bin/sh` only
  - Allowed commands only
  - CPU/RAM/wall-clock limits

### comfyui/run.py
- **Run ComfyUI workflows**
- **Library**: httpx (ComfyUI API)
- **Constraints**: Admin-enabled only

## Tool API

```
POST /api/tool/run
{
  "tool_name": "...",
  "arguments": {...}
}
```

Response:

```
{
  "success": true,
  "output": "...",
  "logs": {...}
}
```

---

# Execution Environment — Hardened Playground

- Entire system runs inside hardened WSL
- Full networking (explicit)
- No host access
- No nested sandbox
- No artificial syscall blocking

## Execution Phases

**Phase 1**

- Python execution
- Real libraries
- Used for analysis, scraping, transforms

**Phase 2**

- Shell execution
- Build tools, media tools, CLI utilities

### Limits

- CPU
- RAM
- Wall-clock time
- Optional disk quotas

All execution:

- Visible
- Logged
- Attributable

### Shell Execution Constraints

| Constraint | Rule |
|------------|------|
| Shell | `/bin/sh` only (not user shell) |
| Interactive | Not allowed |
| Environment | Clean, no inherited env |
| Working dir | Restricted to allowed paths |
| Strategy | Allowlist preferred over denylist |

### Execution Enforcement

- Wall-clock: `asyncio.timeout()`
- CPU/RAM: `resource` (Unix-only)
- Failure = controlled abort, no partial results
