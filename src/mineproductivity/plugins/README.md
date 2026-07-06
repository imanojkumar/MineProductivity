# mineproductivity.plugins

## Purpose

`mineproductivity.plugins` is the plugin lifecycle layer built on [`registry`](../registry/README.md): manifests, version-gated activation, inter-plugin dependency ordering, and graceful failure isolation — the concerns a consumer wanting only "give me a typed lookup table" should not have to pull in (that's `registry` alone).

This package implements the [Registry Framework Design Specification](../../../docs/architecture/03_Registry_Framework_Design_Specification.md) exactly (the specification covers `registry` and `plugins` together). Where this README and that specification disagree, the specification governs.

## Scope

**What belongs here:**

- `PluginManifest`/`PluginDependency` — the declared identity of one installed plugin package.
- `PluginState`/`PluginLifecycle` — the Discovered → Validated → (Failed | Active) → Deactivated state machine and its ABC.
- `PluginLoader` — loads every entry-point group a manifest declares, via `registry.EntryPointDiscovery`.
- `resolve_activation_order()` — topological-sort dependency resolution for a batch of manifests.

**What must never belong here:**

- Specific plugin implementations — this package defines the mechanism, not the plugins.
- Raw entry-point scanning (`importlib.metadata` calls) — that is `registry.EntryPointDiscovery`'s job; `plugins` only orchestrates it.
- Any domain package import (`ontology`, `events`, `kpis`, `connectors`, `analytics`, `optimization`, `simulation`, `decision`, `digital_twin`, `agents`).

## Architecture

```
core  →  registry  →  plugins
core  →  plugins
```

`plugins` is a **cross-cutting** package, like `registry`: may be depended upon by any layer, never depends on a domain layer.

`PluginLifecycle` (an ABC) orchestrates a `PluginManifest` through `PluginState`, delegating the actual entry-point scanning to `registry.EntryPointDiscovery` (via `PluginLoader`) and adding what raw registration alone cannot provide: inter-plugin dependency resolution, activation ordering, and graceful failure isolation. `_DefaultPluginLifecycle` (in `lifecycle.py`, not part of the frozen public API — a reference implementation, like `events._InMemoryEventStore`) provides an in-process, dict-backed implementation suitable for tests, examples, and single-process deployments; a custom `PluginLifecycle` implementation remains a supported extension point (design spec §16).

**Isolation rule (normative):** a single plugin transitioning to `Failed` MUST NOT prevent any other plugin from reaching `Active`. This directly protects "the core never changes to accommodate" a plugin (Cookbook Part I, Ch. 9) — the inverse must also hold: one broken plugin never breaks the platform's ability to serve every other plugin.

See the [design specification's §11](../../../docs/architecture/03_Registry_Framework_Design_Specification.md) for the full lifecycle state diagram and §13.2's failure-isolation sequence diagram.

## Package Structure

```
plugins/
├── __init__.py           # public API surface (__all__)
├── manifest.py              # PluginManifest, PluginDependency
├── lifecycle.py                # PluginState, PluginLifecycle, _DefaultPluginLifecycle
├── loader.py                     # PluginLoader
├── dependency.py                   # resolve_activation_order()
├── exceptions.py                     # the plugins exception hierarchy
└── README.md                           # this file
```

## Dependency Rules

```
core  →  registry  →  plugins
```

- **`plugins` depends on:** `core` and `registry`. No other package.
- **`plugins` is depended on by:** the future `cli` package (a `mineprod plugins` surface); any package that needs manifest-driven activation rather than raw `registry` lookups.
- **Forbidden:** `plugins` must never import `ontology`, `events`, `connectors`, `kpis`, `analytics`, `optimization`, `simulation`, `decision`, `digital_twin`, `agents`, or `visualization`. This is mechanically checked by `tests/unit/plugins/test_public_api.py::TestNoForbiddenDependencies`.

## Public API

```python
from mineproductivity.plugins import (
    PluginManifest, PluginDependency,
    PluginLifecycle, PluginState, PluginLoader,
    resolve_activation_order,
    PluginActivationError, PluginDependencyError,
)
```

`_DefaultPluginLifecycle` (in `mineproductivity.plugins.lifecycle`) is a reference implementation for tests and examples, not part of the public, versioned API — a custom `PluginLifecycle` subclass is the supported extension point for production deployments with different orchestration needs (a UI-driven activation flow, a persistent activation ledger, ...).

## Extension Guide

**Activating a batch of plugins in dependency order:**

```python
from mineproductivity.plugins import resolve_activation_order
from mineproductivity.plugins.lifecycle import _DefaultPluginLifecycle

lifecycle = _DefaultPluginLifecycle(core_version=mineproductivity.__version__)
ordered = resolve_activation_order(discovered_manifests)
if ordered.is_err:
    log.error("plugin dependency graph is invalid: %s", ordered.error)
else:
    for manifest in ordered.value:
        result = lifecycle.activate(manifest)
        if result.is_err:
            log.warning("plugin %r failed to activate: %s", manifest.plugin_name, result.error)
        # continue regardless -- isolation rule
```

**Implementing a custom `PluginLifecycle`.** Subclass the ABC in `lifecycle.py` and implement `activate`/`deactivate`/`state_of` against whatever orchestration a deployment needs (a UI-driven flow, persistent state across restarts, ...) — `_DefaultPluginLifecycle`'s own test suite (`tests/unit/plugins/test_lifecycle.py`) demonstrates the isolation and dependency-checking behavior any conforming implementation should preserve.

## Examples

Runnable, narrated scripts live in [`examples/registry/`](../../../examples/registry/README.md) (the Registry Framework's examples cover both `registry` and `plugins`, per the design specification's shared scope):

| Script | Demonstrates |
|---|---|
| `02_version_compatibility.py` | A compatible and an incompatible `PluginManifest` activated side by side via `_DefaultPluginLifecycle`, proving the isolation rule. |

## Design Rationale

- **Why are `registry` and `plugins` separate packages instead of one?** `registry` is the pure, dependency-free mechanism (register/lookup); `plugins` adds lifecycle concerns (manifests, dependency ordering, activation state) that a consumer wanting only a typed lookup table should not have to pull in — mirrors `core`'s module-per-concept discipline at package granularity (design spec AD-RG-02).
- **Why does `PluginLifecycle.activate()` take one manifest at a time instead of a batch?** Keeps the ABC's contract minimal and matches the isolation rule's framing ("a single plugin transitioning to Failed") — batch-level ordering is `resolve_activation_order()`'s separate responsibility (Single Responsibility), composed by the caller rather than baked into the lifecycle interface itself.
- **Why does dependency resolution use a topological sort (Kahn's algorithm) specifically?** The design specification leaves the algorithm as an implementation decision (§34, Known Constraints) while noting topological sort is "the obvious choice" — it directly models "activate every dependency before its dependents," fails fast and clearly on a cycle, and is O(V+E), cheap even for a large plugin ecosystem.
- **Why does `PluginLoader` exist as a separate class from `EntryPointDiscovery` rather than `PluginLifecycle` calling `EntryPointDiscovery` directly?** A `PluginManifest.provides` is a *tuple* of `EntryPointSpec`s (one plugin package can register into multiple registries); `PluginLoader` is the aggregation step that turns "discover N groups" into a single `Result` for the whole manifest, keeping `_DefaultPluginLifecycle.activate()` focused on state transitions rather than discovery bookkeeping.
- **Why is `state_of()` specified to raise `NotFoundError` for a plugin that was never activated, rather than returning e.g. a `DISCOVERED` default?** A lifecycle implementation only becomes aware of a manifest via `activate()`; querying the state of a name it has never seen is a genuine "no such plugin" condition, not an in-progress state — silently returning `DISCOVERED` would misrepresent a plugin that was never even scanned as one already partway through its lifecycle.

## Anti-Patterns

- ❌ **A `PluginLifecycle.activate()` implementation that raises instead of returning `Result.err` on failure.** The isolation rule depends on failures being representable as data the caller can log and continue past, not exceptions that unwind the activation loop.
- ❌ **Calling `EntryPointDiscovery` directly from application code instead of going through `PluginManifest`/`PluginLoader` when manifest-level concerns (version gating, dependencies) matter.** Raw `registry` discovery skips every lifecycle guarantee this package exists to add.
- ❌ **Hard-coding an activation order instead of calling `resolve_activation_order()`.** A hand-maintained order silently drifts out of sync as plugins gain new `depends_on` declarations.
- ❌ **Catching `Exception` instead of `PluginActivationError`/`MineProductivityError`** when handling a failed activation. Every exception this package raises derives from `core.MineProductivityError` specifically so callers do not need a broad `except Exception`.

## Testing & Quality

- `tests/unit/plugins/` — one `test_*.py` per source module — **100% line coverage**.
- `tests/integration/test_registry_plugin_discovery.py` — `_DefaultPluginLifecycle.activate()` exercised end-to-end against two real, independently pip-installed fixture plugin packages, including the version-incompatibility path.
- A dedicated isolation test proves one plugin reaching `Failed` never blocks another's path to `Active` — not just incidental coverage.
- `mypy --strict` and `ruff` are clean on `src/mineproductivity/plugins/` and `tests/unit/plugins/`.

## Contents

See [Package Structure](#package-structure) above for the full file layout.

## Dependencies

**Depends on:** `core`, `registry`.

**Depended on by:** the future `cli` package.

## Future Work

- A persistent activation ledger (which plugins were active when a report was generated) for the traceability need the design specification's §21 Serialization section anticipates.
- Signed/verified plugins for enterprise deployments, as an additional validation step inside a custom `PluginLifecycle.activate()`.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
- [`docs/architecture/03_Registry_Framework_Design_Specification.md`](../../../docs/architecture/03_Registry_Framework_Design_Specification.md)
- [`docs/design/03_Registry_Implementation_Checklist.md`](../../../docs/design/03_Registry_Implementation_Checklist.md)
- Developer & Cookbook Guide Part I, Chapter 9 (plugin distribution, versioning, and the isolation guarantee)
