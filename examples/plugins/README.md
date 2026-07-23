# Examples - mineproductivity.plugins

## Purpose

Runnable, minimal, self-contained scripts demonstrating the plugin
**lifecycle** layer that sits on top of `mineproductivity.registry`: a
plugin's declared identity (`PluginManifest`), its state machine
(`PluginState`), version gating, dependency-aware activation ordering, and
graceful, isolated failure.

## Scope

Example scripts and their direct output. No test assertions live here (see
`tests/unit/plugins/` and `tests/integration/test_registry_plugin_discovery.py`
for that); each script is meant to be read and run by a human.

## Contents

- `01_manifest_and_lifecycle.py` - a `PluginManifest` driven through
  `Discovered -> Validated -> Active` via the reference `PluginLifecycle`,
  version gating, isolated failure, and deactivation.
- `02_activation_order.py` - `resolve_activation_order` topologically sorting
  manifests by their declared `PluginDependency`, and rejecting a missing
  dependency and a dependency cycle.

## Dependencies

Only `mineproductivity` itself (editable-installed from this repository). No
third-party packages.

## Running

```bash
python examples/plugins/01_manifest_and_lifecycle.py
python examples/plugins/02_activation_order.py
```

Each script exits `0` and prints its own narrated output.
