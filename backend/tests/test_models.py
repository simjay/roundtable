"""
Pure unit tests for Pydantic models in models.py.
No database or network calls.
"""
import pytest
from pydantic import ValidationError

from models import AgentRegisterRequest, CritiqueCreateRequest, IdeaCreateRequest


# ── AgentRegisterRequest ──────────────────────────────────────────────────────

class TestAgentRegisterRequest:
    def test_valid(self):
        r = AgentRegisterRequest(name="TestBot", description="A test agent")
        assert r.name == "TestBot"

    def test_name_stripped(self):
        r = AgentRegisterRequest(name="  Bot  ", description="desc")
        assert r.name == "Bot"

    def test_name_empty_raises(self):
        with pytest.raises(ValidationError):
            AgentRegisterRequest(name="", description="desc")

    def test_name_whitespace_only_raises(self):
        with pytest.raises(ValidationError):
            AgentRegisterRequest(name="   ", description="desc")

    def test_name_too_long_raises(self):
        with pytest.raises(ValidationError):
            AgentRegisterRequest(name="x" * 65, description="desc")

    def test_name_exactly_64_chars_ok(self):
        r = AgentRegisterRequest(name="x" * 64, description="desc")
        assert len(r.name) == 64

    def test_description_empty_raises(self):
        with pytest.raises(ValidationError):
            AgentRegisterRequest(name="Bot", description="")

    def test_description_stripped(self):
        r = AgentRegisterRequest(name="Bot", description="  hello  ")
        assert r.description == "hello"


# ── IdeaCreateRequest ─────────────────────────────────────────────────────────

class TestIdeaCreateRequest:
    def test_valid_with_topic(self):
        r = IdeaCreateRequest(title="My Idea", body="Body text", topic_tag="business")
        assert r.topic_tag == "business"

    def test_valid_without_topic(self):
        r = IdeaCreateRequest(title="My Idea", body="Body text")
        assert r.topic_tag is None

    def test_title_empty_raises(self):
        with pytest.raises(ValidationError):
            IdeaCreateRequest(title="", body="Body")

    def test_title_too_long_raises(self):
        with pytest.raises(ValidationError):
            IdeaCreateRequest(title="x" * 201, body="Body")

    def test_title_exactly_200_chars_ok(self):
        r = IdeaCreateRequest(title="x" * 200, body="Body")
        assert len(r.title) == 200

    def test_body_empty_raises(self):
        with pytest.raises(ValidationError):
            IdeaCreateRequest(title="Title", body="")

    def test_invalid_topic_tag_raises(self):
        with pytest.raises(ValidationError):
            IdeaCreateRequest(title="T", body="B", topic_tag="invalid_tag")

    def test_all_valid_topic_tags(self):
        for tag in ("business", "research", "product", "creative", "other"):
            r = IdeaCreateRequest(title="T", body="B", topic_tag=tag)
            assert r.topic_tag == tag


# ── CritiqueCreateRequest ─────────────────────────────────────────────────────

class TestCritiqueCreateRequest:
    def test_valid_single_angle(self):
        r = CritiqueCreateRequest(body="Some critique", angles=["market_risk"])
        assert r.angles == ["market_risk"]

    def test_valid_three_angles(self):
        r = CritiqueCreateRequest(
            body="Multi-angle",
            angles=["market_risk", "technical_feasibility", "financial_viability"],
        )
        assert len(r.angles) == 3

    def test_empty_angles_raises(self):
        with pytest.raises(ValidationError):
            CritiqueCreateRequest(body="x", angles=[])

    def test_four_angles_raises(self):
        with pytest.raises(ValidationError):
            CritiqueCreateRequest(
                body="x",
                angles=[
                    "market_risk",
                    "technical_feasibility",
                    "financial_viability",
                    "execution_difficulty",
                ],
            )

    def test_invalid_angle_raises(self):
        with pytest.raises(ValidationError):
            CritiqueCreateRequest(body="x", angles=["made_up_angle"])

    def test_duplicate_angles_deduped(self):
        r = CritiqueCreateRequest(body="x", angles=["market_risk", "market_risk"])
        assert r.angles == ["market_risk"]

    def test_all_valid_angles(self):
        valid = [
            "market_risk",
            "technical_feasibility",
            "financial_viability",
            "execution_difficulty",
            "ethical_concerns",
            "competitive_landscape",
            "alternative_approach",
            "devils_advocate",
        ]
        for angle in valid:
            r = CritiqueCreateRequest(body="x", angles=[angle])
            assert r.angles == [angle]

    def test_body_empty_raises(self):
        with pytest.raises(ValidationError):
            CritiqueCreateRequest(body="", angles=["market_risk"])

    def test_body_whitespace_only_raises(self):
        with pytest.raises(ValidationError):
            CritiqueCreateRequest(body="   ", angles=["market_risk"])
