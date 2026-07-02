# Registry Framework — Implementation Checklist

**Packages:** `mineproductivity.registry` + `mineproductivity.plugins`
**Governing specification:** [`docs/architecture/03_Registry_Framework_Design_Specification.md`](../architecture/03_Registry_Framework_Design_Specification.md)
**Status:** Not started

Binding implementation contract covering both locked packages. Complete in order; every box must be checked or explicitly deferred with a linked issue and Chief Software Architect sign-off before merge.

## Pre-Implementation Gate

- [ ] Design specification read in full by the implementer.
- [ ] `core` (v0.2.0) available and importable; confirm `registry`/`plugins` import no domain package (design spec §7).
- [ ] This checklist reviewed against the design spec's §36/§37 — no drift.

## Package Structure

- [ ] `src/mineproductivity/registry/` created matching design spec §6: `registry.py`, `entry_point.py`, `decorators.py`, `version_compat.py`, `caching.py`, `exceptions.py`, `__init__.py`, `README.md`.
- [ ] `src/mineproductivity/plugins/` created matching design spec §6: `manifest.py`, `lifecycle.py`, `loader.py`, `dependency.py`, `exceptions.py`, `__init__.py`, `README.md`.
- [ ] `registry/README.md` and `plugins/README.md` written following the `core/README.md` template.

## Public API

- [ ] `registry/__init__.py` and `plugins/__init__.py` each export exactly the symbol lists in design spec §8, alphabetized `__all__`.
- [ ] `test_public_api.py` in each package's test suite mirrors `tests/unit/core/test_public_api.py`.

## Interfaces / Object Model

- [ ] `Registry[TKey, TItem]` (§10.1) — `register`, `lookup`, `get`, `list` (with `BaseSpecification` filtering), `metadata_for`, `__contains__`, `__len__`, `__iter__`.
- [ ] `EntryPointSpec` + `EntryPointDiscovery` (§10.2) — `discover()` returns `Result[Sequence[TKey]]`.
- [ ] Domain registry type-alias pattern (§10.3) documented with a concrete worked example in `registry/README.md`'s Extension Guide (not implemented here — owned by `kpis`/`connectors`/`ontology`/`analytics`).
- [ ] `VersionRange` + `VersionCompatibility` (§10.4) — `is_compatible`/`check_or_raise`.
- [ ] `DiscoveryCache` (§10.5) — `get_or_discover`, explicit-only `invalidate`.
- [ ] `PluginManifest` + `PluginDependency` (§10.6).
- [ ] `PluginState` enum — `DISCOVERED`, `VALIDATED`, `ACTIVE`, `FAILED`, `DEACTIVATED`.
- [ ] `PluginLifecycle` ABC — `activate`, `deactivate`, `state_of`.

## Lifecycle & State Machine

- [ ] Plugin lifecycle (§11) implemented exactly: Discovered → Validated → (Failed | Active) → Deactivated.
- [ ] **Isolation rule proven**: one plugin reaching `Failed` never blocks another's path to `Active` (dedicated test, not incidental coverage).
- [ ] Registration key lifecycle (§12): Unregistered → Registered → (rejected on re-register) → Deprecated → Retired, all via metadata flags, never key deletion.

## Validation

- [ ] Duplicate-key rejection (`Registry.register()` returns `Result.err(DuplicateRegistrationError)`) — no silent overwrite path exists anywhere in the codebase.
- [ ] `VersionCompatibility.check_or_raise` tested across inclusive/exclusive boundary cases.
- [ ] `PluginLifecycle.activate()` verifies every `PluginDependency` is itself active/activatable before activating the dependent.

## Versioning

- [ ] Confirmed `registry` itself bakes in no domain-specific (KPI/connector) versioning semantics — only the generic container.
- [ ] `PluginManifest.plugin_version` SemVer discipline documented.

## Serialization

- [ ] `PluginManifest`/`EntryPointSpec` serialize via `core.serialization` (`DataclassSerializer`/`to_dict`).

## Performance & Memory

- [ ] `DiscoveryCache` confirmed scan-once-per-process (test: second `get_or_discover()` call for the same spec does not re-invoke `EntryPointDiscovery.discover()`'s underlying scan).
- [ ] `Registry.get()` lookup confirmed O(1) regardless of registry size (benchmark with a synthetic large registry).

## Thread Safety & Concurrency

- [ ] Concurrent reads from multiple threads against a post-startup `Registry` confirmed safe.
- [ ] Concurrent `DiscoveryCache.get_or_discover()` calls for the *same* spec from multiple threads produce exactly one discovery pass (stress test).
- [ ] Confirmed no bare module-level mutable registry exists anywhere outside an owning package's single instance (grep-based check, mirrors `core`'s "no global state" audit).

## Error Handling

- [ ] Full exception hierarchy (§26): `RegistrationError`, `DuplicateRegistrationError`, `UnregisteredLookupError`, `VersionIncompatibleError`, `PluginActivationError`, `PluginDependencyError`.
- [ ] Exception raised while importing one plugin's entry-point module is caught and converted to `Failed` state / logged warning — never propagates to abort discovery of remaining plugins (dedicated isolation test, see Lifecycle section).

## Logging

- [ ] Successful activation logged at `INFO` (plugin name, version, registries populated, item count).
- [ ] Failed activation logged at `WARNING` with specific reason (version vs. dependency vs. import error, distinguishable in the log message).
- [ ] Duplicate-key rejection logged at `WARNING` with both existing and attempted registration's source module.

## Configuration

- [ ] Entry-point group scan list and eager-vs-lazy discovery timing confirmed as `core.BaseConfiguration`-shaped, sourced externally (not hard-coded in `registry`).

## Tests

- [ ] `tests/unit/registry/` and `tests/unit/plugins/` each mirror their source package 1:1.
- [ ] Coverage ≥95% for both packages.
- [ ] A real, independently-built fixture plugin package (installable via `pip install`) used for discovery/integration tests.
- [ ] Isolation test: one broken + one healthy fixture plugin, both discovered together.
- [ ] Concurrency stress tests per Thread Safety section.

## Documentation

- [ ] `registry/README.md` and `plugins/README.md` complete.
- [ ] Extension Guide section shows the exact `@register` decorator pattern every domain package is expected to replicate.

## Examples

- [ ] `examples/registry/01_register_and_discover.py` — full register → discover → lookup cycle using a fixture plugin.
- [ ] `examples/registry/02_version_compatibility.py` — demonstrates a compatible and an incompatible plugin side by side.
- [ ] All examples pass `mypy --strict` + `ruff`.

## Benchmarks

- [ ] Discovery-scan cost vs. registry size recorded in `benchmark/reports/registry/`.
- [ ] Lookup latency at 1x, 10x, 100x typical plugin-count scale recorded.

## Certification

- [ ] Categories A (substituted golden-plugin-fixture), B (integration), C (edge cases), D (corrupted data) from design spec §30 pass.
- [ ] Zero-installed-plugins case confirmed to produce an empty, valid registry — not an error.

## Type Hints, Mypy, Ruff, Coverage

- [ ] 100% type-hinted; `mypy --strict` clean on both packages.
- [ ] `ruff check` and `ruff format --check` clean.
- [ ] Coverage report attached; ≥95% for both packages.

## Release

- [ ] `CHANGELOG.md` updated.
- [ ] Root README dependency diagram cross-checked.
- [ ] Version bump proposed and reviewed.
- [ ] Design spec §37 re-verified as final merge gate.

---

*Derived from [`03_Registry_Framework_Design_Specification.md`](../architecture/03_Registry_Framework_Design_Specification.md). Keep in sync with the governing specification.*
