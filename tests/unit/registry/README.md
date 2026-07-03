# Unit Tests — mineproductivity.registry

## Purpose

Unit tests for `src/mineproductivity/registry/`, mirroring its structure one-to-one.

## Scope

Isolated tests for `mineproductivity.registry` only. Cross-package behavior (discovery/isolation proven against real, pip-installed fixture plugin packages) belongs in `tests/integration/test_registry_plugin_discovery.py`.

## Responsibilities

- Cover every public symbol exported by `mineproductivity.registry`.
- Guard the package's architectural rules mechanically (`test_public_api.py`): no forbidden cross-layer imports, no dependency beyond `core`, `__all__` sorted with no gaps or duplicates, every submodule importable in isolation with no circular imports.

## Contents

- `test_registry.py`, `test_entry_point.py`, `test_version_compat.py`, `test_caching.py`, `test_decorators.py`, `test_exceptions.py`, `test_public_api.py`.
- Entry-point discovery is unit-tested by monkeypatching `importlib.metadata.entry_points()` with real `EntryPoint` objects pointing at synthetic in-process/temp-file modules — fast and isolated, no real package installation required at this level (the real-package proof lives in `tests/integration/`).
- `test_caching.py` includes a thread-based stress test proving `DiscoveryCache.get_or_discover()` triggers exactly one discovery pass under concurrent calls for the same spec.
- **100% line coverage** of `src/mineproductivity/registry/`.

## Dependencies

`pytest`, `pytest-cov`.

## Future Work

Add tests for each new public symbol in the same pull request that introduces it.

## References

- Reference Implementation Blueprint v1.0
- [`docs/architecture/03_Registry_Framework_Design_Specification.md`](../../../docs/architecture/03_Registry_Framework_Design_Specification.md)
