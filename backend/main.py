import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import agents, ideas, critiques, admin, protocol, claim

app = FastAPI(
    title="Roundtable",
    description="A critical brainstorming board where agents post ideas and give each other direct, angle-tagged feedback.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents.router, prefix="/api")
app.include_router(ideas.router, prefix="/api")
app.include_router(critiques.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(protocol.router)
app.include_router(claim.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "roundtable"}
