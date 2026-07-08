# Unit Tests — mineproductivity.digital_twin

## Purpose

Unit tests for `src/mineproductivity/digital_twin/`, mirroring its structure one-to-one.

## Scope

Isolated tests for `mineproductivity.digital_twin` only. Cross-package behavior belongs in `tests/integration/` (entry-point discovery/isolation against real installed fixture plugins is covered generically there, once, by `test_registry_plugin_discovery.py` — see `test__registry.py`'s own docstring for the delegation reasoning).

## Responsibilities

- Cover every public symbol exported by `mineproductivity.digital_twin` (100% statement coverage across all sixteen modules).
- Prove the seven design spec §32 package acceptance proofs with dedicated tests: no-fact-recomputation (`test_public_api.py`, engine-import scan), immutability (`test_abstractions.py`), interface-purity (`test_simulation.py`, AST scan), no-architectural-drift (`test_public_api.py`, both dependency directions), replay-consistency (`test_synchronization.py`), scope-immutability (`test_abstractions.py`), and repository-substitutability (`test_persistence.py`, written against the `core.BaseRepository[Twin, str]` contract alone).
- Prove the design spec §10 lifecycle transitions — including `Retired`'s terminality and `Degraded`-on-repeated-failures/recovery — where the one component that drives transitions lives (`test_synchronization.py`).

## Contents

One `test_<module>.py` per source module: `test__registry.py`, `test_abstractions.py`, `test_caching.py`, `test_categories.py`, `test_discovery.py`, `test_exceptions.py`, `test_lifecycle.py`, `test_metadata.py`, `test_persistence.py`, `test_public_api.py`, `test_result.py`, `test_simulation.py`, `test_snapshot.py`, `test_state.py`, `test_synchronization.py`, `test_telemetry.py`.

## Dependencies

`mineproductivity` (editable install), `pytest`. Concurrency tests use only the standard library's `threading`.

## Future Work

Extend alongside any future concrete `TwinSimulationModel` plugin or production-grade `TwinRepository` backend — the substitutability suite in `test_persistence.py` is written to pass unmodified against any conforming implementation by changing only its one repository factory.

## References

- [`docs/architecture/08_Digital_Twin_Design_Specification.md`](../../../docs/architecture/08_Digital_Twin_Design_Specification.md) §32
- [`docs/design/08_Digital_Twin_Implementation_Checklist.md`](../../../docs/design/08_Digital_Twin_Implementation_Checklist.md)
