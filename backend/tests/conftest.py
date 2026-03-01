"""
Shared fixtures for all backend tests.

The mock_db fixture injects a MagicMock directly into database._client so
every call to get_db() — regardless of how it was imported — returns the mock.
This avoids the "patch at the wrong level" problem caused by `from database import get_db`.
"""
import os
import sys
from unittest.mock import MagicMock

import pytest

# Ensure the backend source is on sys.path so imports resolve correctly
# when pytest is run from the roundtable/ root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Set required env vars before any app module is imported.
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SECRET_KEY", "test-secret-key")
os.environ.setdefault("APP_URL", "http://localhost:8000")
os.environ.setdefault("ADMIN_KEY", "test-admin-key")


@pytest.fixture
def mock_db():
    """
    Replace database._client with a fully chained MagicMock for the duration
    of the test. Because get_db() reads the module-level _client global, this
    intercepts all DB calls regardless of how get_db was imported.
    """
    import database

    db = MagicMock()
    # Every chained call returns the same mock so tests can override selectively.
    db.table.return_value = db
    db.select.return_value = db
    db.insert.return_value = db
    db.update.return_value = db
    db.delete.return_value = db
    db.eq.return_value = db
    db.neq.return_value = db
    db.in_.return_value = db
    db.ilike.return_value = db
    db.order.return_value = db
    db.limit.return_value = db
    db.range.return_value = db
    db.rpc.return_value = db
    db.execute.return_value = MagicMock(data=[])

    original = database._client
    database._client = db
    yield db
    database._client = original


@pytest.fixture
def client(mock_db):
    """FastAPI TestClient with mocked Supabase."""
    from main import app
    from fastapi.testclient import TestClient
    return TestClient(app)
