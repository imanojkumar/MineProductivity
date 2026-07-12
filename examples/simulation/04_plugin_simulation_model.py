"""A third-party-style ``SimulationModel`` category subclass registered
via entry points, mirroring ``examples/registry/01_register_and_discover.py``'s
pattern -- the exact wiring design spec 09 sec. 31 prescribes:

    [project.entry-points."mineproductivity.simulation"]
    sitepack = "mineproductivity_sitepack.simulation"

Run: python examples/simulation/04_plugin_simulation_model.py
"""

from __future__ import annotations

import importlib.metadata
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from mineproductivity.core import InMemoryRepository
from mineproductivity.events.store import _InMemoryEventStore
from mineproductivity.registry import EntryPointDiscovery, EntryPointSpec
from mineproductivity.simulation import (
    REGISTRY,
    RunStatus,
    Scenario,
    SimulationClock,
    SimulationContext,
    SimulationExecutor,
    SimulationMetadata,
    SimulationRun,
    SimulationState,
    TimeProgressionMode,
)

NOW = datetime(2026, 7, 8, 6, 0, tzinfo=timezone.utc)

_PLUGIN_SOURCE = '''\
"""A site pack's own Monte Carlo model -- importing this module
registers it, exactly as a pip-installed plugin's entry-point scan
would."""

import random

from mineproductivity.simulation import (
    MonteCarloModel,
    Scenario,
    SimulationCategory,
    SimulationContext,
    SimulationMetadata,
    SimulationResult,
    SimulationState,
    register,
)


@register
class SitePackDrillPenetrationModel(MonteCarloModel):
    """A site pack's drill-penetration-rate variability model --
    seed-deterministic trials over the scenario's rock-hardness
    parameter."""

    meta = SimulationMetadata(
        code="MONTECARLO.SitePackDrillPenetration",
        category=SimulationCategory.MONTE_CARLO,
        description=(
            "A site pack's drill-penetration-rate variability model -- "
            "seed-deterministic trials over the scenario's rock-hardness parameter."
        ),
    )

    def _trial(self, scenario: Scenario, *, context: SimulationContext, random_seed: int) -> SimulationResult:
        hardness = float(scenario.parameters.get("rock_hardness", 1.0))
        rate = (42.0 / hardness) * random.Random(random_seed).uniform(0.9, 1.1)
        from datetime import datetime, timezone
        return SimulationResult(
            final_state=SimulationState(
                attributes={"penetration_m_per_h": rate},
                simulated_time=datetime(2026, 7, 8, tzinfo=timezone.utc),
            )
        )
'''


def main() -> None:
    print("--- 1. simulation ships zero built-in models (interface-only) ---")
    before = sorted(code for code in REGISTRY if "SitePack" in code)
    print(f"site-pack models before discovery: {before}")

    print()
    print("--- 2. A site pack declares its model via a pyproject.toml entry-point ---")
    with tempfile.TemporaryDirectory() as tmp_dir:
        plugin_path = Path(tmp_dir) / "_example_sitepack_simulation.py"
        plugin_path.write_text(_PLUGIN_SOURCE, encoding="utf-8")
        sys.path.insert(0, tmp_dir)
        try:
            real_entry_points = importlib.metadata.entry_points

            def _fake_entry_points(*, group: str):  # type: ignore[no-untyped-def]
                if group == "mineproductivity.simulation":
                    return (
                        importlib.metadata.EntryPoint(
                            name="sitepack", value="_example_sitepack_simulation", group=group
                        ),
                    )
                return real_entry_points(group=group)

            importlib.metadata.entry_points = _fake_entry_points  # type: ignore[assignment]
            try:
                discovery = EntryPointDiscovery()
                spec = EntryPointSpec(
                    group="mineproductivity.simulation", target_registry="simulation"
                )
                discover_result = discovery.discover(spec)
            finally:
                importlib.metadata.entry_points = real_entry_points
        finally:
            sys.path.remove(tmp_dir)
            sys.modules.pop("_example_sitepack_simulation", None)

    print(
        f"discover() -> is_ok: {discover_result.is_ok},"
        f" loaded entry-points: {discover_result.value}"
    )
    metadata = REGISTRY.metadata_for("MONTECARLO.SitePackDrillPenetration").unwrap()
    assert isinstance(metadata, SimulationMetadata)
    print(f"registered: {metadata.code} ({metadata.category.value})")

    print()
    print("--- 3. The discovered model executes like any built-in would ---")
    repository: InMemoryRepository[SimulationRun, str] = InMemoryRepository()
    repository.add(
        SimulationRun(
            id="RUN-DRILL-1",
            scenario_code="DRILL.HardRockStudy",
            state=SimulationState(attributes={"provisioned": True}, simulated_time=NOW),
        )
    )
    executor = SimulationExecutor(
        repository=repository, clock=SimulationClock(mode=TimeProgressionMode.TRIAL_BASED)
    )
    scenario = Scenario(
        code="DRILL.HardRockStudy",
        model_code="MONTECARLO.SitePackDrillPenetration",
        parameters={"rock_hardness": 1.4},
        time_horizon=timedelta(hours=8),
    )
    result = executor.execute(
        "RUN-DRILL-1",
        scenario,
        context=SimulationContext(event_store=_InMemoryEventStore()),
        random_seed=7,
    )
    assert result.final_state is not None
    print(f"penetration: {result.final_state.attributes['penetration_m_per_h']:.2f} m/h")
    print(f"run status: {repository.get('RUN-DRILL-1').status is RunStatus.COMPLETED}")


if __name__ == "__main__":
    main()
