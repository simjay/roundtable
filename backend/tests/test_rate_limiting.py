"""
Tests for rate limiting improvements:
  - The app exposes a limiter on app.state
  - Exceeding the idea creation limit returns 429
  - The 429 response matches the standard error envelope
  - Exceeding the registration limit returns 429
"""
import uuid
from unittest.mock import MagicMock

import pytest


# ── Shared fixtures ────────────────────────────────────────────────────────────

AGENT_ROW = {
    "id": str(uuid.uuid4()),
    "name": "RateLimitBot",
    "description": "Test agent",
    "api_key": "rtbl_ratelimitkey",
    "claim_token": "rtbl_claim_rl",
    "claim_status": "unclaimed",
    "created_at": "2026-01-01T00:00:00",
    "last_active": "2026-01-01T00:00:00",
}

IDEA_ROW = {
    "id": str(uuid.uuid4()),
    "title": "Idea",
    "body": "Body",
    "topic_tag": None,
    "upvote_count": 0,
    "critique_count": 0,
    "agent_id": AGENT_ROW["id"],
    "created_at": "2026-01-02T00:00:00",
    "updated_at": "2026-01-02T00:00:00",
}


@pytest.fixture(autouse=True)
def reset_limiter():
    """Reset slowapi's in-memory storage before/after each test."""
    from main import app
    lim = app.state.limiter
    storage = getattr(lim, "_storage", None)
    if storage and hasattr(storage, "reset"):
        storage.reset()
    yield
    if storage and hasattr(storage, "reset"):
        storage.reset()


# ── Limiter is wired up ───────────────────────────────────────────────────────

def test_app_has_limiter_configured(client):
    """app.state.limiter must exist — confirms slowapi is wired up."""
    from main import app
    assert hasattr(app.state, "limiter")


# ── Idea creation rate limit ──────────────────────────────────────────────────

def test_rate_limit_response_shape(client, mock_db):
    """After exhausting the idea limit (10/hour), the 429 must match the standard envelope."""
    # Each POST /api/ideas needs: auth → last_active → dup check → insert → activity_log
    # We cycle through those 5 calls per request
    call_count = 0

    def execute_se():
        nonlocal call_count
        call_count += 1
        slot = call_count % 5
        if slot == 1:
            return MagicMock(data=[AGENT_ROW])   # auth
        if slot == 2:
            return MagicMock(data=[])             # last_active
        if slot == 3:
            return MagicMock(data=[])             # dup check
        if slot == 4:
            return MagicMock(data=[IDEA_ROW])     # insert
        return MagicMock(data=[])                 # activity_log

    mock_db.execute.side_effect = execute_se

    resp = None
    for i in range(11):
        resp = client.post(
            "/api/ideas",
            headers={"Authorization": "Bearer rtbl_ratelimitkey"},
            json={"title": f"Idea {i}", "body": "body text"},
        )
        if resp.status_code == 429:
            break

    assert resp is not None and resp.status_code == 429
    body = resp.json()
    assert body["success"] is False
    assert "error" in body
    assert "hint" in body
    assert "retry_after_seconds" in body


# ── Critique creation rate limit ──────────────────────────────────────────────

def test_critique_rate_limit_returns_429(client, mock_db):
    """After exhausting the critique limit (30/hour), the next attempt returns 429."""
    idea_id = str(uuid.uuid4())
    idea_row = {"id": idea_id, "title": "Target Idea"}

    # Each POST /api/ideas/{id}/critiques needs:
    # auth → last_active → idea exists → dup check → insert → activity_log
    call_count = 0

    def execute_se():
        nonlocal call_count
        call_count += 1
        slot = call_count % 6
        if slot == 1:
            return MagicMock(data=[AGENT_ROW])
        if slot == 2:
            return MagicMock(data=[])              # last_active
        if slot == 3:
            return MagicMock(data=[idea_row])      # idea exists
        if slot == 4:
            return MagicMock(data=[])              # dup check
        if slot == 5:
            return MagicMock(                      # critique insert
                data=[{"id": str(uuid.uuid4()), "body": "x", "angles": ["market_risk"],
                       "upvote_count": 0, "created_at": "2026-01-01T00:00:00"}]
            )
        return MagicMock(data=[])                  # activity_log

    mock_db.execute.side_effect = execute_se

    resp = None
    for i in range(32):
        resp = client.post(
            f"/api/ideas/{idea_id}/critiques",
            headers={"Authorization": "Bearer rtbl_ratelimitkey"},
            json={"body": f"Critique {i} " + "x" * 50, "angles": ["market_risk"]},
        )
        if resp.status_code == 429:
            break

    assert resp is not None and resp.status_code == 429


# ── Registration IP rate limit ────────────────────────────────────────────────

def test_register_ip_rate_limit_returns_429(client, mock_db):
    """After 5 registrations from the same IP, the 6th must return 429."""
    mock_db.execute.return_value = MagicMock(data=[])  # name checks always empty

    resp = None
    for i in range(6):
        resp = client.post(
            "/api/agents/register",
            json={"name": f"RLBot{i}", "description": "desc"},
        )
        if resp.status_code == 429:
            break

    assert resp is not None and resp.status_code == 429
