# Examples — mineproductivity.registry / mineproductivity.plugins

## Purpose

Runnable, minimal, self-contained scripts demonstrating the Registry Framework: the register → discover → lookup cycle, and version-gated plugin activation with failure isolation. Covers both `registry` and `plugins`, per the design specification's shared scope.

## Scope

Example scripts and their direct output. No test assertions live here (see `tests/unit/registry/`, `tests/unit/plugins/`, and `tests/integration/test_registry_plugin_discovery.py` for that); each script is meant to be read and run by a human evaluating the packages.

## Responsibilities

- Show idiomatic usage of the Registry Framework's public API.
- Serve as executable documentation that stays correct because it is actually run.

## Contents

- `01_register_and_discover.py` — the full register → discover → lookup cycle: a domain package's `Registry` and `@register` decorator, duplicate-key rejection, and a real, on-disk plugin module discovered through `EntryPointDiscovery`'s exact code path.
- `02_version_compatibility.py` — a compatible and an incompatible `PluginManifest` activated side by side via `PluginLifecycle`, proving the incompatible plugin's rejection never blocks the compatible one.

## Dependencies

Only `mineproductivity` itself (editable-installed from this repository). No third-party packages, no pre-installed fixture packages required — `01_register_and_discover.py` builds its own temporary, real, on-disk plugin module rather than depending on `tests/fixtures/plugins/` being installed first.

## Running the Examples

```bash
pip install -e .
python examples/registry/01_register_and_discover.py
python examples/registry/02_version_compatibility.py
```

Each script exits `0` and prints its own output; there is nothing to configure.

## Future Work

Add an example demonstrating `resolve_activation_order()` across a small dependency graph of three or more plugins, once a second real consumer of `plugins` (beyond these examples and the test suite) motivates a realistic multi-plugin scenario.

## References

- Reference Implementation Blueprint v1.0
- [`docs/architecture/03_Registry_Framework_Design_Specification.md`](../../docs/architecture/03_Registry_Framework_Design_Specification.md)
- [`src/mineproductivity/registry/README.md`](../../src/mineproductivity/registry/README.md)
- [`src/mineproductivity/plugins/README.md`](../../src/mineproductivity/plugins/README.md)
