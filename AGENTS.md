# AGENTS.md - mywebui Development Guide

## Project Overview

- **Language**: Python 3.12+ | **Framework**: FastAPI | **Database**: SQLite (user-specific)
- **Status**: Alpha - APIs evolving
- **Trust Boundary**: Runs inside WSL - no host access

---

## Build, Lint, and Test Commands

### Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Running the Application
```bash
source .venv/bin/activate
uvicorn mywebui.main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 600
```
**Note**: `--timeout-keep-alive 600` is required for long-running LLM requests.

### Linting & Type Checking
```bash
ruff check .
ruff check --fix .
mypy .
```

### Testing
```bash
pytest                                    # all tests
pytest tests/test_auth.py                 # single file
pytest tests/test_auth.py::test_login     # single function
pytest -k "test_login"                   # pattern match
pytest --cov=mywebui --cov-report=html    # with coverage
```

---

## Code Style Guidelines

### General Principles
- Follow **PEP 8** with **Ruff** (line length: 130)
- **Type hints required everywhere** - this is a strict requirement
- Keep functions small (~50 lines max)
- Write docstrings for all public modules, classes, and functions

### Imports (sorted by ruff)
```python
# stdlib → third-party → local
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from mywebui.db import connection
from mywebui.schemas.api import LoginRequest
```

### Naming Conventions
| Element | Convention | Example |
|---------|------------|---------|
| Modules | snake_case | `auth_service.py` |
| Classes | PascalCase | `UserService` |
| Functions | snake_case | `get_current_user` |
| Constants | UPPER_SNAKE_CASE | `MAX_TOKEN_LIMIT` |
| Variables | snake_case | `session_token` |
| Private | _leading_underscore | `_internal_cache` |

### Type Hints
```python
def process_message(message: str, user_id: int) -> dict[str, Any]: ...
def get_optional_value() -> str | None: ...

# Pydantic for DTOs
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
```

### Dataclasses for Internal Data Structures
```python
from dataclasses import dataclass
from typing import Literal, Any

@dataclass
class MessageContentPart:
    type: Literal["text", "image_url"]
    text: str | None = None
    image_url: dict[str, Any] | None = None
```

### Error Handling
```python
# Custom exceptions for business logic
class MyWebUIException(Exception):
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)

# HTTP exceptions for API errors
from fastapi import HTTPException, status
raise HTTPException(status_code=404, detail="Item not found")
```

---

## Security Requirements

- **Never expose secrets** in logs or responses
- **Hash passwords** with bcrypt
- **Validate all inputs** with Pydantic models
- **ACL-first**: Filter data by ownership before retrieval/embedding
- **Audit logging**: Log all tool executions
- **No cross-user data leakage**

---

## API Design Pattern
```python
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(request: LoginRequest) -> LoginResponse:
    ...
```

---

## Database & ORM

- Use **SQLAlchemy 2.0** with async support
- Always define models with explicit types
- Use migrations (Alembic) for schema changes
- **SQLite UUID handling**: Convert UUIDs to strings before DB operations

---

## Testing Guidelines
```python
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from mywebui.main import app
    return TestClient(app)

def test_login_success(client):
    response = client.post("/api/auth/login", json={"username": "test", "password": "password123"})
    assert response.status_code == 200
    assert "access_token" in response.json()
```

- Use **pytest** with **pytest-asyncio**
- Test names: `test_<method>_<expected_behavior>`
- Mock external services (LLM endpoints)

---

## Architecture Constraints

1. **Trust Boundary**: Runs inside WSL - no host access
2. **ACL-first**: Filter data by ACL before retrieval
3. **One tool call per turn**: No recursive tool execution
4. **Explicit ownership**: Every record has a clear owner
5. **Audit logging**: All tool executions must be logged
6. **No implicit promotion**: Session data stays session-scoped unless explicitly promoted

---

## File Organization

```
src/mywebui/
├── __init__.py
├── main.py              # FastAPI entry point
├── config.py            # Config, ProviderType, ModelConfig
├── api/v1/              # Route handlers
│   ├── auth.py          # Login, logout, session
│   ├── chat.py          # Chat endpoint with multimodal
│   ├── users.py         # User management
│   ├── documents.py     # Document CRUD
│   ├── audit.py         # Audit logs
│   └── docs.py          # Document retrieval
├── core/                # Business logic
│   ├── auth.py          # Auth service
│   ├── models.py        # LLM model adapters (LlamaServer*)
│   ├── agents.py        # Agent orchestration
│   ├── rag.py           # Chunking, retrieval, MMR
│   ├── pdf.py           # PDF extraction
│   └── tools.py         # web_search, web_fetch, web_crawl, filesystem
├── db/                  # Database
│   ├── models.py        # SQLAlchemy models
│   ├── connection.py    # DB connection
│   └── user_models.py  # User-specific models
├── middleware.py        # Session middleware
└── schemas/             # Pydantic schemas
```

---

## Key Technical Notes

- **Config URLs**: Don't include `/v1` suffix (provider adds it automatically)
- **Datetime**: Use `datetime.now(timezone.utc)` not `datetime.utcnow()` for cookies
- **LlamaServer**: Uses native `/embedding` endpoint, multimodal with content arrays
- **SSL fallback**: `/usr/lib/ssl/cert.pem` if certifi fails
- **SQLite**: User databases are per-user SQLite files

---

## Database & Alembic Migrations

### Two Separate Alembic Environments

The project uses two independent Alembic environments:

```
alembic_docs/          # Docs database (shared)
├── env.py
├── versions/
│   └── 001_docs_initial.py
└── alembic_docs.ini

alembic_users/        # User history databases (per-user)
├── env.py
├── versions/
│   └── 001_users_initial.py
└── alembic_users.ini
```

### Running Migrations Manually

```bash
# Docs database
alembic -c alembic_docs.ini upgrade head
alembic -c alembic_docs.ini stamp head

# User database
alembic -c alembic_users.ini upgrade head
alembic -c alembic_users.ini stamp head
```

### Programmatic Usage

Database initialization happens automatically at startup via `connection.init_docs_db()` and `connection.init_user_db(username)`. These functions:
1. Check if DB exists
2. If new: create tables with `Base.metadata.create_all()`, then stamp with Alembic
3. If exists: run Alembic upgrades

Never call `Base.metadata.create_all()` on existing databases - it causes schema drift.
