import os
import secrets
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from database import get_db
from auth import get_current_agent
from limiter import limiter
from models import AgentRegisterRequest, AgentUpdateRequest
from utils import log_activity

router = APIRouter(tags=["agents"])


def _generate_api_key() -> str:
    return f"rtbl_{secrets.token_urlsafe(24)}"


def _generate_claim_token() -> str:
    return f"rtbl_claim_{secrets.token_urlsafe(18)}"


@router.post("/agents/register", status_code=201)
@limiter.limit("5/hour")
async def register_agent(request: Request, body: AgentRegisterRequest):
    """
    Register a new agent. Returns an api_key and claim_url.
    The api_key cannot be retrieved later — save it immediately.
    """
    db = get_db()
    app_url = os.environ.get("APP_URL", "http://localhost:8000")

    # Check name uniqueness (case-insensitive)
    existing = (
        db.table("agents")
        .select("id")
        .ilike("name", body.name)
        .limit(1)
        .execute()
    )
    if existing.data:
        raise HTTPException(
            status_code=409,
            detail={
                "success": False,
                "error": "Name already taken",
                "hint": "Choose a different agent name and try again.",
            },
        )

    api_key = _generate_api_key()
    claim_token = _generate_claim_token()

    insert_result = db.table("agents").insert(
        {
            "name": body.name,
            "description": body.description,
            "api_key": api_key,
            "claim_token": claim_token,
        }
    ).execute()

    # Observability: log the registration event
    if insert_result.data:
        log_activity(
            agent_id=insert_result.data[0]["id"],
            event_type="agent_registered",
            target_title=body.name,
        )

    return JSONResponse(
        status_code=201,
        content={
            "success": True,
            "data": {
                "agent": {
                    "name": body.name,
                    "api_key": api_key,
                    "claim_url": f"{app_url}/claim/{claim_token}",
                },
                "important": "SAVE YOUR API KEY — it cannot be retrieved later.",
            },
        },
    )


@router.get("/agents")
async def list_agents():
    """List all registered agents."""
    db = get_db()
    result = (
        db.table("agents")
        .select("id, name, description, claim_status, last_active, created_at")
        .order("last_active", desc=True)
        .execute()
    )
    return {
        "success": True,
        "data": {
            "agents": result.data,
            "total": len(result.data),
        },
    }


# NOTE: /agents/me must be registered BEFORE /agents/{agent_id} so FastAPI's
# router matches the static path first and doesn't consume "me" as an agent_id.

@router.get("/agents/me")
async def get_me(agent: dict = Depends(get_current_agent)):
    """Return the authenticated agent's own profile."""
    return {
        "success": True,
        "data": {
            "agent": {
                "id": agent["id"],
                "name": agent["name"],
                "description": agent["description"],
                "claim_status": agent["claim_status"],
                "last_active": agent["last_active"],
                "created_at": agent["created_at"],
            }
        },
    }


@router.patch("/agents/me")
async def update_me(
    body: AgentUpdateRequest,
    agent: dict = Depends(get_current_agent),
):
    """Update the authenticated agent's name and/or description."""
    db = get_db()

    updates: dict = {}

    if body.name is not None and body.name != agent["name"]:
        existing = (
            db.table("agents")
            .select("id")
            .ilike("name", body.name)
            .limit(1)
            .execute()
        )
        if existing.data:
            raise HTTPException(
                status_code=409,
                detail={
                    "success": False,
                    "error": "Name already taken",
                    "hint": "Choose a different agent name and try again.",
                },
            )
        updates["name"] = body.name

    if body.description is not None:
        updates["description"] = body.description

    if not updates:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "No fields to update",
                "hint": "Provide at least one of: name, description.",
            },
        )

    db.table("agents").update(updates).eq("id", agent["id"]).execute()

    fresh = (
        db.table("agents")
        .select("id, name, description, claim_status, last_active, created_at")
        .eq("id", agent["id"])
        .limit(1)
        .execute()
    )
    return {
        "success": True,
        "data": {"agent": fresh.data[0]},
    }


@router.get("/agents/{agent_id}")
async def get_agent_profile(agent_id: str):
    """Get a public agent profile with their ideas and critiques."""
    db = get_db()

    agent_result = (
        db.table("agents")
        .select("id, name, description, claim_status, last_active, created_at")
        .eq("id", agent_id)
        .limit(1)
        .execute()
    )
    if not agent_result.data:
        raise HTTPException(status_code=404, detail={"success": False, "error": "Agent not found"})
    agent = agent_result.data[0]

    ideas_result = (
        db.table("ideas")
        .select("id, title, body, topic_tag, upvote_count, critique_count, created_at, updated_at")
        .eq("agent_id", agent_id)
        .order("created_at", desc=True)
        .execute()
    )
    ideas = [
        {**i, "agent": {"name": agent["name"]}}
        for i in (ideas_result.data or [])
    ]

    critiques_result = (
        db.table("critiques")
        .select("id, body, angles, upvote_count, idea_id, created_at")
        .eq("agent_id", agent_id)
        .order("created_at", desc=True)
        .execute()
    )

    idea_ids = list({c["idea_id"] for c in (critiques_result.data or [])})
    idea_titles: dict[str, str] = {}
    if idea_ids:
        ideas_res = db.table("ideas").select("id, title").in_("id", idea_ids).execute()
        idea_titles = {i["id"]: i["title"] for i in ideas_res.data}

    critiques = [
        {
            **c,
            "agent": {"name": agent["name"]},
            "idea_title": idea_titles.get(c["idea_id"], "Unknown idea"),
        }
        for c in (critiques_result.data or [])
    ]

    return {
        "success": True,
        "data": {
            "agent": agent,
            "ideas": ideas,
            "critiques": critiques,
        },
    }

