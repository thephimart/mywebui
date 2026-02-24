# AGENTS.md - mywebui Development Guide

## Project Overview

- **Project**: mywebui - Local-first Web UI for AI and automation workloads
- **Language**: Python 3.12+ (pure Python backend)
- **Framework**: FastAPI
- **Database**: SQLite with sqlite-vec for vectors
- **Status**: Alpha - APIs and architecture are evolving

The authoritative system design is in `docs/`. All agent implementations must follow the security model, data ownership rules, and ACL invariants defined there.

---

## Build, Lint, and Test Commands

### Development Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or .venv\Scripts\activate on Windows

# Install dependencies
pip install -e ".[dev]"
```

### Running the Application

```bash
# Run development server
python -m mywebui

# Or via uvicorn
uvicorn mywebui.main:app --reload
```

### Linting & Type Checking

```bash
# Run ruff linter
ruff check .

# Run ruff with auto-fix
ruff check --fix .

# Run mypy type checker
mypy .
```

### Testing

```bash
# Run all tests
pytest

# Run a single test file
pytest tests/test_auth.py

# Run a single test function
pytest tests/test_auth.py::test_login_success

# Run tests matching a pattern
pytest -k "test_login"

# Run with coverage
pytest --cov=mywebui --cov-report=html
```

### Building

```bash
# Build package
python -m build

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

---

## Code Style Guidelines

### General Principles

- Follow **PEP 8** with **Black** formatting (line length: 100)
- Use **type hints** everywhere - this is a strict requirement
- Keep functions small and focused (max ~50 lines)
- Write docstrings for all public modules, classes, and functions

### Imports

```python
# Standard library first, then third-party, then local
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from mywebui.auth import get_current_user
from mywebui.models import User
```

- Use absolute imports (not relative `..`)
- Sort imports with `ruff check --select=I --fix`
- Group: stdlib → third-party → local, with blank lines between groups

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Modules | `snake_case` | `auth_service.py` |
| Classes | `PascalCase` | `UserService` |
| Functions | `snake_case` | `get_current_user` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_TOKEN_LIMIT` |
| Variables | `snake_case` | `session_token` |
| Private members | `_leading_underscore` | `_internal_cache` |

### Type Hints

```python
# Always use explicit types
def process_message(message: str, user_id: int) -> dict[str, Any]:
    ...

# Use Optional for nullable types
def get_optional_value() -> str | None:
    ...

# Use TypeVar for generics
T = TypeVar("T")

# Pydantic models for all data transfer objects
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
```

### Error Handling

```python
# Use custom exception classes
class MyWebUIException(Exception):
    """Base exception for mywebui."""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)

# Handle gracefully with appropriate HTTP exceptions
from fastapi import HTTPException

@app.get("/items/{item_id}")
async def get_item(item_id: int) -> Item:
    item = await db.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
```

### Database & ORM

- Use **SQLAlchemy 2.0** with async support
- Always define models with explicit types
- Use migrations (Alembic) for schema changes
- Never hardcode SQL - use the ORM

### API Design

```python
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(request: LoginRequest) -> LoginResponse:
    ...
```

### Security Requirements (From docs/)

- **Never expose secrets in logs or responses**
- **Always hash passwords** with salt (use bcrypt or argon2)
- **Validate all inputs** with Pydantic models
- **Enforce ACL filtering** before any data access
- **Log all tool executions** for auditability
- **No cross-user data leakage** - each user's data is isolated

### Testing Guidelines

```python
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from mywebui.main import app
    return TestClient(app)

def test_login_success(client):
    response = client.post("/api/auth/login", json={
        "username": "test",
        "password": "password123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
```

- Use **pytest** with async support (**pytest-asyncio**)
- Write descriptive test names: `test_<method>_<expected_behavior>`
- Use fixtures for common setup
- Mock external services (LLM endpoints, file system)
- Aim for meaningful test coverage on critical paths

### Documentation

- Docstrings: **Google style** or **NumPy style**
- Example:
```python
def authenticate_user(username: str, password: str) -> User | None:
    """Authenticate a user by username and password.

    Args:
        username: The user's username.
        password: The user's plaintext password.

    Returns:
        The authenticated User object, or None if authentication fails.

    Raises:
        AuthenticationError: If the credentials are invalid.
    """
```

### Git Conventions

- Commit messages: Imperative mood, 50 chars max for title
- Branches: `feature/description` or `fix/description`
- PRs: Include description of changes and link to issues

---

## Architecture Constraints

Per the docs in `docs/`, agents must respect:

1. **Trust Boundary**: Runs inside hardened WSL - no host access
2. **ACL-first**: Filter data by ACL *before* retrieval/embedding
3. **One tool call per turn**: No recursive tool execution
4. **Explicit ownership**: Every record has a clear owner
5. **Audit logging**: All tool executions must be logged
6. **No implicit promotion**: Session data stays session-scoped unless explicitly promoted

---

## File Organization

```
mywebui/
├── src/mywebui/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── api/                 # API route handlers
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── chat.py
│   │       └── ...
│   ├── core/                # Core business logic
│   │   ├── auth.py
│   │   ├── agents.py
│   │   └── tools.py
│   ├── db/                  # Database models
│   │ & connection   ├── models.py
│   │   └── connection.py
│   └── schemas/             # Pydantic schemas
├── tests/
│   ├── conftest.py
│   └── test_*.py
├── pyproject.toml
└── README.md
```
