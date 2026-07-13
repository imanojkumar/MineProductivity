# Examples - mineproductivity.simulation

## Purpose

Runnable, minimal, self-contained scripts demonstrating the Simulation package: a snapshot-seeded Monte Carlo experiment, scenario comparison, a sensitivity sweep, and third-party model plugins. Every concrete model in these scripts is example-local - the package itself ships zero concrete simulation models by design (interface-only methodologies, design spec §13–§16, ADR-0009).

## Scope

Example scripts and their direct output. No test assertions live here (see `tests/unit/simulation/` and `tests/integration/test_simulation_experiment.py` for that); each script is meant to be read and run by a human evaluating the package.

## Responsibilities

- Show idiomatic usage of the Simulation public API.
- Serve as executable documentation that stays correct because it is actually run.
- Demonstrate the §3.2 discipline end-to-end: scenarios seed from `digital_twin.TwinSnapshot`s, and every statistical judgment is `analytics`' - `simulation` orchestrates and never re-derives either.

## Contents

- `01_monte_carlo_experiment.py` - the design spec §17 worked example, end-to-end: a 500-trial Monte Carlo experiment seeded from a real `TwinSnapshot`, concurrently dispatched with per-trial seeds, summarized via `ScenarioComparator` → `analytics.describe`.
- `02_scenario_comparison.py` - two governed scenarios (baseline vs. surge), 200 trials each, one analytics-backed `StatisticalSummary` per scenario; the "which is better" judgment stays with the caller (a decision-layer question).
- `03_sensitivity_sweep.py` - `SensitivityAnalyzer.sweep()` over a single parameter (one run per value, ordered to match), with `distribution`/`confidence_interval` delegation for the outcome treatment; proves the base `Scenario` is never edited in place.
- `04_plugin_simulation_model.py` - a third-party-style `MonteCarloModel` registered via entry points (`EntryPointSpec(group="mineproductivity.simulation", target_registry="simulation")`, design spec §31), mirroring `examples/registry/01_register_and_discover.py`'s real-discovery pattern.

## Dependencies

`mineproductivity[analytics]` (for `analytics`' statistical primitives). No network access; every event and snapshot is constructed in-script.

## Running the Examples

```bash
pip install -e ".[analytics]"
python examples/simulation/01_monte_carlo_experiment.py
python examples/simulation/02_scenario_comparison.py
python examples/simulation/03_sensitivity_sweep.py
python examples/simulation/04_plugin_simulation_model.py
```

Each script exits `0` and prints its own output; there is nothing to configure.

## Future Work

Add a discrete-event and a system-dynamics walkthrough once first-party or third-party plugins implementing those interface-only extension points exist (deliberately never shipped inside `simulation` itself, design spec §13–§16).

## References

- [`docs/architecture/09_Simulation_Design_Specification.md`](../../docs/architecture/09_Simulation_Design_Specification.md) §9, §13, §17, §19–§20, §31
- [`src/mineproductivity/simulation/README.md`](../../src/mineproductivity/simulation/README.md)
- [`docs/adr/ADR-0009-Simulation.md`](../../docs/adr/ADR-0009-Simulation.md)
