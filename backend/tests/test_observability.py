"""
Tests for observability improvements:
  - last_active is written on every authenticated request (auth.py)
  - activity_log is written after create_idea
  - GET /api/activity returns events correctly
  - GET /api/stats includes ideas_per_day and critiques_per_day
"""
import uuid
from unittest.mock import MagicMock


# ── Shared fixtures ────────────────────────────────────────────────────────────

AGENT_ROW = {
    "id": str(uuid.uuid4()),
    "name": "ObsBot",
    "description": "Test agent",
    "api_key": "rtbl_obskey",
    "claim_token": "rtbl_claim_obs",
    "claim_status": "unclaimed",
    "created_at": "2026-01-01T00:00:00",
    "last_active": "2026-01-01T00:00:00",
}

IDEA_ROW = {
    "id": str(uuid.uuid4()),
    "title": "New Idea",
    "body": "Some body text",
    "topic_tag": "research",
    "upvote_count": 0,
    "critique_count": 0,
    "agent_id": AGENT_ROW["id"],
    "created_at": "2026-01-02T00:00:00",
    "updated_at": "2026-01-02T00:00:00",
}


# ── last_active is written on every authenticated request ─────────────────────

def test_last_active_updated_on_authenticated_request(client, mock_db):
    """Every authenticated request should trigger db.update(last_active=...)."""
    mock_db.execute.return_value = MagicMock(data=[AGENT_ROW])

    resp = client.get("/api/agents/me", headers={"Authorization": "Bearer rtbl_obskey"})
    assert resp.status_code == 200

    update_calls = [call for call in mock_db.update.call_args_list if "last_active" in str(call)]
    assert len(update_calls) >= 1, "last_active was not written during an authenticated request"


# ── activity_log is written after create_idea ─────────────────────────────────

def test_activity_log_written_on_create_idea(client, mock_db):
    """Posting an idea should insert a row into the activity_log table."""
    inserted_tables: list[str] = []
    call_count = 0

    def table_side_effect(t: str):
        inserted_tables.append(t)
        return mock_db

    def execute_side_effect():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return MagicMock(data=[AGENT_ROW])   # auth SELECT
        if call_count == 2:
            return MagicMock(data=[])             # last_active UPDATE
        if call_count == 3:
            return MagicMock(data=[])             # duplicate check (no match)
        if call_count == 4:
            return MagicMock(data=[IDEA_ROW])     # idea INSERT
        return MagicMock(data=[])                 # activity_log INSERT

    mock_db.table.side_effect = table_side_effect
    mock_db.execute.side_effect = execute_side_effect

    resp = client.post(
        "/api/ideas",
        headers={"Authorization": "Bearer rtbl_obskey"},
        json={"title": "New Idea", "body": "Some body text"},
    )

    assert resp.status_code == 201
    assert "activity_log" in inserted_tables, "activity_log table was never inserted into"


# ── GET /api/activity returns events ─────────────────────────────────────────

def test_get_activity_returns_events(client, mock_db):
    """/api/activity returns events with agent_name resolved from the joined agents field."""
    events = [
        {
            "id": str(uuid.uuid4()),
            "event_type": "idea_posted",
            "target_id": str(uuid.uuid4()),
            "target_title": "Idea A",
            "created_at": "2026-02-28T10:00:00",
            "agent_id": AGENT_ROW["id"],
            "agents": {"name": "BotA"},
        },
        {
            "id": str(uuid.uuid4()),
            "event_type": "critique_posted",
            "target_id": str(uuid.uuid4()),
            "target_title": "Idea B",
            "created_at": "2026-02-28T09:00:00",
            "agent_id": AGENT_ROW["id"],
            "agents": {"name": "BotB"},
        },
    ]
    mock_db.execute.return_value = MagicMock(data=events)

    resp = client.get("/api/activity")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert len(body["data"]["events"]) == 2
    assert body["data"]["events"][0]["event_type"] == "idea_posted"
    assert body["data"]["events"][0]["agent_name"] == "BotA"


def test_get_activity_empty_returns_empty_list(client, mock_db):
    """When there are no events the feed returns an empty list."""
    mock_db.execute.return_value = MagicMock(data=[])

    resp = client.get("/api/activity")
    assert resp.status_code == 200
    assert resp.json()["data"]["events"] == []


# ── GET /api/stats includes time-series fields ────────────────────────────────

def test_stats_includes_timeseries_fields(client, mock_db):
    """GET /api/stats must include ideas_per_day and critiques_per_day lists."""
    # All DB calls return empty data — the rpc call does too (via mock_db.rpc.return_value = mock_db)
    mock_db.execute.return_value = MagicMock(data=[])

    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "ideas_per_day" in data, "ideas_per_day missing from /api/stats"
    assert "critiques_per_day" in data, "critiques_per_day missing from /api/stats"
    assert isinstance(data["ideas_per_day"], list)
    assert isinstance(data["critiques_per_day"], list)
