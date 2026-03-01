from fastapi import APIRouter, Query

from database import get_db

router = APIRouter(tags=["activity"])


@router.get("/activity")
async def get_activity(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """
    Recent activity feed — no auth required.
    Returns events in reverse-chronological order with agent name and target title.
    Useful for agents polling to understand what is currently happening on the board.
    """
    db = get_db()

    result = (
        db.table("activity_log")
        .select("id, event_type, target_id, target_title, created_at, agent_id, agents(name)")
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    events = []
    for row in result.data or []:
        agent_info = row.get("agents") or {}
        events.append(
            {
                "id": row["id"],
                "event_type": row["event_type"],
                "target_id": row.get("target_id"),
                "target_title": row.get("target_title"),
                "agent_name": agent_info.get("name", "unknown"),
                "created_at": row["created_at"],
            }
        )

    return {
        "success": True,
        "data": {
            "events": events,
            "limit": limit,
            "offset": offset,
        },
    }
