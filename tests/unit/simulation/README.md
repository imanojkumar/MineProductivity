# Unit Tests — mineproductivity.simulation

## Purpose

Unit tests for `src/mineproductivity/simulation/`, mirroring its structure one-to-one.

## Scope

Isolated tests for `mineproductivity.simulation` only. Cross-package behavior belongs in `tests/integration/` — the design spec §17 worked example (a 500-trial Monte Carlo experiment seeded from a `digital_twin.TwinSnapshot`) is reproduced end-to-end there as `test_simulation_experiment.py`, and entry-point discovery/isolation is covered generically, once, by `test_registry_plugin_discovery.py` (see `test__registry.py`'s own docstring for the delegation reasoning).

## Responsibilities

- Cover every public symbol exported by `mineproductivity.simulation` (100% statement coverage across all twenty-two modules).
- Prove the six design spec §35 package acceptance proofs with dedicated tests: no-fact-recomputation (`test_public_api.py`, engine-import scan), no-statistics-reimplementation (`test_public_api.py` mechanical scan plus the `test_comparison.py`/`test_sensitivity.py` delegation spies asserting the actual `analytics` primitive invoked), immutability (`test_run.py`), interface-purity (the four interface-module test files, AST scans), no-architectural-drift (`test_public_api.py`, both dependency directions), and reproducibility (`test_montecarlo.py`, `test_executor.py`, and the integration test's identical-outcome-multiset re-run).
- Prove the design spec §10 lifecycle transitions — including `Completed`/`Failed` terminality, `Paused` resumption, and `Failed`-marking on model errors — where the one component that drives transitions lives (`test_executor.py`).

## Contents

One `test_<module>.py` per source module: `test__registry.py`, `test_abstractions.py`, `test_caching.py`, `test_calibration.py`, `test_clock.py`, `test_comparison.py`, `test_discovery.py`, `test_discrete_event.py`, `test_exceptions.py`, `test_executor.py`, `test_experiment.py`, `test_metadata.py`, `test_montecarlo.py`, `test_persistence.py`, `test_public_api.py`, `test_replay.py`, `test_result.py`, `test_run.py`, `test_scenario.py`, `test_sensitivity.py`, `test_state.py`, `test_system_dynamics.py`.

## Dependencies

`mineproductivity` (editable install), `pytest`. Concurrency behavior rides on `ExperimentRunner`'s own `ThreadPoolExecutor` dispatch.

## Future Work

Extend alongside any future concrete `MonteCarloModel`/`DiscreteEventModel`/`SystemDynamicsModel`/`CalibrationModel` plugin or production-grade `SimulationRunRepository` backend — the substitutability suite in `test_persistence.py` is written to pass unmodified against any conforming implementation by changing only its one repository factory.

## References

- [`docs/architecture/09_Simulation_Design_Specification.md`](../../../docs/architecture/09_Simulation_Design_Specification.md) §35
- [`docs/design/09_Simulation_Implementation_Checklist.md`](../../../docs/design/09_Simulation_Implementation_Checklist.md)
