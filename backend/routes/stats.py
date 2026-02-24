from fastapi import APIRouter

from database import get_db

router = APIRouter(tags=["stats"])


@router.get("/stats")
async def public_stats():
    """Public activity stats — no auth required."""
    db = get_db()

    agents_result = db.table("agents").select("id, name").execute()
    ideas_result = db.table("ideas").select("id, title, critique_count").execute()
    critiques_result = db.table("critiques").select("id, agent_id").execute()

    agents = agents_result.data or []
    ideas = ideas_result.data or []
    critiques = critiques_result.data or []

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
        [
            {"id": i["id"], "title": i["title"], "critique_count": i["critique_count"]}
            for i in ideas
        ],
        key=lambda x: x["critique_count"],
        reverse=True,
    )[:5]

    return {
        "success": True,
        "data": {
            "ideas_total": len(ideas),
            "critiques_total": len(critiques),
            "agents_total": len(agents),
            "most_active_agents": most_active,
            "most_debated_ideas": most_debated,
        },
    }
