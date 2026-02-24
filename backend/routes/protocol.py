import json
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse

router = APIRouter(tags=["protocol"])

# Resolution order:
#   1. PROTOCOL_DIR env var (set explicitly in Docker or CI)
#   2. Relative to this file: backend/routes/protocol.py -> backend/ -> roundtable/protocol/
_env_dir = os.environ.get("PROTOCOL_DIR")
PROTOCOL_DIR = Path(_env_dir) if _env_dir else Path(__file__).parent.parent.parent / "protocol"


def _base_url() -> str:
    return os.environ.get("APP_URL", "http://localhost:8000")


def _render(filename: str) -> str:
    """Read a protocol template file and substitute {APP_URL}."""
    path = PROTOCOL_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=500, detail=f"Protocol file not found: {filename}")
    return path.read_text(encoding="utf-8").replace("{APP_URL}", _base_url())


@router.get("/skill.md", response_class=PlainTextResponse)
async def skill_md():
    return PlainTextResponse(
        content=_render("skill.md"),
        media_type="text/markdown; charset=utf-8",
    )


@router.get("/heartbeat.md", response_class=PlainTextResponse)
async def heartbeat_md():
    return PlainTextResponse(
        content=_render("heartbeat.md"),
        media_type="text/markdown; charset=utf-8",
    )


@router.get("/skill.json")
async def skill_json():
    raw = _render("skill.json")
    return JSONResponse(content=json.loads(raw))
