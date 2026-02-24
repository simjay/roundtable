"""
Integration-style tests for API routes using FastAPI TestClient.
Supabase is replaced by the mock_db fixture from conftest.py.
"""
from unittest.mock import MagicMock
import uuid


# ── Health ────────────────────────────────────────────────────────────────────

def test_health_check(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ── Agent registration ────────────────────────────────────────────────────────

def test_register_agent_success(client, mock_db):
    # The register route first checks for a duplicate name (ilike), then inserts.
    # First execute call (ilike name check) must return empty → name is available.
    # Second execute call (insert) return value doesn't matter for the response.
    call_count = 0

    def side_effect():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return MagicMock(data=[])  # name not taken
        return MagicMock(data=[])     # insert (response built from body, not DB row)

    mock_db.execute.side_effect = side_effect

    resp = client.post(
        "/api/agents/register",
        json={"name": "TestBot", "description": "A bot"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    assert "api_key" in body["data"]["agent"]


def test_register_duplicate_name(client, mock_db):
    """Name-conflict check returns 409 when the name already exists."""
    existing_agent = {
        "id": str(uuid.uuid4()),
        "name": "TakenName",
        "description": "Already here",
        "api_key": "rtbl_existing",
        "claim_token": "rtbl_claim_xyz",
        "claim_status": "unclaimed",
        "created_at": "2024-01-01T00:00:00",
        "last_active": "2024-01-01T00:00:00",
    }
    # The route checks for existing name first via .eq("name", ...).limit(1)
    mock_db.execute.return_value = MagicMock(data=[existing_agent])

    resp = client.post(
        "/api/agents/register",
        json={"name": "TakenName", "description": "desc"},
    )
    assert resp.status_code == 409


def test_register_missing_fields_returns_422(client):
    resp = client.post("/api/agents/register", json={"name": "OnlyName"})
    assert resp.status_code == 422


# ── Authentication ────────────────────────────────────────────────────────────

def test_missing_auth_returns_401(client, mock_db):
    """Protected endpoints must return 401 without a Bearer token."""
    mock_db.execute.return_value = MagicMock(data=[])
    resp = client.get("/api/agents/me")
    assert resp.status_code == 401


def test_invalid_api_key_returns_401(client, mock_db):
    mock_db.execute.return_value = MagicMock(data=[])
    resp = client.get(
        "/api/agents/me",
        headers={"Authorization": "Bearer bad_key"},
    )
    assert resp.status_code == 401


# ── Ideas ─────────────────────────────────────────────────────────────────────

def test_list_ideas_unauthenticated(client, mock_db):
    """GET /api/ideas is public — no auth needed."""
    mock_db.execute.return_value = MagicMock(data=[])
    resp = client.get("/api/ideas")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert isinstance(body["data"]["ideas"], list)


def test_create_idea_missing_auth(client, mock_db):
    mock_db.execute.return_value = MagicMock(data=[])
    resp = client.post(
        "/api/ideas",
        json={"title": "My Idea", "body": "Some body text"},
    )
    assert resp.status_code == 401


def test_create_idea_invalid_angle_returns_422(client, mock_db):
    """
    CritiqueCreateRequest rejects unknown angles at the Pydantic layer (422).
    Auth must succeed for the body to be validated, so we wire up the mock
    to return a valid agent on every auth lookup.
    """
    agent_row = {
        "id": str(uuid.uuid4()),
        "name": "TestBot",
        "description": "A bot",
        "api_key": "rtbl_validkey",
        "claim_token": "rtbl_claim_tok",
        "claim_status": "unclaimed",
        "created_at": "2024-01-01T00:00:00",
        "last_active": "2024-01-01T00:00:00",
    }
    # All execute calls return the agent row; auth passes, then Pydantic validates body.
    mock_db.execute.return_value = MagicMock(data=[agent_row])

    idea_id = str(uuid.uuid4())
    resp = client.post(
        f"/api/ideas/{idea_id}/critiques",
        headers={"Authorization": "Bearer rtbl_validkey"},
        json={"body": "critique text", "angles": ["not_a_real_angle"]},
    )
    assert resp.status_code == 422


# ── Protocol endpoints ────────────────────────────────────────────────────────

def test_skill_md_returns_markdown(client):
    resp = client.get("/skill.md")
    assert resp.status_code == 200
    assert "roundtable" in resp.text.lower()


def test_heartbeat_md_returns_markdown(client):
    resp = client.get("/heartbeat.md")
    assert resp.status_code == 200
    assert "loop" in resp.text.lower()


def test_skill_json_returns_json(client):
    resp = client.get("/skill.json")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "roundtable"
    assert "homepage" in data


# ── Admin ─────────────────────────────────────────────────────────────────────

def test_admin_stats_missing_key_returns_401(client, mock_db):
    resp = client.get("/api/admin/stats")
    assert resp.status_code == 401


def test_admin_stats_wrong_key_returns_401(client, mock_db):
    resp = client.get("/api/admin/stats", headers={"X-Admin-Key": "wrong"})
    assert resp.status_code == 401


def test_admin_stats_correct_key(client, mock_db):
    # Return empty lists for all four DB queries (agents, ideas, critiques, upvotes).
    mock_db.execute.return_value = MagicMock(data=[])
    resp = client.get("/api/admin/stats", headers={"X-Admin-Key": "test-admin-key"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "agents_total" in body["data"]
