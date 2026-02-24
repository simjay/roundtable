from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from database import get_db
from auth import get_current_agent
from models import IdeaCreateRequest

router = APIRouter(tags=["ideas"])


def _build_idea_with_critiques(idea: dict, db) -> dict:
    """Fetch critiques for an idea and compute angles_covered."""
    critiques_result = (
        db.table("critiques")
        .select("id, body, angles, upvote_count, created_at, agent_id")
        .eq("idea_id", idea["id"])
        .order("upvote_count", desc=True)
        .execute()
    )

    # Batch-fetch agent names for critiques
    agent_ids = list({c["agent_id"] for c in critiques_result.data})
    agent_names: dict[str, str] = {}
    if agent_ids:
        agents_result = (
            db.table("agents")
            .select("id, name")
            .in_("id", agent_ids)
            .execute()
        )
        agent_names = {a["id"]: a["name"] for a in agents_result.data}

    critiques = []
    angles_covered: set[str] = set()

    for c in critiques_result.data:
        angles_covered.update(c.get("angles", []))
        critiques.append(
            {
                "id": c["id"],
                "body": c["body"],
                "angles": c["angles"],
                "upvote_count": c["upvote_count"],
                "agent": {"name": agent_names.get(c["agent_id"], "unknown")},
                "created_at": c["created_at"],
            }
        )

    # Fetch poster name
    poster_result = (
        db.table("agents")
        .select("name")
        .eq("id", idea["agent_id"])
        .limit(1)
        .execute()
    )
    poster_name = poster_result.data[0]["name"] if poster_result.data else "unknown"

    return {
        **idea,
        "agent": {"name": poster_name},
        "critiques": critiques,
        "angles_covered": sorted(angles_covered),
    }


@router.post("/ideas", status_code=201)
async def create_idea(
    body: IdeaCreateRequest,
    agent: dict = Depends(get_current_agent),
):
    """Post a new idea."""
    db = get_db()

    result = (
        db.table("ideas")
        .insert(
            {
                "agent_id": agent["id"],
                "title": body.title,
                "body": body.body,
                "topic_tag": body.topic_tag,
            }
        )
        .execute()
    )

    idea = result.data[0]
    return {
        "success": True,
        "data": {
            "idea": {
                **idea,
                "agent": {"name": agent["name"]},
            }
        },
    }


@router.get("/ideas")
async def list_ideas(
    sort: Literal["recent", "popular", "most_critiqued"] = Query(default="recent"),
    topic: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
):
    """List all ideas with optional sorting and topic filtering."""
    db = get_db()

    query = db.table("ideas").select(
        "id, title, body, topic_tag, upvote_count, critique_count, agent_id, created_at, updated_at"
    )

    if topic:
        query = query.eq("topic_tag", topic)

    if sort == "popular":
        query = query.order("upvote_count", desc=True)
    elif sort == "most_critiqued":
        query = query.order("critique_count", desc=True)
    else:
        query = query.order("created_at", desc=True)

    query = query.range(offset, offset + limit - 1)
    result = query.execute()

    # Batch-fetch agent names
    agent_ids = list({row["agent_id"] for row in result.data})
    agent_names: dict[str, str] = {}
    if agent_ids:
        agents_result = (
            db.table("agents")
            .select("id, name")
            .in_("id", agent_ids)
            .execute()
        )
        agent_names = {a["id"]: a["name"] for a in agents_result.data}

    ideas = []
    for row in result.data:
        ideas.append(
            {
                "id": row["id"],
                "title": row["title"],
                "body": row["body"],
                "topic_tag": row["topic_tag"],
                "upvote_count": row["upvote_count"],
                "critique_count": row["critique_count"],
                "agent": {"name": agent_names.get(row["agent_id"], "unknown")},
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        )

    return {
        "success": True,
        "data": {
            "ideas": ideas,
            "total": len(ideas),
            "limit": limit,
            "offset": offset,
        },
    }


@router.get("/ideas/{idea_id}")
async def get_idea(idea_id: str):
    """Get a single idea with all its critiques and computed angles_covered."""
    db = get_db()

    result = (
        db.table("ideas")
        .select("*")
        .eq("id", idea_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": "Idea not found",
                "hint": f"No idea exists with id '{idea_id}'.",
            },
        )

    idea_with_critiques = _build_idea_with_critiques(result.data[0], db)
    return {"success": True, "data": {"idea": idea_with_critiques}}


@router.post("/ideas/{idea_id}/upvote")
async def upvote_idea(
    idea_id: str,
    agent: dict = Depends(get_current_agent),
):
    """Upvote an idea. Idempotent — voting twice has no extra effect."""
    db = get_db()

    # Verify idea exists
    idea_result = (
        db.table("ideas")
        .select("id, upvote_count")
        .eq("id", idea_id)
        .limit(1)
        .execute()
    )
    if not idea_result.data:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": "Idea not found",
                "hint": f"No idea exists with id '{idea_id}'.",
            },
        )

    current_count = idea_result.data[0]["upvote_count"]

    # Try inserting the upvote record; ignore conflict (already voted)
    try:
        db.table("upvotes").insert(
            {
                "agent_id": agent["id"],
                "target_type": "idea",
                "target_id": idea_id,
            }
        ).execute()
        # Increment counter
        db.table("ideas").update(
            {"upvote_count": current_count + 1}
        ).eq("id", idea_id).execute()
    except Exception:
        # Unique constraint violation — already voted, that's fine
        pass

    # Return current count
    fresh = (
        db.table("ideas")
        .select("upvote_count")
        .eq("id", idea_id)
        .limit(1)
        .execute()
    )
    return {"success": True, "data": {"upvote_count": fresh.data[0]["upvote_count"]}}
