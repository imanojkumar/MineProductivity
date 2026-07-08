# Examples — mineproductivity.digital_twin

## Purpose

Runnable, minimal, self-contained scripts demonstrating the Digital Twin package: cold-start reconstruction from event history plus live event-driven synchronization, category/scope discovery over a twin repository, point-in-time snapshots with generic serialization, and third-party twin-type plugins.

## Scope

Example scripts and their direct output. No test assertions live here (see `tests/unit/digital_twin/` for that); each script is meant to be read and run by a human evaluating the package.

## Responsibilities

- Show idiomatic usage of the Digital Twin public API.
- Serve as executable documentation that stays correct because it is actually run.
- Demonstrate the §3.3 discipline end-to-end: every state change produces a new `Twin` instance via `with_state()`; twin state is always a projection of the immutable event log, never a side channel.

## Contents

- `01_provision_and_sync.py` — the design spec §15 worked example, end-to-end: a `ConveyorTwin` cold-started from genesis via `EventStore.replay`, provisioned into a `TwinRepository` (`core.InMemoryRepository`, unchanged), then kept live via `EventBus.subscribe(sync_policy.event_filter, handler)` — including the store→bus wiring, `SyncPolicy` event narrowing, and proof the pre-sync instance is never mutated.
- `02_discovery.py` — `by_category`/`by_scope` composed lookups (`&`, `~`) over a populated repository; a filter matching nothing returns an empty sequence, never raises.
- `03_snapshot_and_serialize.py` — `TwinSnapshot` capture (reusing `events.AsOf`), a `core.serialization` round-trip reproducing state/status/as_of exactly, and a scenario-`AsOf` fork — the hook a future `TwinSimulationModel` implementer consumes.
- `04_plugin_twin_type.py` — a third-party-style `Twin` type registered via entry points (`EntryPointSpec(group="mineproductivity.digital_twin", target_registry="digital_twin")`, design spec §28), mirroring `examples/registry/01_register_and_discover.py`'s real-discovery pattern; also shows the package ships zero built-in twin types.

## Dependencies

`mineproductivity`, editable-installed from this repository (`pip install -e .`). No network access; every event is constructed in-script.

## Running the Examples

```bash
pip install -e .
python examples/digital_twin/01_provision_and_sync.py
python examples/digital_twin/02_discovery.py
python examples/digital_twin/03_snapshot_and_serialize.py
python examples/digital_twin/04_plugin_twin_type.py
```

Each script exits `0` and prints its own output; there is nothing to configure.

## Future Work

Add a concrete `TwinSimulationModel` walkthrough once a first-party or third-party plugin implementing that interface-only extension point exists (deliberately never shipped inside `digital_twin` itself, design spec §14, ADR-0008).

## References

- [`docs/architecture/08_Digital_Twin_Design_Specification.md`](../../docs/architecture/08_Digital_Twin_Design_Specification.md) §9, §13, §15, §18–§20, §28
- [`src/mineproductivity/digital_twin/README.md`](../../src/mineproductivity/digital_twin/README.md)
- [`docs/adr/ADR-0008-Digital-Twin.md`](../../docs/adr/ADR-0008-Digital-Twin.md)
