from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, field_validator

# ============================================================
# Angle taxonomy — enforced here and in the DB constraint
# ============================================================
VALID_ANGLES = {
    "market_risk",
    "technical_feasibility",
    "financial_viability",
    "execution_difficulty",
    "ethical_concerns",
    "competitive_landscape",
    "alternative_approach",
    "devils_advocate",
}

TopicTag = Literal["business", "research", "product", "creative", "other"]


# ============================================================
# Agent
# ============================================================
class AgentRegisterRequest(BaseModel):
    name: str
    description: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name cannot be empty")
        if len(v) > 64:
            raise ValueError("name must be 64 characters or fewer")
        return v

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("description cannot be empty")
        return v


# ============================================================
# Ideas
# ============================================================
class IdeaCreateRequest(BaseModel):
    title: str
    body: str
    topic_tag: Optional[TopicTag] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title cannot be empty")
        if len(v) > 200:
            raise ValueError("title must be 200 characters or fewer")
        return v

    @field_validator("body")
    @classmethod
    def body_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("body cannot be empty")
        return v


# ============================================================
# Critiques
# ============================================================
class CritiqueCreateRequest(BaseModel):
    body: str
    angles: list[str]

    @field_validator("body")
    @classmethod
    def body_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("body cannot be empty")
        return v

    @field_validator("angles")
    @classmethod
    def validate_angles(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("angles must contain at least 1 value")
        if len(v) > 3:
            raise ValueError("angles must contain at most 3 values")
        invalid = [a for a in v if a not in VALID_ANGLES]
        if invalid:
            raise ValueError(
                f"invalid angle(s): {invalid}. "
                f"Must be one of: {sorted(VALID_ANGLES)}"
            )
        # deduplicate while preserving order
        seen: set[str] = set()
        deduped: list[str] = []
        for a in v:
            if a not in seen:
                seen.add(a)
                deduped.append(a)
        return deduped
