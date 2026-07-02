# Examples — mineproductivity.events

## Purpose

Runnable, minimal, self-contained scripts demonstrating the Event Framework: constructing and validating canonical events, appending them to a store, querying, and time-travelling through replay.

## Scope

Example scripts and their direct output. No test assertions live here (see `tests/unit/events/` and `tests/integration/test_events_pipeline.py` for that); each script is meant to be read and run by a human evaluating the package.

## Responsibilities

- Show idiomatic usage of the Event Framework's public API.
- Serve as executable documentation that stays correct because it is actually run.

## Contents

- `01_first_event.py` — construct a `CycleEvent`, wrap it in an `EventEnvelope`, validate it, and append it to an `EventStore`.
- `02_replay.py` — append several events across a shift and reconstruct the store's state at an earlier point in time via `replay()`.
- `03_correction.py` — append an event, then append a correction under the same `EventID` with an incremented `EventVersion`, and show both the current and historical views.

## Dependencies

Only `mineproductivity` itself (editable-installed from this repository). No third-party packages.

## Running the Examples

```bash
pip install -e .
python examples/events/01_first_event.py
python examples/events/02_replay.py
python examples/events/03_correction.py
```

Each script exits `0` and prints its own output; there is nothing to configure.

## Future Work

Add an example demonstrating the `EventBus` publish/subscribe path once a downstream consumer package (e.g. a future `digital_twin`) exists to motivate a realistic subscriber.

## References

- Reference Implementation Blueprint v1.0
- [`docs/architecture/01_Event_Framework_Design_Specification.md`](../../docs/architecture/01_Event_Framework_Design_Specification.md)
- [`src/mineproductivity/events/README.md`](../../src/mineproductivity/events/README.md)
