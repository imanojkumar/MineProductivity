"""Tests for mineproductivity.agents.capability (design spec §9)."""

from __future__ import annotations

import uuid

import pytest

from mineproductivity.agents.capability import (
    AgentCapabilitySet,
    Permission,
    publish_capabilities,
    published_capabilities,
)
from mineproductivity.core.serialization import to_dict


class TestPermission:
    def test_scope_defaults_empty_and_is_frozen(self) -> None:
        permission = Permission(capability="approve_shutdown")
        assert dict(permission.scope) == {}
        with pytest.raises(TypeError):
            permission.scope["pit"] = "north"  # type: ignore[index]

    def test_scope_is_copied_not_aliased(self) -> None:
        source = {"pit": "north"}
        permission = Permission(capability="reassign_truck", scope=source)
        source["pit"] = "south"
        assert permission.scope["pit"] == "north"

    def test_value_equality(self) -> None:
        assert Permission(capability="x") == Permission(capability="x")
        assert Permission(capability="x") != Permission(capability="y")


class TestAgentCapabilitySet:
    def test_carries_agent_code_and_permissions(self) -> None:
        caps = AgentCapabilitySet(
            agent_code="FLEET.ReassignmentAdvisor",
            permissions=(Permission(capability="reassign_truck"),),
        )
        assert caps.permissions[0].capability == "reassign_truck"

    def test_serializes_via_core_serialization(self) -> None:
        caps = AgentCapabilitySet(agent_code="A", permissions=(Permission(capability="c"),))
        assert to_dict(caps)["agent_code"] == "A"


class TestGovernedStore:
    def test_published_set_is_an_explicit_authored_artifact(self) -> None:
        """Design spec §9: a capability grant is always published,
        never inferred from an Agent subclass's own code."""
        agent_code = f"FLEET.CapabilityFixture{uuid.uuid4().hex}"
        assert published_capabilities(agent_code) is None
        caps = AgentCapabilitySet(
            agent_code=agent_code, permissions=(Permission(capability="reassign_truck"),)
        )
        assert publish_capabilities(caps) is caps
        assert published_capabilities(agent_code) is caps
