import os
import secrets
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from database import get_db
from auth import get_current_agent
from models import AgentRegisterRequest

router = APIRouter(tags=["agents"])


def _generate_api_key() -> str:
    return f"rtbl_{secrets.token_urlsafe(24)}"


def _generate_claim_token() -> str:
    return f"rtbl_claim_{secrets.token_urlsafe(18)}"


@router.post("/agents/register", status_code=201)
async def register_agent(body: AgentRegisterRequest):
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

    db.table("agents").insert(
        {
            "name": body.name,
            "description": body.description,
            "api_key": api_key,
            "claim_token": claim_token,
        }
    ).execute()

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
