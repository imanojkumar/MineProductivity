# Unit Tests — mineproductivity.plugins

## Purpose

Unit tests for `src/mineproductivity/plugins/`, mirroring its structure one-to-one.

## Scope

Isolated tests for `mineproductivity.plugins` only. Cross-package behavior (full activation against real, pip-installed fixture plugin packages) belongs in `tests/integration/test_registry_plugin_discovery.py`.

## Responsibilities

- Cover every public symbol exported by `mineproductivity.plugins`.
- Guard the package's architectural rules mechanically (`test_public_api.py`): no forbidden cross-layer imports, no dependency beyond `core`/`registry`, `__all__` sorted with no gaps or duplicates, every submodule importable in isolation with no circular imports.
- Prove the isolation rule (design spec §11, §26) as a dedicated test, not incidental coverage: one plugin reaching `Failed` never blocks another's path to `Active`.

## Contents

- `test_manifest.py`, `test_lifecycle.py`, `test_loader.py`, `test_dependency.py`, `test_exceptions.py`, `test_public_api.py`.
- `test_dependency.py` covers linear chains, diamond-shaped dependency graphs, missing dependencies, and cycle detection (self-dependency and longer cycles) for `resolve_activation_order()`.
- `test_lifecycle.py` covers every `PluginState` transition against `_DefaultPluginLifecycle`, using a stub `EntryPointDiscovery` so these tests stay fast and independent of real installed packages.
- **100% line coverage** of `src/mineproductivity/plugins/`.

## Dependencies

`pytest`, `pytest-cov`.

## Future Work

Add tests for each new public symbol in the same pull request that introduces it.

## References

- Reference Implementation Blueprint v1.0
- [`docs/architecture/03_Registry_Framework_Design_Specification.md`](../../../docs/architecture/03_Registry_Framework_Design_Specification.md)
