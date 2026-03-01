"""
Tests for reliability improvements:
  - Duplicate idea returns 200 with existing record; insert is NOT called
  - Duplicate critique returns 200 with existing record; insert is NOT called
  - Upvoting an idea twice returns the same count (idempotent)
  - 422 validation errors are reshaped into the standard error envelope
"""
import uuid
from unittest.mock import MagicMock


# ── Shared fixtures ────────────────────────────────────────────────────────────

AGENT_ROW = {
    "id": str(uuid.uuid4()),
    "name": "ReliabilityBot",
    "description": "Test agent",
    "api_key": "rtbl_reliablekey",
    "claim_token": "rtbl_claim_rel",
    "claim_status": "unclaimed",
    "created_at": "2026-01-01T00:00:00",
    "last_active": "2026-01-01T00:00:00",
}

IDEA_ID = str(uuid.uuid4())
CRITIQUE_ID = str(uuid.uuid4())

EXISTING_IDEA = {
    "id": IDEA_ID,
    "title": "My Existing Idea",
    "body": "original body",
    "topic_tag": "research",
    "upvote_count": 3,
    "critique_count": 1,
    "created_at": "2026-02-01T00:00:00",
    "updated_at": "2026-02-01T00:00:00",
}

EXISTING_CRITIQUE = {
    "id": CRITIQUE_ID,
    "body": "This idea has a serious market risk that undermines its viability.",
    "angles": ["market_risk"],
    "upvote_count": 0,
    "created_at": "2026-02-01T00:00:00",
}


# ── Duplicate idea detection ──────────────────────────────────────────────────

def test_create_idea_duplicate_returns_existing(client, mock_db):
    """POST /api/ideas with a title already used by this agent must return 200
    with the existing idea and must NOT call db.insert."""
    call_count = 0

    def execute_se():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return MagicMock(data=[AGENT_ROW])      # auth SELECT
        if call_count == 2:
            return MagicMock(data=[])               # last_active UPDATE
        # 3rd call = duplicate title check → match found
        return MagicMock(data=[EXISTING_IDEA])

    mock_db.execute.side_effect = execute_se

    resp = client.post(
        "/api/ideas",
        headers={"Authorization": "Bearer rtbl_reliablekey"},
        json={"title": "My Existing Idea", "body": "retry body"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["idea"]["id"] == IDEA_ID
    assert "note" in body

    # insert must NOT have been called
    insert_calls = list(mock_db.insert.call_args_list)
    assert len(insert_calls) == 0, "insert was called despite a duplicate being detected"


def test_create_idea_no_duplicate_proceeds_normally(client, mock_db):
    """When no duplicate title exists the idea is inserted and returns 201."""
    new_idea = {**EXISTING_IDEA, "id": str(uuid.uuid4()), "title": "Brand New Idea"}
    call_count = 0

    def execute_se():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return MagicMock(data=[AGENT_ROW])   # auth
        if call_count == 2:
            return MagicMock(data=[])            # last_active
        if call_count == 3:
            return MagicMock(data=[])            # dup check — no match
        if call_count == 4:
            return MagicMock(data=[new_idea])    # insert
        return MagicMock(data=[])                # activity_log

    mock_db.execute.side_effect = execute_se

    resp = client.post(
        "/api/ideas",
        headers={"Authorization": "Bearer rtbl_reliablekey"},
        json={"title": "Brand New Idea", "body": "body text"},
    )

    assert resp.status_code == 201
    assert "note" not in resp.json()


# ── Duplicate critique detection ──────────────────────────────────────────────

def test_create_critique_duplicate_returns_existing(client, mock_db):
    """POST /api/ideas/{id}/critiques with same agent+idea+body prefix must return 200
    with the existing critique and must NOT call db.insert."""
    call_count = 0

    def execute_se():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return MagicMock(data=[AGENT_ROW])                           # auth
        if call_count == 2:
            return MagicMock(data=[])                                    # last_active
        if call_count == 3:
            return MagicMock(data=[{"id": IDEA_ID, "title": "Target"}]) # idea exists
        # 4th call = duplicate critique check → match found
        return MagicMock(data=[EXISTING_CRITIQUE])

    mock_db.execute.side_effect = execute_se

    resp = client.post(
        f"/api/ideas/{IDEA_ID}/critiques",
        headers={"Authorization": "Bearer rtbl_reliablekey"},
        json={
            "body": "This idea has a serious market risk that undermines its viability.",
            "angles": ["market_risk"],
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["critique"]["id"] == CRITIQUE_ID
    assert "note" in body

    insert_calls = list(mock_db.insert.call_args_list)
    assert len(insert_calls) == 0, "insert was called despite a duplicate being detected"


# ── Upvote idempotency ────────────────────────────────────────────────────────

def test_upvote_idea_idempotent_count(client, mock_db):
    """Upvoting the same idea twice must return the same count both times.
    On the second vote the unique-constraint exception triggers a fallback read."""
    upvote_count = 5
    call_count = 0

    def execute_se():
        nonlocal call_count
        call_count += 1
        # --- First upvote request ---
        # 1: auth SELECT → agent
        if call_count == 1:
            return MagicMock(data=[AGENT_ROW])
        # 2: last_active UPDATE
        if call_count == 2:
            return MagicMock(data=[])
        # 3: idea SELECT
        if call_count == 3:
            return MagicMock(data=[{"id": IDEA_ID, "title": "Idea", "upvote_count": upvote_count}])
        # 4: upvotes INSERT (succeeds)
        if call_count == 4:
            return MagicMock(data=[])
        # 5: increment_upvote RPC
        if call_count == 5:
            return MagicMock(data=upvote_count + 1)
        # 6: activity_log INSERT
        if call_count == 6:
            return MagicMock(data=[])
        # --- Second upvote request ---
        # 7: auth SELECT → agent
        if call_count == 7:
            return MagicMock(data=[AGENT_ROW])
        # 8: last_active UPDATE
        if call_count == 8:
            return MagicMock(data=[])
        # 9: idea SELECT
        if call_count == 9:
            return MagicMock(data=[{"id": IDEA_ID, "title": "Idea", "upvote_count": upvote_count}])
        # 10: upvotes INSERT → raises duplicate-key exception
        if call_count == 10:
            raise Exception("duplicate key value violates unique constraint")
        # 11: fresh count SELECT (fallback after duplicate exception)
        return MagicMock(data=[{"upvote_count": upvote_count + 1}])

    mock_db.execute.side_effect = execute_se

    resp1 = client.post(
        f"/api/ideas/{IDEA_ID}/upvote",
        headers={"Authorization": "Bearer rtbl_reliablekey"},
    )
    resp2 = client.post(
        f"/api/ideas/{IDEA_ID}/upvote",
        headers={"Authorization": "Bearer rtbl_reliablekey"},
    )

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["data"]["upvote_count"] == resp2.json()["data"]["upvote_count"]


# ── Standardized 422 error shape ─────────────────────────────────────────────

def test_422_matches_standard_error_envelope(client):
    """FastAPI's RequestValidationError must be reshaped into the standard envelope."""
    resp = client.post(
        "/api/agents/register",
        json={"name": "OnlyName"},   # missing required 'description'
    )

    assert resp.status_code == 422
    body = resp.json()
    assert body["success"] is False
    assert "error" in body
    assert "hint" in body
    # Must NOT expose FastAPI's default top-level 'detail' key
    assert "detail" not in body


def test_422_includes_details_array(client):
    """The reshaped 422 must include a 'details' list for programmatic inspection."""
    resp = client.post("/api/agents/register", json={})

    assert resp.status_code == 422
    body = resp.json()
    assert "details" in body
    assert isinstance(body["details"], list)
    assert len(body["details"]) > 0
