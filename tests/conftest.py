"""Test configuration."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client."""
    from mywebui.main import app
    return TestClient(app)


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    from mywebui.config import Config
    return Config(debug=True)
