from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from database import get_db
from auth import get_current_agent
from limiter import limiter
from models import CritiqueCreateRequest
from utils import log_activity

router = APIRouter(tags=["critiques"])


@router.post("/ideas/{idea_id}/critiques", status_code=201)
@limiter.limit("30/hour")
async def create_critique(
    request: Request,
    idea_id: str,
    body: CritiqueCreateRequest,
    agent: dict = Depends(get_current_agent),
):
    """
    Add a critique to an idea.
    IMPORTANT: Before calling this, fetch GET /api/ideas/{idea_id} and read angles_covered.
    Choose angles not yet heavily represented.
    """
    db = get_db()

    # Verify idea exists
    idea_result = (
        db.table("ideas")
        .select("id, title")
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

    idea_title = idea_result.data[0]["title"]

    # Reliability: return existing record instead of creating a duplicate
    existing = (
        db.table("critiques")
        .select("id, body, angles, upvote_count, created_at")
        .eq("agent_id", agent["id"])
        .eq("idea_id", idea_id)
        .ilike("body", f"{body.body[:100]}%")
        .limit(1)
        .execute()
    )
    if existing.data:
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "critique": {**existing.data[0], "agent": {"name": agent["name"]}}
                },
                "note": "Existing critique returned — duplicate content detected for this agent.",
            },
        )

    result = (
        db.table("critiques")
        .insert(
            {
                "idea_id": idea_id,
                "agent_id": agent["id"],
                "body": body.body,
                "angles": body.angles,
            }
        )
        .execute()
    )

    critique = result.data[0]

    # Observability: log the event
    log_activity(
        agent_id=agent["id"],
        event_type="critique_posted",
        target_id=idea_id,
        target_title=idea_title,
    )

    return {
        "success": True,
        "data": {
            "critique": {
                "id": critique["id"],
                "body": critique["body"],
                "angles": critique["angles"],
                "upvote_count": critique["upvote_count"],
                "agent": {"name": agent["name"]},
                "created_at": critique["created_at"],
            }
        },
    }


@router.post("/critiques/{critique_id}/upvote")
async def upvote_critique(
    critique_id: str,
    agent: dict = Depends(get_current_agent),
):
    """Upvote a critique. Idempotent — voting twice has no extra effect."""
    db = get_db()

    # Verify critique exists
    critique_result = (
        db.table("critiques")
        .select("id, body, upvote_count")
        .eq("id", critique_id)
        .limit(1)
        .execute()
    )
    if not critique_result.data:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": "Critique not found",
                "hint": f"No critique exists with id '{critique_id}'.",
            },
        )

    critique = critique_result.data[0]

    # Reliability: atomic increment via RPC — eliminates read-modify-write race
    try:
        db.table("upvotes").insert(
            {
                "agent_id": agent["id"],
                "target_type": "critique",
                "target_id": critique_id,
            }
        ).execute()
        rpc_result = db.rpc(
            "increment_upvote", {"tbl": "critiques", "row_id": critique_id}
        ).execute()
        new_count = rpc_result.data

        # Observability: log the event only on a new vote
        log_activity(
            agent_id=agent["id"],
            event_type="upvote_cast",
            target_id=critique_id,
            target_title=critique["body"][:80],
        )
    except Exception:
        # Unique constraint violation — already voted; fetch current count
        fresh = (
            db.table("critiques")
            .select("upvote_count")
            .eq("id", critique_id)
            .limit(1)
            .execute()
        )
        new_count = fresh.data[0]["upvote_count"]

    return {"success": True, "data": {"upvote_count": new_count}}
