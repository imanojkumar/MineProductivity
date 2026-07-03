# Unit Tests — mineproductivity.connectors

## Purpose

Unit tests for `src/mineproductivity/connectors/`, mirroring its structure one-to-one.

## Scope

Isolated tests for `mineproductivity.connectors` only. Cross-package behavior (the full CSV → connector → Event Framework pipeline) belongs in `tests/integration/test_connector_pipeline.py`.

## Responsibilities

- Cover every public symbol exported by `mineproductivity.connectors`.
- Guard the package's architectural rules mechanically (`test_public_api.py`): no forbidden cross-layer imports, no dependency beyond `core`/`ontology`/`events`/`registry`, `__all__` sorted with no gaps or duplicates, every submodule importable in isolation with no circular imports.

## Contents

- `test_exceptions.py`, `test_health.py`, `test_auth.py`, `test_retry.py`, `test_normalization.py`, `test_base.py`, `test_connector_registry.py`, `test_contract_tests.py`, `test_public_api.py` — the cross-cutting root modules.
- `file/`, `network/`, `streaming/`, `oem/` — one `test_*.py` per source module, mirroring `src/mineproductivity/connectors/` exactly.
- `network/conftest.py` — a `run_server` fixture that spins up a real, local `http.server.HTTPServer` per test (no mocking library) for `RestConnector`/`GraphQLConnector` tests.
- `oem/test_oem_shapes.py` — all five vendor shapes are structurally identical, so they are covered together via `pytest.mark.parametrize` rather than five near-duplicate files.
- **100% line coverage** of `src/mineproductivity/connectors/`.

## Dependencies

`pytest`, `pytest-cov`, `openpyxl` (the `connectors` extra, for `ExcelConnector` tests).

## Future Work

Add tests for each new public symbol in the same pull request that introduces it.

## References

- Reference Implementation Blueprint v1.0
- [`docs/architecture/04_Connector_Framework_Design_Specification.md`](../../../docs/architecture/04_Connector_Framework_Design_Specification.md)
