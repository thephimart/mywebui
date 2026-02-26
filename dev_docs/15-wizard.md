# First-Run Wizard

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/wizard/status` | GET | Current wizard state |
| `/api/wizard/complete` | POST | Submit wizard data |

## Wizard States

| State | Description |
|-------|-------------|
| `needs_admin` | No admin account exists |
| `needs_models` | Admin exists, models not configured |
| `needs_tools` | Models configured, tools not enabled |
| `complete` | System ready |

## Workflow

### Step 1: Create Admin Account

```
POST /api/wizard/complete
{
  "admin_username": "admin",
  "admin_password": "securepassword123"
}
```

### Step 2: Configure Models

```
{
  "admin_username": "admin",
  "admin_password": "...",
  "models": {
    "main": {
      "provider": "openai-compatible",
      "url": "http://localhost:11434",
      "model": "llama3"
    },
    "embedding": {
      "provider": "openai-compatible", 
      "url": "http://localhost:11434",
      "model": "nomic-embed-text"
    }
  }
}
```

### Step 3: Enable Tools

```
{
  "admin_username": "...",
  "admin_password": "...",
  "tools": {
    "filesystem": {
      "enabled": true,
      "allowed_paths": ["/home/user/data"]
    }
  }
}
```

## Existing Data Detection

On startup, detect existing data and present explicit options:

| Option | Behavior |
|--------|----------|
| **Reuse** | Continue with existing data |
| **Backup + Reset** | Archive existing data, start fresh |
| **Abort** | Stop startup, require manual resolution |

## Rules

- **No silent migrations**
- **No implicit schema upgrades**
- User must choose explicitly

This is a trust decision as much as technical.
