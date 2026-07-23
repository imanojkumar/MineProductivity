# Package Tutorial 5 — Connectors (Deep)

!!! abstract "Milestone 2 · Package Tutorials · Tutorial 5 of 13"
    Deep, full-surface tutorial for `mineproductivity.connectors` — the
    vendor-neutral **ingestion boundary** that turns any data source into the
    canonical events of Tutorial 3. Authored to **Package Tutorial Template v1.0**
    under the [Package Tutorial Implementation Standard](../../learning/PACKAGE_TUTORIAL_IMPLEMENTATION_STANDARD.md).
    This is the last tutorial of Unit A (Foundation).

## Objective

Master the working surface of `mineproductivity.connectors`: the one small
`FMSConnector` contract every source implements, the six reference connectors and
the `CONNECTORS` registry, resilient network ingestion (`RetryPolicy`,
`BackoffStrategy`, `AuthProvider`), health reporting, source-independent
normalization (`Normalizer`, `FieldMapper`, `ReasonCodeMap`), and — the payoff —
**implementing `FMSConnector` for a new source**.

All 25 public symbols (`mineproductivity.connectors.__all__`) are accounted for
under the **coverage convention** (§5): **13 [deep]** / **12 [ref]**. Public APIs
only.

## Prerequisites

- [Package Tutorial 1 — Core](01_core.md), [2 — Ontology](02_ontology.md),
  [3 — Events](03_events.md), [4 — Registry & Plugins](04_registry_and_plugins.md):
  connectors integrates **all four** (§3) — it is the layer where the whole of
  Unit A comes together.

**No Fundamentals lesson** — first exposure at this depth; §1 and §3 carry their
own why-before-how.

## Running the examples

Every code block below is executed and its output pasted verbatim. Three scripts
(the third authored for this tutorial), no extras:

```bash
pip install -e .
python examples/connectors/01_csv_ingestion.py     # + 02_rest_with_retry, 03_custom_connector
```

---

## 1. Why this package exists

Every layer you have met so far assumes the events already exist. But real data
arrives as a vendor CSV export, a dispatch-system REST API, a Kafka topic — each
with its own field names, its own reason codes, its own auth and failure modes.
Something has to stand at the boundary and turn all of that into the *one*
canonical event vocabulary the platform speaks. That is `connectors`.

Its contract is deliberately tiny: **"every connector implements one small
abstract base class."** A source-specific adapter yields canonical
`events` (a `CycleEvent`, a `DelayEvent`, …) and nothing else — the rest of the
platform never sees a raw CSV row or a vendor JSON blob. Two disciplines make this
robust:

- **The connector never exposes raw records** — it normalizes at the boundary, so
  a mapping bug is caught in one place, not smeared across every downstream KPI.
- **Ingestion is resilient by construction** — retry/backoff and auth-refresh are
  shared, tested machinery, not re-invented per vendor.

## 2. Architectural role

`connectors` is the top of Unit A: it depends on everything below it and feeds
everything above it.

```
core ─► ontology ─► events ─► registry ─► plugins ─► connectors ─► kpis ─► … ─► visualization
```

It is where the mine's **real data enters the platform**. Downstream, `kpis`
computes from the events a connector ingested; a `digital_twin` cold-starts from
them. A new vendor integration is a new connector — a pip-installable plugin
(Tutorial 4) that registers into `CONNECTORS` — not a change to any layer above.

## 3. Integration with adjacent layers

Connectors is the **confluence of Unit A** — it uses all four packages below it.

**`core` (Tutorial 1):**

| Connectors construct | Core primitive |
|---|---|
| `RetryPolicy` | subclasses `core.BaseConfiguration` (immutable, validated, `from_mapping`) |
| `Credentials`, `ConnectorHealth`, `FieldMapper`, `ReasonCodeMap` | subclass `core.BaseValueObject` |
| `AuthProvider.refresh()` | returns a `core.Result`; `ReasonCodeMap.resolve()` returns a `core.Maybe` |
| every exception | derives from `core.MineProductivityError` |

**`registry` (Tutorial 4) — connectors is a *host*:** `CONNECTORS` is a
`registry.Registry[str, type[FMSConnector]]`; `register_connector` is
`registry.registered_in(CONNECTORS, key_of=lambda cls: cls.name)`; `get_connector`
is `CONNECTORS.get`. The "a package exposes a registry a plugin targets" idea from
Tutorial 4 is exactly this — a third-party vendor pack does `@register_connector`
and appears in `CONNECTORS` on install.

**`ontology` (Tutorial 2):** `ReasonCodeMap` maps a vendor's delay-reason string to
an **`ontology.DelayCategory`** — the governed taxonomy, so every site's delays
become comparable.

**`events` (Tutorial 3) — the whole point:** every `FMSConnector.get_*_data` method
**yields canonical `events`** (`CycleEvent`, `DelayEvent`, …). A connector is the
producer at the head of the event log; everything downstream consumes what it
ingests. This is the platform's data-flow in one sentence: **connectors ingest →
events record → the intelligence layers derive.**

## 4. Package structure

| Group | Module(s) | Public symbols |
|---|---|---|
| The contract | `base` | `FMSConnector`, `IngestionMode` |
| The registry | `_registry` | `CONNECTORS`, `register_connector`, `get_connector` |
| Reference connectors | `file/`, `network/`, `streaming/` | `CSVConnector`, `ExcelConnector`, `RestConnector`, `GraphQLConnector`, `KafkaConnector`, `MqttConnector` |
| Resilience | `retry`, `auth` | `RetryPolicy`, `BackoffStrategy`, `AuthProvider`, `Credentials` |
| Health | `health` | `ConnectorHealth`, `HealthStatus` |
| Normalization | `normalization` | `Normalizer`, `FieldMapper`, `ReasonCodeMap` |
| Exceptions | `exceptions` | `ConnectorError`, `SourceUnavailableError`, `ContractViolationError`, `MappingError`, `AuthenticationError` |

## 5. Public APIs

All 25 exports under the **coverage convention**:

- **[deep]** — taught in a §8 walkthrough with executed output, or in the §13
  extension example.
- **[ref]** — reference coverage: documented in the table below (every symbol
  named), plus the [API reference](../../api-reference/connectors.md).

**The contract, registry & resilience — [deep]**
: `FMSConnector`, `IngestionMode`, `ConnectorHealth`, `HealthStatus`, `CONNECTORS`,
  `register_connector`, `get_connector`, `CSVConnector`, `RestConnector`,
  `AuthProvider`, `Credentials`, `RetryPolicy`, `BackoffStrategy`

**Everything else — [ref]** — see the table.

### Reference coverage

| Group | Symbols (`[ref]`) | What / when |
|---|---|---|
| Other reference connectors | `ExcelConnector`, `GraphQLConnector`, `KafkaConnector`, `MqttConnector` | The remaining built-ins (spreadsheet, GraphQL API, and the two streaming sources) — each an `FMSConnector` registered in `CONNECTORS`, differing only in transport. |
| Normalization | `Normalizer`, `FieldMapper`, `ReasonCodeMap` | Translate one raw record → a canonical event, independently of live I/O: `FieldMapper` renames vendor fields; `ReasonCodeMap` maps a vendor code → `(ontology.DelayCategory, reason)`; `Normalizer` is the ABC combining them. |
| Exceptions | `ConnectorError`, `SourceUnavailableError`, `ContractViolationError`, `MappingError`, `AuthenticationError` | Root + the four categories: unreachable source (the default *retryable* type), a failed contract test, an unmappable record, an auth failure. All derive from `core.MineProductivityError`. |

## 6. Conceptual model

Five ideas explain the package.

**A. One small contract.** `FMSConnector` has six `get_*_data(since, until)`
methods; only `get_cycle_data` and `get_delay_data` are abstract (AD-CN-01), the
rest default to yielding nothing. Every method **must be lazy** (a generator) so
the same connector handles a 200-row test file or a 50-million-row shift export.

**B. Connectors are registered, discoverable types.** `CONNECTORS` is a registry
(Tutorial 4); the six reference connectors register on import, and a plugin adds
its own with `@register_connector`. `get_connector(name)` returns the class.

**C. Normalization is separate from I/O.** `FieldMapper`/`ReasonCodeMap`/`Normalizer`
translate a raw record into a canonical event *without any live connection*, so
mapping logic is unit-testable on its own and the reason-code map — "the hardest
part of a real connector" — is a governed, comparable artifact.

**D. Resilience is shared, not per-vendor.** `RetryPolicy` (with `BackoffStrategy`)
and `AuthProvider` are one implementation every network connector reuses — retry on
a transient error, refresh on a 401 — so there is one thing to test and trust.

**E. Health is observable.** Every connector reports a `ConnectorHealth`
(`HealthStatus` HEALTHY/DEGRADED/UNHEALTHY/UNKNOWN), updated after a pull, so an
operations dashboard can see a failing feed before the KPIs go quiet.

## 7. Real mining examples

The walkthroughs ingest a real shift's data three ways: a **CSV export** of cycle
and delay events, a **REST API** with pagination that throws a 401 and a transient
503, and a custom **in-memory dispatch log** (§13). The canonical output is always
the same `events.CycleEvent`s — the whole point of the boundary.

## 8. Step-by-step walkthroughs

### 8.1 CSV ingestion, end to end

A connector is looked up from `CONNECTORS` by name, constructed, and asked to
`get_cycle_data(since, until)` — which yields canonical `CycleEvent`s, never raw
rows. Those flow straight into the `EventValidator` → `EventStore` → query pipeline
of Tutorial 3. Running
[`01_csv_ingestion.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/connectors/01_csv_ingestion.py):

```text
--- 1. Every reference connector is registered by default ---
"csv" in CONNECTORS: True
registered connectors: ['csv', 'excel', 'graphql', 'kafka', 'mqtt', 'rest']

--- 2. Look up and construct a connector by name ---

--- 3. Pull canonical events -- the connector never exposes raw CSV rows ---
4 cycle events | first payload_t: 220.0

--- 4. health_check() reports HEALTHY after a successful pull ---
HealthStatus.HEALTHY

--- 5. Contextually validate, envelope, and durably append each event ---
appended 4 events, confidence of the last: 1.0

--- 6. Query it back, scoped by equipment ---
HT-214: 2 event(s), payloads: [220.0, 221.0]
```

Sections 3→6 are the platform's data-flow made concrete: a CSV file becomes
governed, queryable, confidence-scored events — and the CSV-ness stops at the
connector.

### 8.2 Resilient network ingestion: retry and auth-refresh

A `RestConnector` is configured with an `AuthProvider` and a `RetryPolicy`
(`BackoffStrategy.EXPONENTIAL`). Against a real local server that returns a 401
(stale token) then a transient 503, the connector refreshes its token once and
retries the 503 automatically — and still ingests every event. Running
[`02_rest_with_retry.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/connectors/02_rest_with_retry.py):

```text
--- Demo server running at http://127.0.0.1:62427 ---

--- 1. AuthProvider + RetryPolicy configuration ---

--- 2. First request gets a 401 (stale token); AuthProvider.refresh() is called once ---
--- 3. Page 1's first attempt gets a transient 503; RetryPolicy retries automatically ---

--- 4. Result: 2 events ingested despite the 401 and the transient 503 ---
health_check(): HealthStatus.HEALTHY
```

(The server port is random per run — the URL will differ.) The resilience is not in
the `RestConnector`'s vendor logic; it is in the shared `RetryPolicy`/`AuthProvider`
every network connector reuses, so a new REST integration inherits it for free.

## 9. Repository example reuse

Two scripts were reused; the third (`03_custom_connector.py`, the §13 extension) was
**authored for this tutorial** — connectors had no custom-connector example — and
added to the shared lesson-execution smoke test. All three executed (exit `0`).

| Script | Public API it exercises | Walkthrough |
|---|---|---|
| [`01_csv_ingestion.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/connectors/01_csv_ingestion.py) | `CONNECTORS`, `CSVConnector`, `get_connector`, `ConnectorHealth`, `HealthStatus` | §8.1 |
| [`02_rest_with_retry.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/connectors/02_rest_with_retry.py) | `RestConnector`, `RetryPolicy`, `BackoffStrategy`, `AuthProvider` | §8.2 |
| [`03_custom_connector.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/connectors/03_custom_connector.py) | `FMSConnector`, `IngestionMode`, `register_connector` | §13 |

## 10. Common mistakes

| Mistake | What happens | Do this instead |
|---|---|---|
| Returning a materialized `list` from `get_*_data` | Breaks on a 50-million-row export; fails the contract suite | Yield lazily (a generator) |
| Exposing raw source records to callers | Mapping bugs smear across every downstream KPI | Normalize at the boundary; yield canonical events only |
| Re-implementing retry/auth per vendor | N untested copies of a subtle concern | Reuse `RetryPolicy` / `AuthProvider` |
| Inventing a local delay-reason enum | Delays stop being comparable across sites | Map to `ontology.DelayCategory` via `ReasonCodeMap` |
| Yielding events outside `[since, until)` | Double-counting on the next window | Honor the half-open window |
| Making `AuthProvider.refresh()` non-thread-safe | Concurrent 401s acquire duplicate tokens | `refresh()` must be concurrency-safe (design spec §24) |
| Skipping `@register_connector` on a new connector | It's invisible to `CONNECTORS`/`get_connector` | Register it (add-only, Tutorial 4) |

## 11. Best practices

- **Implement only what your source has.** Override `get_cycle_data`/`get_delay_data`
  (and any of the other four you can supply); leave the rest as the no-op default.
- **Yield lazily**, always — the contract's one hard rule.
- **Put the reason-code map in a `ReasonCodeMap`** keyed to `ontology.DelayCategory`;
  it is the highest-leverage artifact in a real connector.
- **Reuse the shared resilience** (`RetryPolicy`, `AuthProvider`); don't roll your own.
- **Report real health** in `health_check()` so a dead feed is visible early.
- **Register with `@register_connector`** and ship your connector as a plugin.

## 12. Performance considerations

- **Laziness is the performance contract.** A generator streams a 50M-row export at
  constant memory; a `list` would not. `provided_event_types()` lets tooling report a
  connector's capabilities *without instantiating* it.
- **`RetryPolicy.compute_delay` is O(1)**; `EXPONENTIAL_JITTER` spreads retries to
  avoid a thundering herd. Injectable `sleep_fn`/`jitter_fn` keep unit tests instant.
- **`CONNECTORS` lookups are O(1)** (a registry dict, Tutorial 4).
- **Normalization is pure and connection-free**, so it parallelizes and unit-tests
  trivially, off the critical I/O path.

## 13. Extension points — implement a connector for a new source

`connectors`' extension point is the whole package's reason for being: **subclass
`FMSConnector`, implement `get_cycle_data`/`get_delay_data` as lazy generators of
canonical events, and register with `@register_connector`.** The new source then
behaves exactly like a built-in. The example below (a self-contained in-memory
dispatch log) was executed and passes `ruff` / `ruff format --check` /
`mypy --strict`:

```python
from collections.abc import Iterable
from datetime import datetime
from typing import ClassVar

from mineproductivity.connectors import (
    ConnectorHealth, FMSConnector, HealthStatus, IngestionMode, register_connector,
)
from mineproductivity.events import CycleEvent, DelayEvent


@register_connector
class DispatchLogConnector(FMSConnector):
    name: ClassVar[str] = "dispatch_log"
    supported_modes: ClassVar[tuple[IngestionMode, ...]] = (
        IngestionMode.BATCH, IngestionMode.INCREMENTAL,
    )

    def __init__(self, *, shift_id: str) -> None:
        self._shift_id = shift_id
        self._pulled = False

    def get_cycle_data(self, since: datetime, until: datetime) -> Iterable[CycleEvent]:
        for record in _DISPATCH_LOG:                 # a lazy generator...
            if since <= record.event_time < until:   # ...honoring [since, until)
                yield CycleEvent(equipment_id=record.equipment_id, shift_id=self._shift_id, ...)
        self._pulled = True

    def get_delay_data(self, since: datetime, until: datetime) -> Iterable[DelayEvent]:
        return iter(())                              # this source has no delay telemetry

    def health_check(self) -> ConnectorHealth:
        return ConnectorHealth(status=HealthStatus.HEALTHY if self._pulled else HealthStatus.UNKNOWN)
```

Exercising it — the custom connector registers itself, is discoverable by name, and
yields the same canonical events as any built-in:

```text
--- 1. The custom connector registered itself alongside the built-ins ---
"dispatch_log" in CONNECTORS: True
registered connectors: ['csv', 'dispatch_log', 'excel', 'graphql', 'kafka', 'mqtt', 'rest']

--- 2. Discoverable by name via get_connector(), like any built-in ---
get_connector('dispatch_log') is DispatchLogConnector: True
provided_event_types(): ('cycle', 'delay')

--- 3. It yields the SAME canonical events every connector does ---
pulled 2 cycle events in [06:00, 07:00): payloads=[220.0, 218.0]
health after pull: HealthStatus.HEALTHY
```

Two further surfaces use the same idiom: a **custom `Normalizer`** (implement
`normalize_cycle`/`normalize_delay` with a `FieldMapper` + `ReasonCodeMap`) to keep
mapping testable off the I/O path, and a **custom `AuthProvider`** for a source with
an unusual token flow. Ship the whole thing as a plugin (Tutorial 4) and it installs
into `CONNECTORS` with no change to any layer above.

!!! note "Reference implementations are private"
    `connectors` ships six *public* reference connectors, but the reference
    `AuthProvider` (`_StaticAuthProvider`) is private, as is `events`'
    `_InMemoryEventStore`. Public connectors are meant to be used; the private auth
    reference is a test/example stand-in — implement `AuthProvider` for production.

## 14. Exercises

1. **Implement a connector.** Following §13, write a `WeighbridgeConnector` over an
   in-memory list of weigh records, yielding `CycleEvent`s lazily and honoring
   `[since, until)`. Register it and confirm it appears in `sorted(CONNECTORS)`.
2. **Map a reason code.** Build a `ReasonCodeMap` for a fictional vendor mapping two
   codes to `ontology.DelayCategory` values, and show `resolve()` returns a `Maybe`
   (some for a known code, nothing for an unknown one).
3. **Configure retry.** Construct three `RetryPolicy`s (`FIXED`, `EXPONENTIAL`,
   `EXPONENTIAL_JITTER`) and compare `compute_delay(1)`/`compute_delay(2)`/`compute_delay(3)`.
   Why does jitter matter when 500 trucks reconnect at once after an outage?
4. **Rename fields.** Use a `FieldMapper` to rename a vendor's `TruckID`/`Tonnes` to
   `equipment_id`/`payload_t`, and confirm unmapped keys pass through unchanged.
5. **Prove laziness.** Give your §13 connector a source of 1,000,000 records but pull a
   1-hour window; confirm only the in-window events are produced and that construction
   did not read the whole source.

## 15. Reference solutions

??? success "Solution 1 — Implement a connector"
    ```python
    @register_connector
    class WeighbridgeConnector(FMSConnector):
        name: ClassVar[str] = "weighbridge"
        def __init__(self, *, shift_id: str) -> None:
            self._shift_id = shift_id
        def get_cycle_data(self, since, until):
            for r in _WEIGHS:
                if since <= r.event_time < until:
                    yield CycleEvent(equipment_id=r.equipment_id, shift_id=self._shift_id,
                                     queue_min=0, spot_min=0, load_min=0, haul_min=0,
                                     dump_min=0, return_min=0, payload_t=r.tonnes)
        def get_delay_data(self, since, until):
            return iter(())
    "weighbridge" in sorted(CONNECTORS)   # True
    ```

??? success "Solution 2 — Map a reason code"
    ```python
    from mineproductivity.ontology import DelayCategory
    m = ReasonCodeMap(vendor_name="acme", mapping={
        "MECH": (DelayCategory.EQUIPMENT, "mechanical failure"),
        "WX":   (DelayCategory.WEATHER, "rain"),
    })
    m.resolve("MECH").unwrap()      # (DelayCategory.EQUIPMENT, 'mechanical failure')
    m.resolve("NOPE").is_nothing    # True
    ```

??? success "Solution 3 — Configure retry"
    ```python
    RetryPolicy(backoff=BackoffStrategy.FIXED, base_delay_s=1.0).compute_delay(3)        # 1.0
    RetryPolicy(backoff=BackoffStrategy.EXPONENTIAL, base_delay_s=1.0).compute_delay(3)  # 4.0
    # EXPONENTIAL_JITTER multiplies by 0.5 + random(), spreading reconnects so 500
    # trucks don't all retry on the same tick (a thundering herd on your API).
    ```

??? success "Solution 4 — Rename fields"
    ```python
    FieldMapper(mapping={"TruckID": "equipment_id", "Tonnes": "payload_t"}).apply(
        {"TruckID": "HT-214", "Tonnes": 220.0, "Note": "ok"}
    )   # {'equipment_id': 'HT-214', 'payload_t': 220.0, 'Note': 'ok'}  -- 'Note' passes through
    ```

??? success "Solution 5 — Prove laziness"
    Because `get_cycle_data` is a generator, `DispatchLogConnector(...)` reads nothing
    at construction; iterating with a 1-hour `[since, until)` yields only in-window
    events and stops. A `list(...)`-returning implementation would have to build all
    1,000,000 in memory first — which is exactly what the contract forbids.

## 16. Further reading

- **[`connectors` package guide](../../packages/connectors.md)** — the capability-tour view.
- **[`connectors` API reference](../../api-reference/connectors.md)** — every symbol, from source.
- **[Connector Framework Design Specification](../../architecture/04_Connector_Framework_Design_Specification.md)** — AD-CN-01 (two abstract methods), AD-CN-02 (normalization separate from I/O), AD-CN-05 (shared retry), the contract test suite.
- **Package Tutorials [1 — Core](01_core.md) · [2 — Ontology](02_ontology.md) · [3 — Events](03_events.md) · [4 — Registry & Plugins](04_registry_and_plugins.md)** — the four layers connectors unites.

---

**Next package tutorial:** KPIs (deep) — the metadata-first metric backbone that
measures the events a connector ingested. It opens Unit B (Intelligence).
*(Not yet written — Tutorial 6 of 13.)*
