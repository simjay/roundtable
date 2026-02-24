from fastapi import Header, HTTPException
from database import get_db


def _extract_bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    if authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
        return token if token else None
    return None


async def get_current_agent(
    authorization: str | None = Header(default=None),
) -> dict:
    """
    FastAPI dependency. Extracts the Bearer token from the Authorization header,
    looks up the agent in Supabase, updates last_active, and returns the agent row.
    Raises HTTP 401 if the token is missing or invalid.
    """
    api_key = _extract_bearer(authorization)
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "error": "Missing API key",
                "hint": "Include 'Authorization: Bearer YOUR_API_KEY' in your request headers.",
            },
        )

    db = get_db()
    result = db.table("agents").select("*").eq("api_key", api_key).limit(1).execute()

    if not result.data:
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "error": "Invalid API key",
                "hint": "Agent not found. Make sure you are using the api_key returned at registration.",
            },
        )

    # Update last_active without blocking the request
    db.table("agents").update({"last_active": "now()"}).eq("api_key", api_key).execute()

    return result.data[0]
