"""Shared fixtures for ``mineproductivity.analytics`` unit tests."""

from __future__ import annotations

import ast
import inspect
import textwrap
from collections.abc import Callable
from datetime import datetime, timezone
from types import ModuleType
from typing import Any

import pytest

from mineproductivity.events.canonical import CycleEvent
from mineproductivity.events.envelope import EventEnvelope, EventMetadata
from mineproductivity.events.identifier import EventID
from mineproductivity.events.store import _InMemoryEventStore
from mineproductivity.events.versioning import EventVersion
from mineproductivity.kpis import REGISTRY, KPIEngine, ResultCache
from mineproductivity.kpis.backends import PandasBackend

NOW = datetime(2026, 6, 25, 6, 0, tzinfo=timezone.utc)


@pytest.fixture
def event_store() -> _InMemoryEventStore:
    return _InMemoryEventStore()


@pytest.fixture
def cycle_event_factory() -> Callable[..., CycleEvent]:
    def factory(
        *, equipment_id: str = "HT-214", shift_id: str = "A-2026-06-25", payload_t: float = 220.0
    ) -> CycleEvent:
        return CycleEvent(
            equipment_id=equipment_id,
            shift_id=shift_id,
            queue_min=1.5,
            spot_min=0.5,
            load_min=2.5,
            haul_min=8.0,
            dump_min=1.0,
            return_min=6.0,
            payload_t=payload_t,
        )

    return factory


@pytest.fixture
def cycle_envelope_factory(
    cycle_event_factory: Callable[..., CycleEvent],
) -> Callable[..., EventEnvelope[CycleEvent]]:
    def factory(
        *,
        payload: CycleEvent | None = None,
        event_time: datetime = NOW,
    ) -> EventEnvelope[CycleEvent]:
        return EventEnvelope(
            event_id=EventID.generate(),
            version=EventVersion(),
            payload=payload or cycle_event_factory(),
            event_time_utc=event_time,
            processing_time_utc=event_time,
            ingestion_time_utc=event_time,
            metadata=EventMetadata(name="test-event", source_system="test"),
        )

    return factory


@pytest.fixture
def engine(event_store: _InMemoryEventStore) -> KPIEngine:
    return KPIEngine(
        store=event_store, registry=REGISTRY, backend=PandasBackend(), cache=ResultCache()
    )


def assert_stub_method_body(method: Callable[..., Any]) -> None:
    """Assert ``method``'s body is a docstring only -- no statements, no
    branching, no return. Shared by the interface-only modules'
    (``forecasting.py``, ``anomaly.py``, ``outliers.py``) test suites to
    mechanically prove "no algorithmic behavior exists beyond
    orchestration" (design spec §35) without each duplicating the same
    AST-parsing assertion."""
    source = inspect.getsource(method)
    (function_def,) = ast.parse(textwrap.dedent(source)).body
    assert isinstance(function_def, ast.FunctionDef)
    assert len(function_def.body) == 1
    assert isinstance(function_def.body[0], ast.Expr)
    assert isinstance(function_def.body[0].value, ast.Constant)
    assert isinstance(function_def.body[0].value.value, str)


def assert_no_import_from(module: ModuleType, *forbidden_submodules: str) -> None:
    """Assert ``module`` (a ``mineproductivity.analytics`` submodule)
    does not import from any of ``forbidden_submodules`` (sibling
    ``analytics`` submodule names, e.g. ``"statistics"``, ``"rolling"``).
    Shared by the execution-mode modules' (``batch.py``,
    ``streaming.py``, ``incremental.py``) test suites to mechanically
    prove they coordinate existing components rather than duplicating
    logic that belongs in one specific, single-responsibility module."""
    tree = ast.parse(inspect.getsource(module))
    imported_modules = {
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module
    }
    for forbidden in forbidden_submodules:
        full_name = f"mineproductivity.analytics.{forbidden}"
        assert full_name not in imported_modules, f"{module.__name__} imports from {full_name}"
