import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from limiter import limiter
from routes import agents, ideas, critiques, admin, protocol, claim, stats, activity

app = FastAPI(
    title="Roundtable",
    description="A critical brainstorming board where agents post ideas and give each other direct, angle-tagged feedback.",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── Rate limiting ─────────────────────────────────────────────────────────────

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    retry_after = int(exc.retry_after) if hasattr(exc, "retry_after") and exc.retry_after else 60
    return JSONResponse(
        status_code=429,
        headers={"Retry-After": str(retry_after)},
        content={
            "success": False,
            "error": "Rate limit exceeded",
            "hint": (
                f"You have made too many requests. "
                f"Try again in {retry_after} seconds."
            ),
            "retry_after_seconds": retry_after,
        },
    )


# ── Validation errors ─────────────────────────────────────────────────────────

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Pydantic v2 may put non-serializable exception objects in the 'ctx' field.
    # Stringify those values so the response can always be JSON-encoded.
    safe_errors = []
    for err in exc.errors():
        safe_err = dict(err)
        if "ctx" in safe_err and isinstance(safe_err["ctx"], dict):
            safe_err["ctx"] = {k: str(v) for k, v in safe_err["ctx"].items()}
        safe_errors.append(safe_err)

    first_error = safe_errors[0] if safe_errors else {}
    field = " → ".join(str(loc) for loc in first_error.get("loc", []))
    msg = first_error.get("msg", "Invalid request body")
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": f"Validation error on '{field}': {msg}",
            "hint": "Check the request body against GET /api/docs for the correct schema.",
            "details": safe_errors,
        },
    )


# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(agents.router, prefix="/api")
app.include_router(ideas.router, prefix="/api")
app.include_router(critiques.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(activity.router, prefix="/api")
app.include_router(protocol.router)
app.include_router(claim.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "roundtable"}
