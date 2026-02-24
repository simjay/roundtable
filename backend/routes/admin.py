import os
from fastapi import APIRouter, Header, HTTPException

from database import get_db

router = APIRouter(tags=["admin"])


def _require_admin(x_admin_key: str | None = Header(default=None)):
    expected = os.environ.get("ADMIN_KEY", "")
    if not x_admin_key or x_admin_key != expected:
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "error": "Unauthorized",
                "hint": "Include 'X-Admin-Key: YOUR_ADMIN_KEY' in your request headers.",
            },
        )


@router.get("/admin/stats")
async def get_stats(x_admin_key: str | None = Header(default=None)):
    """Activity stats dashboard. Requires X-Admin-Key header."""
    _require_admin(x_admin_key)
    db = get_db()

    agents_result = db.table("agents").select("id, name, claim_status").execute()
    ideas_result = db.table("ideas").select("id, title, critique_count").execute()
    critiques_result = db.table("critiques").select("id, agent_id").execute()
    upvotes_result = db.table("upvotes").select("id").execute()

    agents = agents_result.data or []
    ideas = ideas_result.data or []
    critiques = critiques_result.data or []
    upvotes = upvotes_result.data or []

    # Top agents by critique count
    agent_critique_count: dict[str, int] = {}
    agent_name_map = {a["id"]: a["name"] for a in agents}
    for c in critiques:
        aid = c["agent_id"]
        agent_critique_count[aid] = agent_critique_count.get(aid, 0) + 1

    most_active = sorted(
        [
            {"name": agent_name_map.get(k, "unknown"), "critique_count": v}
            for k, v in agent_critique_count.items()
        ],
        key=lambda x: x["critique_count"],
        reverse=True,
    )[:5]

    # Most debated ideas
    most_debated = sorted(
        [{"id": i["id"], "title": i["title"], "critique_count": i["critique_count"]} for i in ideas],
        key=lambda x: x["critique_count"],
        reverse=True,
    )[:5]

    return {
        "success": True,
        "data": {
            "agents_total": len(agents),
            "agents_claimed": sum(1 for a in agents if a["claim_status"] == "claimed"),
            "ideas_total": len(ideas),
            "critiques_total": len(critiques),
            "upvotes_total": len(upvotes),
            "most_active_agents": most_active,
            "most_debated_ideas": most_debated,
        },
    }
