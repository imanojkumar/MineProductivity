"""``Scenario``/``ScenarioStatus``: scenarios as versioned, governed
artifacts (design spec §9) -- the scenario-management responsibility.

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``core.BaseValueObject`` and the ``MappingProxyType``-freezing
convention are reused verbatim; ``digital_twin.TwinSnapshot`` is reused
directly as ``initial_state`` (spec 08 §13) rather than defining a
second "starting condition" concept -- "simulate forward from last
Tuesday's actual conditions" and "simulate forward from a purely
hypothetical configuration" are the same ``Scenario`` shape.
``events.AsOf`` is reused directly as the point-in-time/scenario
reference (its ``scenario`` field is exactly the hook
``decision.WhatIfEngine`` and ``digital_twin.TwinSimulationModel`` were
each designed around). The publish/supersede governance mechanism
mirrors ``decision.policy.publish_policy`` exactly (spec 07 §12's own
reasoning for why ``registry.Registry.register()``'s add-only contract
cannot express update-permitting, version-gated republication) --
``publish_scenario`` is deliberately **not** re-exported from the
package's top-level ``__all__``, mirroring ``publish_policy``'s own
disclosed non-export: design spec §7's public API list names
``Scenario``/``ScenarioStatus`` only.
"""

from __future__ import annotations

import dataclasses
import threading
from collections.abc import Mapping
from datetime import timedelta
from enum import Enum
from types import MappingProxyType
from typing import Any

from mineproductivity.core import BaseValueObject
from mineproductivity.digital_twin import TwinSnapshot
from mineproductivity.events import AsOf

from mineproductivity.simulation.exceptions import (
    ScenarioConflictError,
    SimulationValidationError,
)

__all__ = ["Scenario", "ScenarioStatus"]

_scenarios: dict[str, Scenario] = {}
_scenario_history: dict[str, list[Scenario]] = {}
_lock = threading.Lock()


class ScenarioStatus(Enum):
    """The ``Scenario`` lifecycle -- mirrors ``decision.DecisionStatus``
    (spec 07 §12) exactly, applied here to governed
    simulation-configuration artifacts rather than to business
    policies."""

    PROPOSED = "proposed"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    RETIRED = "retired"


@dataclasses.dataclass(frozen=True, slots=True)
class Scenario(BaseValueObject):
    """A named, versioned simulation configuration -- the
    business-policy-grade governed artifact this package owns,
    analogous to ``decision.Policy`` (spec 07 §12) one layer down.

    An ``Active`` ``Scenario`` is a public contract: it is never edited
    in place. A changed scenario is published as a new version; the
    prior version transitions to ``Superseded``, never silently
    repointed (design spec §9, §25, §34's recorded anti-pattern).

    Examples
    --------
    >>> scenario = Scenario(
    ...     code="FLEET.NightShiftSurge",
    ...     model_code="MONTECARLO.HaulCycleVariability",
    ...     parameters={"trucks_added": 3},
    ...     time_horizon=timedelta(hours=12),
    ... )
    >>> scenario.status
    <ScenarioStatus.PROPOSED: 'proposed'>
    >>> scenario.version
    '1.0.0'
    >>> scenario.initial_state is None
    True
    """

    code: str
    version: str = dataclasses.field(default="1.0.0", kw_only=True)
    status: ScenarioStatus = dataclasses.field(
        default_factory=lambda: ScenarioStatus.PROPOSED, kw_only=True
    )
    model_code: str = dataclasses.field(kw_only=True)
    parameters: Mapping[str, Any] = dataclasses.field(default_factory=dict, kw_only=True)
    time_horizon: timedelta = dataclasses.field(kw_only=True)
    initial_state: TwinSnapshot | None = dataclasses.field(default=None, kw_only=True)
    as_of: AsOf | None = dataclasses.field(default=None, kw_only=True)

    def _normalize(self) -> None:
        super(Scenario, self)._normalize()
        object.__setattr__(self, "parameters", MappingProxyType(dict(self.parameters)))

    def validate(self) -> None:
        if not self.code.strip():
            raise SimulationValidationError("Scenario.code must not be empty")
        if not self.model_code.strip():
            raise SimulationValidationError("Scenario.model_code must not be empty")


def publish_scenario(scenario: Scenario) -> Scenario:
    """Publish ``scenario`` into the process-wide scenario store, keyed
    by ``scenario.code`` -- the governance action design spec §9/§25
    prescribe, mirroring ``decision.policy.publish_policy`` exactly.

    Raises
    ------
    ScenarioConflictError
        If an ``Active`` scenario is already published under
        ``scenario.code`` and ``scenario`` changes its ``parameters``/
        ``initial_state`` without a version bump -- raised at
        publication time, never deferred (§25).
    """
    with _lock:
        existing = _scenarios.get(scenario.code)
        if existing is not None and existing.status is ScenarioStatus.ACTIVE:
            changed = (
                existing.parameters != scenario.parameters
                or existing.initial_state != scenario.initial_state
            )
            if changed and scenario.version == existing.version:
                raise ScenarioConflictError(
                    f"Scenario {scenario.code!r} is Active at version {existing.version!r}; "
                    f"changing its parameters/initial conditions requires a new version, "
                    f"not re-publication"
                )
            if changed and scenario.status is ScenarioStatus.ACTIVE:
                superseded = existing.replace(status=ScenarioStatus.SUPERSEDED)
                _scenario_history.setdefault(scenario.code, []).append(superseded)
        _scenarios[scenario.code] = scenario
        return scenario


def published_scenario(code: str) -> Scenario | None:
    """Non-raising lookup of the currently-published ``Scenario`` for
    ``code``, or ``None`` if none has been published."""
    with _lock:
        return _scenarios.get(code)


def scenario_history(code: str) -> tuple[Scenario, ...]:
    """Every prior version of ``code`` that :func:`publish_scenario`
    has transitioned to ``Superseded``, oldest first."""
    with _lock:
        return tuple(_scenario_history.get(code, ()))
