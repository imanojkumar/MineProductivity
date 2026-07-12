"""Tests for mineproductivity.agents.metadata (design spec §29)."""

from __future__ import annotations

import pytest

from mineproductivity.agents.exceptions import AgentValidationError
from mineproductivity.agents.metadata import AgentCategory, AgentMetadata


def _meta(**overrides: object) -> AgentMetadata:
    kwargs: dict[str, object] = {
        "code": "FLEET.ReassignmentAdvisor",
        "category": AgentCategory.FLEET,
        "description": "Advises on truck reassignment.",
    }
    kwargs.update(overrides)
    return AgentMetadata(**kwargs)  # type: ignore[arg-type]


class TestAgentCategory:
    def test_exactly_the_ten_closed_members(self) -> None:
        """Design spec §29: a closed enum; adding a member is a
        governance-reviewed change."""
        assert {member.value for member in AgentCategory} == {
            "production",
            "dispatch",
            "fleet",
            "maintenance",
            "drill_and_blast",
            "shift_supervisor",
            "esg",
            "safety",
            "executive_advisor",
            "planning",
        }


class TestAgentMetadata:
    def test_name_defaults_to_code(self) -> None:
        assert _meta().name == "FLEET.ReassignmentAdvisor"

    def test_explicit_name_is_kept(self) -> None:
        assert _meta(name="Reassignment Advisor").name == "Reassignment Advisor"

    def test_version_defaults(self) -> None:
        assert _meta().version == "1.0.0"

    def test_empty_code_raises(self) -> None:
        with pytest.raises(AgentValidationError, match="code"):
            _meta(code="  ")

    def test_non_category_raises(self) -> None:
        with pytest.raises(AgentValidationError, match="category"):
            _meta(category="fleet")

    def test_frozen(self) -> None:
        with pytest.raises(AttributeError):
            _meta().code = "OTHER"  # type: ignore[misc]
