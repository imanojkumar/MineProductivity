# mineproductivity.registry

## Purpose

`mineproductivity.registry` is the plugin-first backbone of MineProductivity: the single, generic discovery-and-lookup mechanism that lets KPIs, connectors, ontology entity types, and analytics models be added to the platform as separate, installable packages, with zero change to the core. It is the direct implementation of the root README's plugin-first principle.

This package implements the [Registry Framework Design Specification](../../../docs/architecture/03_Registry_Framework_Design_Specification.md) exactly. Where this README and that specification disagree, the specification governs. Note the specification covers **two** packages together: `registry` (this package, the pure mechanism) and [`plugins`](../plugins/README.md) (the lifecycle layer built on it).

## Scope

**What belongs here:**

- The generic `Registry[TKey, TItem]` mechanism: register, lookup, get, list, metadata.
- `EntryPointDiscovery`/`EntryPointSpec` — scanning Python entry-points via `importlib.metadata`.
- `registered_in()` — the generic `@register` decorator factory every domain package's own decorator is built from.
- `VersionRange`/`VersionCompatibility` — plugin-to-core version gating.
- `DiscoveryCache` — scan-once-per-process memoization of discovery results.

**What must never belong here:**

- What gets registered. A `KPIMetadata` instance, a connector subclass, an `EquipmentType` subclass — their shapes are defined by `kpis`, `connectors`, `ontology` respectively; `registry` only defines the container.
- Plugin lifecycle concerns (activation state, manifests, inter-plugin dependencies) — see [`plugins`](../plugins/README.md).
- Any domain package import (`ontology`, `events`, `kpis`, `connectors`, `analytics`, `optimization`, `simulation`, `decision`, `digital_twin`, `agents`) — the mechanism cannot play favorites among the things it discovers, because it cannot even see them.

## Architecture

`registry` is a **cross-cutting** package per the root README's dependency rules: may be depended upon by any layer, but must never depend on a domain layer.

```
core  →  registry  →  plugins
```

`Registry[TKey, TItem]` is a deliberate structural echo of `core.BaseRepository`: a registry *is*, conceptually, a repository whose entities are types/classes/callables instead of domain entities. It does not subclass `BaseRepository` (its keys are typically strings/codes, not `BaseEntity` ids), and every domain-specific registry (a future `kpis.REGISTRY`, `connectors.CONNECTORS`, `ontology`'s internal entity-type registry) is a **type alias** over this one class, never a subclass with new behavior (design spec AD-RG-01) — composition over inheritance applied at the plugin-architecture level.

Discovery is scan-once, cache-forever within a process (`DiscoveryCache`): `importlib.metadata` entry-point scanning touches installed-package metadata on disk and is not repeated on every `Registry.get()` call. Lookup itself is O(1) regardless of how many plugins are installed.

See the [design specification's §10](../../../docs/architecture/03_Registry_Framework_Design_Specification.md) for the full object model, sequence diagrams, and class diagrams.

## Package Structure

```
registry/
├── __init__.py           # public API surface (__all__)
├── registry.py             # Registry[TKey, TItem]
├── entry_point.py            # EntryPointSpec, EntryPointDiscovery
├── decorators.py                # registered_in() -- the generic @register decorator factory
├── version_compat.py              # VersionRange, VersionCompatibility
├── caching.py                       # DiscoveryCache
├── exceptions.py                      # the registry exception hierarchy
└── README.md                            # this file
```

## Dependency Rules

```
core  →  registry  →  plugins
```

- **`registry` depends on:** `core` only. No other package.
- **`registry` is depended on by:** `plugins`, and will be depended on by `ontology` (its internal entity-type registry, once migrated), `events`, `kpis`, `connectors`, `analytics`, `agents` — every package that exposes an extension point.
- **Forbidden:** `registry` must never import `plugins`, `ontology`, `events`, `connectors`, `kpis`, `analytics`, `optimization`, `simulation`, `decision`, `digital_twin`, or `agents`. This is mechanically checked by `tests/unit/registry/test_public_api.py::TestNoForbiddenDependencies`.

## Public API

```python
from mineproductivity.registry import (
    Registry, EntryPointDiscovery, EntryPointSpec,
    VersionCompatibility, VersionRange, DiscoveryCache,
    registered_in,
    RegistrationError, DuplicateRegistrationError,
    UnregisteredLookupError, VersionIncompatibleError,
)
```

## Extension Guide

**Building a domain registry.** Instantiate `Registry[TKey, TItem]`, expose it as `REGISTRY` (or a domain-appropriate name), and build a thin `@register` decorator. When registration needs nothing beyond "derive a key, reject a duplicate," build it directly from `registered_in()` — `connectors.register_connector` does exactly this:

```python
# src/mineproductivity/connectors/_registry.py
from mineproductivity.registry import Registry, registered_in

CONNECTORS: Registry[str, type[FMSConnector]] = Registry(name="connectors")
register_connector = registered_in(CONNECTORS, key_of=lambda cls: cls.name)
```

When a domain package needs additional registration-time validation, it implements its own `@register` calling `Registry.register()` directly instead of wrapping `registered_in()` — `kpis.register` does this to also raise `KPICircularDependencyError` immediately if the new KPI would complete a dependency cycle, never deferred to first use (see `kpis/_registry.py`). Every domain package's `@register` still shares the same *shape* — decorator, typed `Registry`, raising lookup — even when it isn't literally built from this one function; that shape, not this specific helper, is the actual consistency guarantee. (`ontology.register_equipment` is a different case again: `ontology` sits below `registry` in the dependency stack and cannot import it at all, so its entity-type registry predates and is independent of this package.)

```toml
# In a THIRD-PARTY plugin package's pyproject.toml
[project.entry-points."mineproductivity.kpis"]
haulmetrics = "mineproductivity_haulmetrics.kpis"
```

**Discovering installed plugins at startup:**

```python
from mineproductivity.registry import EntryPointDiscovery, EntryPointSpec

discovery = EntryPointDiscovery()
result = discovery.discover(EntryPointSpec(group="mineproductivity.kpis", target_registry="kpis"))
if result.is_err:
    log.warning("KPI plugin discovery scan failed: %s", result.error)
```

An exception raised while importing any *one* entry-point's target module is caught, logged, and skipped by `EntryPointDiscovery` itself — it never aborts discovery of the remaining entry-points in the same group (the isolation rule).

**Gating a plugin by core version.** Declare a `VersionRange` and check it before activation (`plugins.PluginLifecycle` does this automatically as part of `activate()`; call it directly for a standalone check):

```python
from mineproductivity.registry import VersionCompatibility, VersionRange

VersionCompatibility.check_or_raise(VersionRange(min_version="0.5.0", max_version_exclusive="1.0.0"), "0.5.0")
```

## Examples

Runnable, narrated scripts live in [`examples/registry/`](../../../examples/registry/README.md):

| Script | Demonstrates |
|---|---|
| `01_register_and_discover.py` | The full register → discover → lookup cycle, including duplicate-key rejection and a real, on-disk module discovered through `EntryPointDiscovery`. |
| `02_version_compatibility.py` | A compatible and an incompatible plugin activated side by side, proving the incompatible one's failure never blocks the compatible one. |

## Design Rationale

- **Why one generic `Registry[TKey, TItem]` class, specialized by type alias per domain, rather than a base class subclassed per domain?** A domain registry needs no *behavior* beyond the generic mechanism, only a *type* — subclassing would add ceremony without adding capability (design spec AD-RG-01).
- **Why does `Registry.register()` return a `Result` instead of raising on a duplicate key?** Duplicate registration during plugin discovery is an expected, recoverable condition (two plugins claiming the same code), not an exceptional one — `Result` lets a discovery loop continue processing the remaining entry-points after logging the conflict, mirroring `EntryPointDiscovery`'s own isolation philosophy.
- **Why is registration add-only, with no update path?** A registered key is a public contract (a KPI code, a connector name, an entity type code); silently overwriting it on re-registration is exactly the "our numbers don't match" failure mode the whole registry design exists to prevent (design spec AD-RG-04). A genuine new version of what a code means is a versioning event the *owning domain package* governs, never a mechanism-level silent overwrite.
- **Why does `Registry` store types/classes by default, not instances?** Matches every worked example in the Cookbook (`REGISTRY.get("PROD.TPH")()` — instantiated at point of use) and keeps registered-item memory footprint independent of how many times an item is used (design spec AD-RG-05).
- **Why is `DiscoveryCache` a separate class from `EntryPointDiscovery` rather than caching being built into `discover()` itself?** Single Responsibility: `EntryPointDiscovery` knows how to scan and import; `DiscoveryCache` knows when *not* to re-scan. Separating them also makes the "never invalidated implicitly" contract auditable in one small class instead of buried inside a larger one.
- **Why does `registered_in()` take `key_of`/`metadata_of` callables instead of requiring every registered item to implement a common protocol?** Domain packages register very different kinds of things (KPI classes, connector classes, entity types) with different metadata shapes; deriving the key/metadata via a caller-supplied function keeps `registry` itself free of any assumption about what shape a registered item takes.

## Anti-Patterns

- ❌ **A domain package implementing its own ad hoc `dict`-based registry** instead of instantiating `Registry[T]`. Every domain registry must be a `Registry` instance so tooling, discovery, and version-compatibility checks work uniformly platform-wide.
- ❌ **Silently overwriting a registration on key collision.** Always reject and log; see Design Rationale above.
- ❌ **Eagerly importing every possible plugin module at `registry` import time.** Discovery is driven by *installed* entry-points, never by `registry` maintaining a hard-coded list of "known" plugins.
- ❌ **Letting one plugin's import-time exception crash application startup.** `EntryPointDiscovery` already isolates this — do not wrap `discover()` calls in code that re-raises on the first entry-point failure.
- ❌ **A `Registry` instance stored as a bare module-level global mutated from arbitrary call sites outside its owning package.** Every registry has exactly one owner package that constructs and exposes it.
- ❌ **Reaching into `Registry._items` or `Registry._metadata` directly.** Use the public methods; the underscore-prefixed attributes are implementation detail.

## Testing & Quality

- `tests/unit/registry/` — one `test_*.py` per source module — **100% line coverage**.
- `tests/integration/test_registry_plugin_discovery.py` — discovery and isolation proven against two real, independently pip-installed fixture plugin packages (`tests/fixtures/plugins/`), not mocks.
- `mypy --strict` and `ruff` are clean on `src/mineproductivity/registry/`, `tests/unit/registry/`, and `examples/registry/`.
- Concurrent `DiscoveryCache.get_or_discover()` calls for the same spec are covered by a dedicated thread-based stress test, not just incidental coverage.

## Contents

See [Package Structure](#package-structure) above for the full file layout.

## Dependencies

**Depends on:** `core` only.

**Depended on by:** `plugins`; will be depended on by `ontology`, `events`, `kpis`, `connectors`, `analytics`, `agents`.

## Future Work

- `ontology`'s internal `_EntityTypeRegistry` migrating to a `Registry[str, type[BaseEntityType]]` instance once this package existed to delegate to (documented as a forward-compatible seam in `ontology/README.md`).
- A registry introspection/discovery CLI surface (`mineprod plugins list`), built on `Registry.list()`/`PluginManifest`, requiring no changes to this package.
- Remote/marketplace plugin discovery as an additional `EntryPointDiscovery`-like source beyond local `importlib.metadata`.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
- [`docs/architecture/03_Registry_Framework_Design_Specification.md`](../../../docs/architecture/03_Registry_Framework_Design_Specification.md)
- [`docs/design/03_Registry_Implementation_Checklist.md`](../../../docs/design/03_Registry_Implementation_Checklist.md)
- Developer & Cookbook Guide Part I, Chapter 3 (layered configuration) and Chapter 9 ("one discovery pattern for the whole ecosystem")
