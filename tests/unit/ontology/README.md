# Unit Tests — mineproductivity.ontology

## Purpose

Unit tests for `src/mineproductivity/ontology/`, mirroring its structure one-to-one.

## Scope

Isolated tests for `mineproductivity.ontology` only. Cross-package behavior (e.g. the full mine model validated end-to-end and cross-checked against `events`) belongs in `tests/integration/test_ontology_model.py`.

## Responsibilities

- Cover every public symbol exported by `mineproductivity.ontology`.
- Guard the package's architectural rules mechanically (`test_public_api.py`): no forbidden cross-layer imports, no dependency beyond `core`, `__all__` sorted with no gaps or duplicates, every submodule importable in isolation with no circular imports.

## Contents

- `test_exceptions.py`, `test_entity_type.py`, `test_relationship.py`, `test_graph_projection.py`, `test_validation.py`, `test_public_api.py` — the cross-cutting root modules.
- `equipment/`, `material/`, `location/`, `organization/`, `production/`, `maintenance/`, `cost/`, `quality/`, `safety/`, `environmental/`, `reference/` — one `test_*.py` per source module, mirroring `src/mineproductivity/ontology/` exactly.
- **207 tests, 100% line coverage** of `src/mineproductivity/ontology/`.

## Dependencies

`pytest`, `pytest-cov`.

## Future Work

Add tests for each new sub-ontology family or leaf type in the same pull request that introduces it.

## References

- Reference Implementation Blueprint v1.0
- [`docs/architecture/02_Ontology_Framework_Design_Specification.md`](../../../docs/architecture/02_Ontology_Framework_Design_Specification.md)
