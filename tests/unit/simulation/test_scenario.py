"""Tests for mineproductivity.simulation.scenario."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from mineproductivity.core import BaseValueObject
from mineproductivity.core.serialization import to_dict
from mineproductivity.digital_twin import TwinSnapshot, TwinState, TwinStatus
from mineproductivity.events import AsOf
from mineproductivity.simulation.exceptions import (
    ScenarioConflictError,
    SimulationValidationError,
)
from mineproductivity.simulation.scenario import (
    Scenario,
    ScenarioStatus,
    publish_scenario,
    published_scenario,
    scenario_history,
)

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _unique_code() -> str:
    return f"TEST.Scenario.{uuid.uuid4().hex}"


def _scenario(**overrides: object) -> Scenario:
    fields: dict[str, object] = {
        "code": "FLEET.NightShiftSurge",
        "model_code": "MONTECARLO.HaulCycleVariability",
        "time_horizon": timedelta(hours=12),
    }
    fields.update(overrides)
    return Scenario(**fields)  # type: ignore[arg-type]


class TestScenarioStatus:
    def test_members(self) -> None:
        assert {member.value for member in ScenarioStatus} == {
            "proposed",
            "active",
            "superseded",
            "retired",
        }


class TestScenarioConstruction:
    def test_minimal_valid_construction(self) -> None:
        scenario = _scenario()
        assert scenario.version == "1.0.0"
        assert scenario.status is ScenarioStatus.PROPOSED
        assert scenario.initial_state is None
        assert scenario.as_of is None
        assert dict(scenario.parameters) == {}

    def test_is_a_frozen_value_object(self) -> None:
        assert issubclass(Scenario, BaseValueObject)

    def test_parameters_are_frozen_into_a_read_only_mapping(self) -> None:
        scenario = _scenario(parameters={"trucks_added": 3})
        with pytest.raises(TypeError):
            scenario.parameters["more"] = 1  # type: ignore[index]

    def test_initial_state_reuses_a_twin_snapshot_directly(self) -> None:
        """Design spec §9: no second 'starting condition' concept."""
        snapshot = TwinSnapshot(
            twin_id="FLEET-NORTH",
            state=TwinState(attributes={"trucks": 24}, captured_at=_EPOCH),
            status=TwinStatus.SYNCHRONIZED,
            as_of=AsOf(utc=_EPOCH),
        )
        assert _scenario(initial_state=snapshot).initial_state is snapshot

    def test_empty_code_raises(self) -> None:
        with pytest.raises(SimulationValidationError, match="code must not be empty"):
            _scenario(code="  ")

    def test_empty_model_code_raises(self) -> None:
        with pytest.raises(SimulationValidationError, match="model_code must not be empty"):
            _scenario(model_code="")

    def test_serializes_generically(self) -> None:
        assert to_dict(_scenario())["code"] == "FLEET.NightShiftSurge"


class TestPublishScenario:
    def test_first_publication_succeeds(self) -> None:
        code = _unique_code()
        scenario = _scenario(code=code)
        assert publish_scenario(scenario) is scenario
        assert published_scenario(code) is scenario

    def test_lookup_of_unpublished_code_returns_none(self) -> None:
        assert published_scenario(_unique_code()) is None

    def test_changing_an_active_scenario_at_the_same_version_raises(self) -> None:
        code = _unique_code()
        publish_scenario(_scenario(code=code, status=ScenarioStatus.ACTIVE))
        changed = _scenario(code=code, status=ScenarioStatus.ACTIVE, parameters={"trucks_added": 5})
        with pytest.raises(ScenarioConflictError, match="requires a new version"):
            publish_scenario(changed)

    def test_publishing_a_new_version_supersedes_the_prior_active_version(self) -> None:
        code = _unique_code()
        publish_scenario(_scenario(code=code, version="1.0.0", status=ScenarioStatus.ACTIVE))
        v2 = _scenario(
            code=code,
            version="2.0.0",
            status=ScenarioStatus.ACTIVE,
            parameters={"trucks_added": 5},
        )
        publish_scenario(v2)
        assert published_scenario(code) is v2
        history = scenario_history(code)
        assert len(history) == 1
        assert history[0].version == "1.0.0"
        assert history[0].status is ScenarioStatus.SUPERSEDED

    def test_changing_while_prior_is_not_active_does_not_raise(self) -> None:
        code = _unique_code()
        publish_scenario(_scenario(code=code))  # PROPOSED
        changed = _scenario(code=code, status=ScenarioStatus.ACTIVE, parameters={"trucks_added": 5})
        assert publish_scenario(changed) is changed

    def test_unchanged_republication_of_an_active_scenario_is_allowed(self) -> None:
        code = _unique_code()
        active = _scenario(code=code, status=ScenarioStatus.ACTIVE)
        publish_scenario(active)
        publish_scenario(active)  # identical -- not a conflict
        assert published_scenario(code) is active

    def test_never_superseded_code_has_empty_history(self) -> None:
        assert scenario_history(_unique_code()) == ()
