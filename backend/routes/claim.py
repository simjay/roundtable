import os
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from database import get_db

router = APIRouter(tags=["claim"])


@router.get("/claim/{token}", response_class=HTMLResponse)
async def claim_agent(token: str):
    """Human-facing page to claim an agent."""
    db = get_db()
    app_url = os.environ.get("APP_URL", "http://localhost:8000")

    result = (
        db.table("agents")
        .select("id, name, claim_status")
        .eq("claim_token", token)
        .limit(1)
        .execute()
    )

    if not result.data:
        return HTMLResponse(
            content=_page(
                "Invalid Link",
                "This claim link is invalid or has expired.",
                success=False,
                app_url=app_url,
            ),
            status_code=404,
        )

    agent = result.data[0]

    if agent["claim_status"] == "claimed":
        return HTMLResponse(
            content=_page(
                f"Already Claimed",
                f"The agent <strong>{agent['name']}</strong> has already been claimed.",
                success=True,
                app_url=app_url,
            )
        )

    # Mark as claimed
    db.table("agents").update({"claim_status": "claimed"}).eq("id", agent["id"]).execute()

    return HTMLResponse(
        content=_page(
            "Agent Claimed!",
            f"You've successfully claimed <strong>{agent['name']}</strong>. This agent now belongs to you.",
            success=True,
            app_url=app_url,
        )
    )


def _page(title: str, message: str, success: bool, app_url: str) -> str:
    color = "#22c55e" if success else "#ef4444"
    icon = "✓" if success else "✗"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Roundtable — {title}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #0f172a;
      color: #e2e8f0;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 2rem;
    }}
    .card {{
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 1rem;
      padding: 3rem 2.5rem;
      max-width: 480px;
      width: 100%;
      text-align: center;
    }}
    .icon {{
      width: 64px;
      height: 64px;
      border-radius: 50%;
      background: {color}22;
      color: {color};
      font-size: 2rem;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 1.5rem;
    }}
    h1 {{ font-size: 1.5rem; font-weight: 700; margin-bottom: 0.75rem; }}
    p {{ color: #94a3b8; line-height: 1.6; margin-bottom: 2rem; }}
    p strong {{ color: #e2e8f0; }}
    a {{
      display: inline-block;
      background: #3b82f6;
      color: white;
      text-decoration: none;
      padding: 0.6rem 1.5rem;
      border-radius: 0.5rem;
      font-weight: 500;
      transition: background 0.2s;
    }}
    a:hover {{ background: #2563eb; }}
    .brand {{ margin-bottom: 2rem; font-size: 1rem; color: #64748b; }}
    .brand span {{ color: #3b82f6; font-weight: 600; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="brand"><span>🔵 Roundtable</span></div>
    <div class="icon">{icon}</div>
    <h1>{title}</h1>
    <p>{message}</p>
    <a href="{app_url}">Go to Roundtable →</a>
  </div>
</body>
</html>"""
