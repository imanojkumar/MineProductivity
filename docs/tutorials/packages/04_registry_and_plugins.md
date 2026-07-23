# Package Tutorial 4 — Registry & Plugins (Deep)

!!! abstract "Milestone 2 · Package Tutorials · Tutorial 4 of 13"
    Deep, full-surface tutorial for the **extensibility subsystem** —
    `mineproductivity.registry` (the registration + discovery *mechanism*) and
    `mineproductivity.plugins` (the plugin *lifecycle* built on it). Authored to
    **Package Tutorial Template v1.0** under the
    [Package Tutorial Implementation Standard](../../learning/PACKAGE_TUTORIAL_IMPLEMENTATION_STANDARD.md).
    This is the platform's headline capability: how every "the platform refuses to
    choose for you" becomes an installable extension.

## Objective

Master the two packages that make MineProductivity extensible: **`registry`** —
the one generic `Registry`, the `@register` decorator factory, entry-point
`discover`y, and version gating (11 symbols); and **`plugins`** — the
`PluginManifest`, the five-state `PluginLifecycle`, dependency-aware activation
ordering, and isolated failure (8 symbols). The payoff: **developing a custom
plugin** end to end.

All 19 public symbols across both `__all__`s are accounted for under the
**coverage convention** (§5): **13 [deep]** / **6 [ref]**. Public APIs only.

## Prerequisites

- [Package Tutorial 1 — Core](01_core.md): `Result`, `Maybe`, `BaseValueObject`,
  `BaseSpecification`, `BaseRepository`, the exception hierarchy — both packages are
  built on them (§3).
- [Package Tutorials 2 — Ontology](02_ontology.md) and
  [3 — Events](03_events.md): both packages *own a registry* and are the kind of
  thing a plugin extends.

**These packages have no Fundamentals lesson** — they are first exposure at this
depth. §1 and §3 therefore carry their own why-before-how.

## Running the examples

Every code block below is executed and its output pasted verbatim (stdout; the
packages also emit `logging` diagnostics to stderr). Four scripts, no extras:

```bash
pip install -e .
python examples/registry/01_register_and_discover.py    # + registry/02
python examples/plugins/01_manifest_and_lifecycle.py     # + plugins/02
```

---

## 1. Why this subsystem exists

Across the earlier tutorials the platform kept **refusing to choose for you**:
`analytics` ships no forecaster, `decision` no root-cause engine, `visualization`
no renderer. Those refusals are deliberate — the right forecaster is your data's
business, not the framework's. But a refusal is only useful if there is a
*disciplined way to supply the answer yourself*. That is this subsystem.

- **`registry`** is the mechanism: a single, generic, type-safe `Registry` plus a
  `@register` decorator and entry-point `discover`y. Every domain package
  (`kpis`, `connectors`, `analytics`, …) exposes its own `@register` built the
  same *shape* from this one implementation — so a plugin author learns the
  pattern **once** and it works everywhere ("one discovery pattern for the whole
  ecosystem").
- **`plugins`** is the orchestration on top: a `PluginManifest` (a plugin's
  declared identity — what it provides, which core versions it supports, what it
  depends on) driven through a `PluginLifecycle` state machine, with version
  gating, dependency ordering, and the **isolation rule**: one broken plugin must
  never take the platform down.

Together they turn "the platform refuses to choose" into "install a pip package
and the capability appears."

## 2. Architectural role

The two packages sit in the middle of the chain, above the system-of-record and
below the intelligence layers that get extended:

```
core ─► ontology ─► events ─► registry ─► plugins ─► connectors ─► kpis ─► … ─► visualization
```

`registry` depends only on `core`; `plugins` depends on `registry` (+ `core`).
Crucially, **`registry` is the mechanism every package *above* it specializes** —
`kpis` has a KPI registry, `connectors` a connector registry, all type aliases
over the one `Registry`. A package *below* `registry` cannot use it: `ontology`
(Tutorial 2) sits under `registry` in the dependency order, which is exactly why
it carries its **own** small internal type registry rather than importing this one.

## 3. Integration with adjacent layers

**Downward to `core` (Tutorial 1) — both packages are built from Core primitives:**

| Construct | Core primitive it uses |
|---|---|
| `Registry` | a **structural echo of `core.BaseRepository`** (`register`/`lookup`/`get`/`list`/`__contains__`); `register`→`core.Result`, `lookup`→`core.Maybe`, `list(spec)` takes a `core.BaseSpecification`, metadata is a `core.BaseMetadata` |
| `EntryPointSpec`, `VersionRange`, `PluginManifest`, `PluginDependency` | subclass `core.BaseValueObject` (immutable, `validate()` on construction) |
| `EntryPointDiscovery.discover`, `PluginLifecycle.activate`, `resolve_activation_order` | return `core.Result` |
| every exception | derives from `core.MineProductivityError` (registry's `UnregisteredLookupError` via `NotFoundError`) |

**Package interaction — `plugins` builds directly on `registry`:** a
`PluginManifest.provides` is a tuple of `registry.EntryPointSpec`; its
`core_version_range` is a `registry.VersionRange`; activation delegates the actual
entry-point scanning to `registry.EntryPointDiscovery` (via `PluginLoader`) and
gates on `registry.VersionCompatibility`. `plugins` adds only what `registry`
deliberately leaves out: identity, lifecycle, dependencies, ordering.

**Upward — every domain package is a *host* for plugins:** `kpis`, `connectors`,
`analytics`, `agents`, and `visualization` each own a `Registry` and a
`@register`, and each declares an entry-point group a plugin can `provides` into.
This tutorial's `§13` builds exactly such a host.

## 4. Package structure

| Package | Module | Public symbols |
|---|---|---|
| `registry` | `registry` | `Registry` |
| | `decorators` | `registered_in` |
| | `entry_point` | `EntryPointSpec`, `EntryPointDiscovery` |
| | `caching` | `DiscoveryCache` |
| | `version_compat` | `VersionRange`, `VersionCompatibility` |
| | `exceptions` | `RegistrationError`, `DuplicateRegistrationError`, `UnregisteredLookupError`, `VersionIncompatibleError` |
| `plugins` | `manifest` | `PluginManifest`, `PluginDependency` |
| | `lifecycle` | `PluginLifecycle`, `PluginState` |
| | `loader` | `PluginLoader` |
| | `dependency` | `resolve_activation_order` |
| | `exceptions` | `PluginActivationError`, `PluginDependencyError` |

## 5. Public APIs

All 19 exports under the **coverage convention**:

**registry — [deep]**
: `Registry`, `registered_in`, `EntryPointSpec`, `EntryPointDiscovery`,
  `VersionRange`, `VersionCompatibility`, `DuplicateRegistrationError`

**plugins — [deep]**
: `PluginManifest`, `PluginDependency`, `PluginState`, `PluginLifecycle`,
  `resolve_activation_order`, `PluginDependencyError`

**Everything else — [ref]** — see the table.

### Reference coverage

| Symbol | What / when to reach for it |
|---|---|
| `DiscoveryCache` | Memoizes `EntryPointDiscovery.discover` per `EntryPointSpec` for the process (entry-point scanning touches the filesystem); `invalidate()` to force a re-scan. |
| `RegistrationError` | Base class of registry errors — catch it to handle any registration failure category at once. |
| `UnregisteredLookupError` | Raised by `Registry.get(key)` when nothing is registered under `key` (via `core.NotFoundError`). Use `lookup()` for the non-raising `Maybe` form. |
| `VersionIncompatibleError` | Raised by `VersionCompatibility.check_or_raise` when the installed core version is outside a plugin's declared range. |
| `PluginLoader` | The bridge a `PluginLifecycle` uses to complete `Validated → Active`: discovers every `EntryPointSpec` in a manifest's `provides`. Reach for it when writing a custom lifecycle. |
| `PluginActivationError` | Raised when activation fails for a non-version reason (e.g. an entry-point module raised on import); `PluginDependencyError` is its subclass. |

## 6. Conceptual model

Five ideas explain both packages.

**A. One registry, many aliases.** There is exactly one `Registry[TKey, TItem]`
implementation. Every domain registry is a *type alias* over it, never a subclass —
composition over inheritance, one thing to trust (design spec AD-RG-01). A
`Registry` is, structurally, a `BaseRepository` whose "entities" are types.

**B. Registration is add-only.** `register(key, item)` returns a `Result`;
re-registering an existing key is **always rejected**, never a silent overwrite
(AD-RG-04). This is what makes "30 installed KPI packs" safe — two packs claiming
the same code is a loud, catchable error, not a last-writer-wins surprise.

**C. Discovery is entry-point-driven and isolated.** A plugin declares an
entry-point in its `pyproject.toml`; on install, `EntryPointDiscovery.discover`
imports it and its `@register` side effects run. If **one** entry-point's module
raises on import, it is logged and skipped — the other packs still load.

**D. A plugin is a manifest through a lifecycle.** `PluginManifest` is the
declared identity (`plugin_name`, `plugin_version`, `core_version_range`,
`provides`, `depends_on`). `PluginLifecycle.activate` walks it through
`PluginState`: `DISCOVERED → VALIDATED → ACTIVE`, or `FAILED` (in isolation);
`deactivate` → `DEACTIVATED`.

**E. Dependencies and versions are gated up front.** `resolve_activation_order`
topologically sorts manifests so each activates after what it depends on (rejecting
a missing dependency or a cycle as a `Result.err`), and `VersionCompatibility`
refuses a plugin built for an incompatible core — before any of its code runs.

## 7. Real mining examples

The subsystem is domain-free, so the walkthroughs supply the domain: a site runs a
base KPI registry and installs third-party **KPI packs** — `haulmetrics` (a
compatible pack that registers `COST.FuelPerTonne`), a `legacy-analytics-pack`
built for an older core, and a `site-pack` that depends on `haulmetrics`. §13 adds
a `forecasters` host and an `ewma-pack` plugin.

## 8. Step-by-step walkthroughs

### 8.1 Registry: register → discover → lookup

A host package owns a `Registry` and a `@register` decorator built from
`registered_in`. Registering is add-only (a duplicate returns a `Result.err`).
`EntryPointDiscovery.discover(EntryPointSpec(...))` runs a real plugin module's
`@register` side effects — the same code path a pip-installed plugin uses — and
`lookup` returns a `Maybe`. Running
[`01_register_and_discover.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/registry/01_register_and_discover.py):

```text
--- 1. A domain package owns a Registry and a @register decorator ---

--- 2. Registering directly (no plugin involved yet) ---
registered: ['PROD.TruckCycleTime']

--- 3. Duplicate registration is rejected, not silently overwritten ---
re-registering the same code -> is_ok: False, error: DuplicateRegistrationError

--- 4. Discovery: a plugin declares itself via a pyproject.toml entry-point ---
(a real, on-disk module -- the same EntryPointDiscovery code path a pip-installed plugin uses)
discover() -> is_ok: True, loaded entry-points: ('haulmetrics',)
registered after discovery: ['COST.FuelPerTonne', 'PROD.TruckCycleTime']

--- 5. Lookup downstream ---
lookup('COST.FuelPerTonne').is_some: True
lookup('COST.NotARealCode').is_nothing: True
```

After discovery the registry holds both the directly-registered KPI *and* the
plugin's — with no edit to the host package. That is the whole extensibility
promise in one output block.

### 8.2 Version gating and failure isolation

`VersionRange` is a half-open `[min, max)`; `VersionCompatibility.is_compatible`
checks the installed core against it. Activating two plugins — one in range, one
not — proves the isolation rule: the incompatible one goes to `FAILED`, the
compatible one to `ACTIVE`, independently. Running
[`02_version_compatibility.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/registry/02_version_compatibility.py):

```text
--- Installed core version: 0.5.0 ---

--- Two plugins with different declared compatibility ranges ---
compatible_range:   [0.4.0, 1.0.0)
incompatible_range: [1.0.0, 2.0.0)

--- VersionCompatibility.is_compatible() ---
compatible?   True
incompatible? False

--- Full PluginLifecycle.activate(), both plugins, isolation proven ---
legacy-analytics-pack: activate().is_ok=False, state=failed
haulmetrics:           activate().is_ok=True, state=active

The incompatible plugin's failure never touched the compatible plugin's activation.
```

### 8.3 The plugin lifecycle

A `PluginManifest` declares a plugin's identity. `PluginLifecycle.activate` walks
it to `ACTIVE` (or `FAILED`, isolated), and `deactivate` to `DEACTIVATED` — the
five `PluginState`s. Running
[`01_manifest_and_lifecycle.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/plugins/01_manifest_and_lifecycle.py):

```text
--- 1. A manifest is a plugin's declared identity ---
haulmetrics v1.0.0 provides -> ['kpis']

--- 2. Activation walks the state machine to Active ---
activate().is_ok=True, state=active

--- 3. Version gating: a plugin built for an older core is failed, in isolation ---
legacy-pack activate().is_ok=False, state=failed
haulmetrics still: active (unaffected by legacy-pack's failure)

--- 4. Deactivation moves an active plugin to Deactivated ---
haulmetrics after deactivate: deactivated
all five states exist: ['discovered', 'validated', 'active', 'failed', 'deactivated']
```

### 8.4 Activation order and dependencies

When plugins depend on each other, `resolve_activation_order` topologically sorts
them (Kahn's algorithm) so each activates after its dependencies — and returns a
`Result.err(PluginDependencyError)` for a missing dependency or a cycle, rather than
raising or hanging. Running
[`02_activation_order.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/plugins/02_activation_order.py):

```text
--- 1. Declared out of order; the resolver sorts by dependency ---
is_ok=True, order=['base-metrics', 'haulmetrics', 'site-pack']

--- 2. A dependency on a plugin not being resolved is rejected ---
is_ok=False, error=PluginDependencyError

--- 3. A dependency cycle is detected, never hung on ---
is_ok=False, error=PluginDependencyError
```

## 9. Repository example reuse

Two `registry` scripts were reused; the two `plugins` scripts were **authored for
this tutorial** (the package had no examples — Standard §1/Risk R2) and added to
the shared lesson-execution smoke test. All four executed (exit `0`), output above.

| Script | Public API it exercises | Walkthrough |
|---|---|---|
| [`registry/01_register_and_discover.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/registry/01_register_and_discover.py) | `Registry`, `registered_in`, `EntryPointDiscovery`, `EntryPointSpec`, `DuplicateRegistrationError` | §8.1 |
| [`registry/02_version_compatibility.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/registry/02_version_compatibility.py) | `VersionRange`, `VersionCompatibility`, `PluginManifest`, `PluginState` | §8.2 |
| [`plugins/01_manifest_and_lifecycle.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/plugins/01_manifest_and_lifecycle.py) | `PluginManifest`, `PluginState`, `PluginLifecycle` | §8.3 |
| [`plugins/02_activation_order.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/plugins/02_activation_order.py) | `PluginDependency`, `resolve_activation_order`, `PluginDependencyError` | §8.4 |

## 10. Common mistakes

| Mistake | What happens | Do this instead |
|---|---|---|
| Expecting `register` to overwrite an existing key | It returns `Result.err(DuplicateRegistrationError)` — add-only by design | Choose a unique key; a clash is a real conflict to resolve |
| Ignoring the `Result` from `register`/`activate`/`discover` | You miss the failure path | Check `is_ok` / handle `error` |
| Letting one bad plugin abort discovery | Would defeat the isolation rule | `discover` already skips a failing entry-point; don't wrap it to re-raise |
| Subclassing `Registry` to add behaviour | Fragments "one registry to trust" | Use a **type alias**; add behaviour in your `@register` |
| Using `registry` from a package below it (e.g. `ontology`) | Import cycle — ontology sits under registry | Below `registry`, carry a small internal registry (as ontology does) |
| Skipping `depends_on`/version metadata in a manifest | Activation order and gating can't protect you | Declare `core_version_range`, `provides`, `depends_on` honestly |
| Reaching into `_DefaultPluginLifecycle` as your production runtime | It's the private reference impl | Implement the public `PluginLifecycle` contract for production |

## 11. Best practices

- **Build your `@register` from `registered_in`** for the common case; call
  `Registry.register()` directly only when you need extra registration-time
  validation.
- **Keep registration add-only and keys globally unique** within a registry
  (namespaced codes like `COST.FuelPerTonne` help).
- **Let discovery isolate failures** — never wrap `discover` so one pack's import
  error aborts the rest.
- **Declare a truthful `PluginManifest`**: real `core_version_range`, every
  `provides` group, every `depends_on`.
- **Resolve activation order** for interdependent plugins instead of activating in
  arbitrary order.
- **Cache discovery** with `DiscoveryCache` in long-lived processes; `invalidate()`
  when you knowingly install a plugin mid-process.

## 12. Performance considerations

- **Entry-point scanning is not free** (it touches installed-package metadata and
  imports modules). `DiscoveryCache` memoizes per `EntryPointSpec` for the process;
  it invalidates only on an explicit `invalidate()`, never implicitly.
- **A `Registry` is a dict** — `register`/`lookup`/`get`/`__contains__` are O(1);
  `list(spec)` is O(n) and its specification short-circuits (Tutorial 1).
- **`resolve_activation_order` is O(V + E)** in plugins and dependency edges
  (Kahn's algorithm) — linear, and it detects cycles rather than looping.
- **Version parsing is dependency-free and cheap** (leading-digit comparison); it
  is not a full semver parser, by design (no third-party dependency in the base
  install).

## 13. Extension points — custom plugin development

The whole subsystem *is* the extension mechanism, so §13 shows **developing a
plugin end to end**: a host package exposes a typed `Registry` + `@register`; a
plugin registers into it without editing the host; then the plugin is packaged as a
`PluginManifest` and activated through the lifecycle. The example was executed and
passes `ruff` / `ruff format --check` / `mypy --strict`:

```python
from typing import Any

from mineproductivity.plugins import PluginManifest, PluginState
from mineproductivity.plugins.lifecycle import _DefaultPluginLifecycle  # reference impl, as in every example
from mineproductivity.registry import EntryPointSpec, Registry, VersionRange, registered_in

# 1. The HOST package owns one typed registry + a @register decorator.
FORECASTER_REGISTRY: Registry[str, Any] = Registry(name="forecasters")
register_forecaster = registered_in(FORECASTER_REGISTRY, key_of=lambda cls: cls.code)


# 2. A PLUGIN author registers a class -- the host is never edited.
@register_forecaster
class EwmaForecaster:
    code = "FORECAST.Ewma"
```

Exercising it — the registered item is discoverable, add-only is enforced, and the
plugin activates to `ACTIVE`:

```text
--- 1. The registered item is discoverable by its key ---
get('FORECAST.Ewma') is EwmaForecaster: True
registry now holds: ['FORECAST.Ewma']

--- 2. Registration is add-only: a duplicate key is rejected ---
re-register -> is_ok=False, error=DuplicateRegistrationError

--- 3. Package it as a plugin and activate it through the lifecycle ---
activate('ewma-pack').is_ok=True, state=active
reached PluginState.ACTIVE: True
```

```python
    manifest = PluginManifest(
        plugin_name="ewma-pack", plugin_version="1.0.0",
        core_version_range=VersionRange(min_version="1.0.0", max_version_exclusive="2.0.0"),
        provides=(EntryPointSpec(group="mineproductivity.forecasters", target_registry="forecasters"),),
    )
    lifecycle = _DefaultPluginLifecycle(core_version="1.2.0")
    result = lifecycle.activate(manifest)   # -> PluginState.ACTIVE
```

Two further extension surfaces use the same idiom: a **custom `PluginLifecycle`**
(implement `activate`/`deactivate`/`state_of` for a distributed or persisted
runtime — the public contract the private reference impl fulfils), and a **new
host registry** in your own domain package (a type alias over `Registry` + a
`@register`), which any future plugin can then target.

!!! note "The reference lifecycle is intentionally private"
    `PluginLifecycle` is an abstract contract; `plugins` ships a *private*
    reference implementation (`_DefaultPluginLifecycle`) for tests and examples,
    not a public production runtime — exactly as `events` keeps `_InMemoryEventStore`
    private (Tutorial 3). Use it as a harness; implement the contract for production.

## 14. Exercises

1. **Own a registry.** Build a `Registry[str, type]`, wrap it with `registered_in`,
   register two classes, and show a duplicate key returns `Result.err`. Then
   `list()` everything registered.
2. **Gate a version.** Construct a `VersionRange` and check three core versions
   (below, inside, at the exclusive upper bound) with
   `VersionCompatibility.is_compatible`. Which of the three is compatible, and why is
   the upper bound exclusive?
3. **Walk the lifecycle.** Activate a compatible manifest and an incompatible one
   through `_DefaultPluginLifecycle`; assert their `state_of` is `ACTIVE` and
   `FAILED` respectively, and that one did not affect the other.
4. **Order a dependency graph.** Build four manifests where `d` depends on `c`, `c`
   on `b`, `b` on `a`; pass them to `resolve_activation_order` in shuffled order and
   confirm the result is `a, b, c, d`. Then introduce a cycle and observe the error.
5. **Develop a plugin.** Following §13, expose a `sensors` host registry, register a
   `VibrationSensor` into it, wrap it in a `PluginManifest`, and activate it. Confirm
   the class is retrievable *and* the plugin reaches `ACTIVE`.

## 15. Reference solutions

??? success "Solution 1 — Own a registry"
    ```python
    reg: Registry[str, type] = Registry(name="widgets")
    register = registered_in(reg, key_of=lambda cls: cls.__name__)
    @register
    class Alpha: ...
    @register
    class Beta: ...
    reg.register("Alpha", Alpha).is_ok   # False — add-only
    list(reg)                            # ['Alpha', 'Beta']
    ```

??? success "Solution 2 — Gate a version"
    ```python
    r = VersionRange(min_version="1.0.0", max_version_exclusive="2.0.0")
    VersionCompatibility.is_compatible(r, "0.9.9")  # False (below)
    VersionCompatibility.is_compatible(r, "1.5.0")  # True  (inside)
    VersionCompatibility.is_compatible(r, "2.0.0")  # False (upper bound is exclusive)
    ```
    The upper bound is exclusive so a *new major* (`2.0.0`), which may break the
    plugin's assumptions, is never silently accepted.

??? success "Solution 3 — Walk the lifecycle"
    ```python
    lc = _DefaultPluginLifecycle(core_version="1.2.0")
    lc.activate(good_manifest)   # core_version_range covers 1.2.0
    lc.activate(bad_manifest)    # range excludes 1.2.0
    assert lc.state_of("good") is PluginState.ACTIVE
    assert lc.state_of("bad") is PluginState.FAILED
    ```

??? success "Solution 4 — Order a dependency graph"
    ```python
    order = resolve_activation_order([d, a, c, b])   # any input order
    [m.plugin_name for m in order.value]             # ['a', 'b', 'c', 'd']
    # a cycle (a<-b, b<-a) -> Result.err(PluginDependencyError)
    ```

??? success "Solution 5 — Develop a plugin"
    ```python
    SENSORS: Registry[str, Any] = Registry(name="sensors")
    register_sensor = registered_in(SENSORS, key_of=lambda cls: cls.code)
    @register_sensor
    class VibrationSensor:
        code = "SENSOR.Vibration"
    manifest = PluginManifest(
        plugin_name="sensor-pack", plugin_version="1.0.0",
        core_version_range=VersionRange(min_version="1.0.0", max_version_exclusive="2.0.0"),
        provides=(EntryPointSpec(group="mineproductivity.sensors", target_registry="sensors"),),
    )
    lc = _DefaultPluginLifecycle(core_version="1.1.0")
    assert lc.activate(manifest).is_ok and lc.state_of("sensor-pack") is PluginState.ACTIVE
    assert SENSORS.get("SENSOR.Vibration") is VibrationSensor
    ```

## 16. Further reading

- **[`registry` package guide](../../packages/registry.md)** · **[`plugins` package guide](../../packages/plugins.md)** — the capability-tour views.
- **[`registry` API reference](../../api-reference/registry.md)** · **[`plugins` API reference](../../api-reference/plugins.md)** — every symbol, from source.
- **[Registry Framework Design Specification](../../architecture/03_Registry_Framework_Design_Specification.md)** — AD-RG-01 (one registry), AD-RG-04 (add-only), the isolation rule (§11/§26), the lifecycle state machine.
- **[Package Tutorial 1 — Core](01_core.md)** — `Result`/`Maybe`/`BaseRepository`, the primitives both packages are built on.

---

**Next package tutorial:** Connectors (deep) — the vendor-neutral ingestion
boundary that turns real FMS/dispatch data into the events of Tutorial 3.
*(Not yet written — Tutorial 5 of 13.)*
