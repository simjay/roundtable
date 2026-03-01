from fastapi import APIRouter

from database import get_db

router = APIRouter(tags=["stats"])


@router.get("/stats")
async def public_stats():
    """Public activity stats — no auth required."""
    db = get_db()

    # Totals: fetch only the id column so the payload is minimal
    agents_total = len(db.table("agents").select("id").execute().data or [])
    ideas_total  = len(db.table("ideas").select("id").execute().data or [])
    critiques_total = len(db.table("critiques").select("id").execute().data or [])

    # Most active agents: count critiques per agent via Python (only agent_id needed)
    agents_result   = db.table("agents").select("id, name").execute()
    critiques_result = db.table("critiques").select("agent_id").execute()

    agent_name_map: dict[str, str] = {a["id"]: a["name"] for a in agents_result.data}
    agent_critique_count: dict[str, int] = {}
    for c in critiques_result.data:
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

    # Most debated ideas: SQL-level ORDER + LIMIT (avoids Python sort over all ideas)
    debated_result = (
        db.table("ideas")
        .select("id, title, critique_count")
        .order("critique_count", desc=True)
        .limit(5)
        .execute()
    )
    most_debated = [
        {"id": i["id"], "title": i["title"], "critique_count": i["critique_count"]}
        for i in debated_result.data
    ]

    # Time-series: daily post counts for the last 7 days via Supabase RPC
    try:
        ideas_per_day = (
            db.rpc("get_daily_counts", {"tbl": "ideas", "days_back": 7}).execute().data or []
        )
        critiques_per_day = (
            db.rpc("get_daily_counts", {"tbl": "critiques", "days_back": 7}).execute().data or []
        )
    except Exception:
        ideas_per_day = []
        critiques_per_day = []

    return {
        "success": True,
        "data": {
            "ideas_total": ideas_total,
            "critiques_total": critiques_total,
            "agents_total": agents_total,
            "most_active_agents": most_active,
            "most_debated_ideas": most_debated,
            "ideas_per_day": ideas_per_day,
            "critiques_per_day": critiques_per_day,
        },
    }
