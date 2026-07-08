"""Tests for mineproductivity.digital_twin.abstractions."""

from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta, timezone
from typing import Any, ClassVar

import pytest

from mineproductivity.core import BaseEntity
from mineproductivity.decision import DecisionResult
from mineproductivity.digital_twin.abstractions import Twin, TwinContext
from mineproductivity.digital_twin.lifecycle import TwinStatus
from mineproductivity.digital_twin.metadata import TwinCategory, TwinMetadata
from mineproductivity.digital_twin.state import TwinState
from mineproductivity.events import AsOf
from mineproductivity.kpis import KPIResult

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


class _CounterTwin(Twin):
    """Counts events folded into it -- deterministic on the cumulative
    event count, so cold-start and incremental folds converge exactly."""

    meta: ClassVar[TwinMetadata] = TwinMetadata(
        code="TEST.Counter",
        category=TwinCategory.EQUIPMENT,
        description="Counts events folded into it.",
    )

    def _apply(self, events: Any, *, context: TwinContext) -> TwinState:
        if not events:
            return self.state
        seen = int(self.state.attributes.get("events_seen", 0)) + len(events)
        return TwinState(
            attributes={"events_seen": seen},
            captured_at=_EPOCH + timedelta(seconds=seen),
        )


def _state(**attributes: Any) -> TwinState:
    return TwinState(attributes=attributes or {"events_seen": 0}, captured_at=_EPOCH)


def _twin(twin_id: str = "EQ-1", **kwargs: Any) -> _CounterTwin:
    kwargs.setdefault("scope", {"equipment_id": twin_id})
    kwargs.setdefault("state", _state())
    return _CounterTwin(id=twin_id, **kwargs)


class _FakeStore:
    """Duck-typed ``EventStore`` stand-in, mirroring
    ``analytics.AnalyticsContext``'s own doctest precedent."""


class TestTwinIsABaseEntity:
    def test_subclasses_base_entity(self) -> None:
        assert issubclass(Twin, BaseEntity)

    def test_bare_abstract_twin_cannot_be_instantiated(self) -> None:
        with pytest.raises(TypeError):
            Twin(id="X", scope={}, state=_state())  # type: ignore[abstract]

    def test_same_id_different_state_compare_equal(self) -> None:
        first = _twin(twin_id="EQ-1")
        second = _twin(twin_id="EQ-1", state=_state(events_seen=99))
        assert first == second
        assert hash(first) == hash(second)

    def test_different_ids_never_compare_equal(self) -> None:
        assert _twin(twin_id="EQ-1") != _twin(twin_id="EQ-2")

    def test_eq_and_hash_are_inherited_from_base_entity_unchanged(self) -> None:
        """Design spec §8: no override anywhere in this package."""
        assert "__eq__" not in Twin.__dict__
        assert "__hash__" not in Twin.__dict__
        assert Twin.__eq__ is BaseEntity.__eq__
        assert Twin.__hash__ is BaseEntity.__hash__


class TestTwinImmutability:
    def test_state_cannot_be_reassigned(self) -> None:
        twin = _twin()
        with pytest.raises(dataclasses.FrozenInstanceError):
            twin.state = _state(events_seen=5)  # type: ignore[misc]

    def test_status_cannot_be_reassigned(self) -> None:
        twin = _twin()
        with pytest.raises(dataclasses.FrozenInstanceError):
            twin.status = TwinStatus.RETIRED  # type: ignore[misc]

    def test_scope_cannot_be_reassigned(self) -> None:
        """Design spec §9, §32's scope-immutability proof: scope is set
        once at provisioning time, never re-assigned in place."""
        twin = _twin()
        with pytest.raises(dataclasses.FrozenInstanceError):
            twin.scope = {"equipment_id": "OTHER"}  # type: ignore[misc]

    def test_scope_mapping_itself_is_read_only(self) -> None:
        twin = _twin()
        with pytest.raises(TypeError):
            twin.scope["new_key"] = "x"  # type: ignore[index]

    def test_scope_is_copied_from_the_caller_supplied_mapping(self) -> None:
        supplied = {"equipment_id": "EQ-1"}
        twin = _CounterTwin(id="EQ-1", scope=supplied, state=_state())
        supplied["equipment_id"] = "TAMPERED"
        assert twin.scope["equipment_id"] == "EQ-1"


class TestWithState:
    def test_returns_a_new_instance(self) -> None:
        twin = _twin()
        replacement = twin.with_state(_state(events_seen=1))
        assert replacement is not twin
        assert replacement == twin  # same identity (§8)

    def test_original_instance_is_untouched(self) -> None:
        twin = _twin()
        original_state = twin.state
        twin.with_state(_state(events_seen=1), status=TwinStatus.SYNCHRONIZED)
        assert twin.state is original_state
        assert twin.status is TwinStatus.PROVISIONED

    def test_preserves_id_and_scope(self) -> None:
        twin = _twin()
        replacement = twin.with_state(_state(events_seen=1))
        assert replacement.id == twin.id
        assert dict(replacement.scope) == dict(twin.scope)

    def test_status_defaults_to_current(self) -> None:
        twin = _twin(status=TwinStatus.SYNCHRONIZED)
        assert twin.with_state(_state(events_seen=1)).status is TwinStatus.SYNCHRONIZED

    def test_status_can_be_replaced_alongside_state(self) -> None:
        twin = _twin()
        replacement = twin.with_state(_state(events_seen=1), status=TwinStatus.SYNCHRONIZED)
        assert replacement.status is TwinStatus.SYNCHRONIZED


class TestApplyContract:
    def test_empty_batch_returns_state_unchanged(self) -> None:
        """Design spec §8's 'qualify, don't coerce' rule."""
        twin = _twin()
        context = TwinContext(event_store=_FakeStore())
        assert twin._apply((), context=context) is twin.state

    def test_default_status_is_provisioned(self) -> None:
        assert _twin().status is TwinStatus.PROVISIONED


class TestTwinContext:
    def test_evidence_defaults_to_empty_tuples(self) -> None:
        context = TwinContext(event_store=_FakeStore())
        assert context.kpi_results == ()
        assert context.analytics_results == ()
        assert context.decision_results == ()
        assert context.as_of is None

    def test_evidence_sequences_are_coerced_to_tuples(self) -> None:
        context = TwinContext(
            event_store=_FakeStore(),
            kpi_results=[KPIResult(code="UTIL.OEE", value=0.83, unit="")],
            decision_results=[DecisionResult(model_code="STRATEGY.Threshold")],
        )
        assert isinstance(context.kpi_results, tuple)
        assert isinstance(context.decision_results, tuple)
        assert context.kpi_results[0].code == "UTIL.OEE"

    def test_as_of_is_carried(self) -> None:
        as_of = AsOf(utc=_EPOCH)
        context = TwinContext(event_store=_FakeStore(), as_of=as_of)
        assert context.as_of is as_of

    def test_repr_names_the_collaborators(self) -> None:
        text = repr(TwinContext(event_store=_FakeStore()))
        assert "TwinContext" in text
        assert "kpi_results" in text
