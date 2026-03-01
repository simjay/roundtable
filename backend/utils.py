from __future__ import annotations

from database import get_db


def log_activity(
    agent_id: str,
    event_type: str,
    target_id: str | None = None,
    target_title: str | None = None,
) -> None:
    """Insert one row into activity_log. Errors are silently swallowed so that a
    logging failure never breaks the main request."""
    try:
        db = get_db()
        db.table("activity_log").insert(
            {
                "agent_id": agent_id,
                "event_type": event_type,
                "target_id": target_id,
                "target_title": target_title,
            }
        ).execute()
    except Exception:
        pass
