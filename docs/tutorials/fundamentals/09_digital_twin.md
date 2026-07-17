# Lesson 09 - Digital Twin

## Objective

Build a ROM stockpile twin whose state is **always a projection of the event log** - cold-start it from history, keep it live, and understand why the absence of a `set_tonnes()` method is the entire point.

## Prerequisites

- [Lesson 02 - Entities](02_entities.md) (identity that outlives state)
- [Lesson 04 - Events](04_events.md) (the log a twin projects from)

## Concepts covered

| Concept | Why it exists |
|---|---|
| `Twin` category bases | Eleven of them (`StockpileTwin`, `ConveyorTwin`, `FleetTwin`, …) matching `TwinCategory`. |
| `_apply(events, *, context)` | The **only** way state changes: fold events into a new `TwinState`. |
| Cold start via `replay` + `AsOf` | A twin lost to a restart is reconstructed exactly. |
| `TwinSynchronizer` + `EventBus` | Live updates as events land. |
| `TwinSnapshot` | Freezes "what was true" at a moment - what simulation/optimization seed from. |

## Complete runnable example

**[:material-file-code: `examples/fundamentals/09_digital_twin/digital_twin.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/fundamentals/09_digital_twin/digital_twin.py)**

```bash
python examples/fundamentals/09_digital_twin/digital_twin.py
```

Look at what this class does **not** have - there is no `add_tonnes()`:

```python
class RomStockpileTwin(StockpileTwin):
    meta: ClassVar[TwinMetadata] = TwinMetadata(
        code="STOCKPILE.RunOfMine",
        category=TwinCategory.STOCKPILE,
        description="A ROM stockpile twin projected from production events.",
    )

    def _apply(self, events: Sequence[BaseEvent], *, context: TwinContext) -> TwinState:
        tonnes = float(self.state.attributes.get("tonnes_on_pad", 0.0))
        tips = int(self.state.attributes.get("tips", 0))
        for event in events:
            if isinstance(event, ProductionEvent):
                tonnes += event.tonnes_moved
                tips += 1
        return TwinState(attributes={"tonnes_on_pad": tonnes, "tips": tips}, captured_at=...)
```

## Expected output

```text
--- 1. The event log already holds this shift's tips ---
4 production events appended (3 to ROM-01's trucks, 1 elsewhere)

--- 2. Cold start: rebuild the twin from history via replay ---
replayed 3 relevant events (applied=3) -> {'tonnes_on_pad': 663.0, 'tips': 3}
status: provisioned -> synchronized
(a twin lost to a restart is reconstructed EXACTLY -- no state was
 stored anywhere but the event log)

--- 3. Go live: the synchronizer folds in new events as they land ---
  synced: synchronized -> synchronized, events_applied=1
live state: {'tonnes_on_pad': 894.0, 'tips': 4}

--- 4. Immutability: the cold-start instance never changed ---
cold-start instance still reads: 663 t
repository instance now reads  : 894 t
but they are the SAME twin: twin == current -> True
(identity-based equality again -- ROM-01 is ROM-01; state changes
 produce new instances, exactly like the entity in lesson 02)

--- 5. A snapshot freezes 'what was true' at a point in time ---
snapshot of ROM-01 as_of 2026-06-25T08:00:00+00:00
  {'tonnes_on_pad': 894.0, 'tips': 4}
(this is what simulation and optimization seed from -- a real
 starting condition, not a hand-typed guess)

--- 6. Cancelled: later events no longer reach the twin ---
tips after cancel: 4
(the event is still in the log forever -- the twin simply stopped
 listening. History and projection are separate concerns.)
```

## Explanation

### A twin is not a dashboard

In most vendor decks a "digital twin" is a 3D model with live numbers on it. Here it is something stricter and far more useful: **an entity whose state is always a projection of the immutable event log**, never a side channel someone can write to.

Notice `RomStockpileTwin` has no `add_tonnes()`, no `set_state()`, no setter of any kind. The only way its state changes is by applying events. That constraint is the whole design.

### What the constraint buys you

**Cold start.** Section 2 rebuilds the twin from history: replay the log, fold the relevant events, get `663 t`. If the process dies, the twin is reconstructed *exactly* - because no state was ever stored anywhere except the event log. There is nothing to back up, nothing to corrupt, nothing to drift.

**Auditability.** Every tonne on that pad traces to a `ProductionEvent` that says which truck tipped it and when. Ask "why does ROM-01 say 894 t?" and the answer is four events, each with an id and three timestamps.

If state could be poked directly, *neither* property would hold. A single `stockpile.tonnes = 900` written by a well-meaning integration would make the twin unreconstructable and untraceable, forever.

### Identity again - Lesson 02 pays off

Section 4 is worth pausing on. The cold-start instance still reads 663 t; the repository instance reads 894 t; and `twin == current` is **True**.

This is exactly `BaseEntity` from Lesson 02. ROM-01 is ROM-01. State changes produce *new instances*, and identity-based equality means both instances are the same stockpile at different moments. The twin did not become a different stockpile when a truck tipped on it - just as HT-214 did not become a different truck when it burned diesel.

### Snapshots seed the layers above

A `TwinSnapshot` freezes state at an `AsOf` moment. This is what `simulation` and `optimization` consume as their starting condition - a *real*, evidence-backed state of the mine, rather than a hand-typed guess in a scenario file. That is the difference between "what if we add three trucks to a pad holding 894 t" and "what if we add three trucks to a pad holding, uh, roughly 900?"

### History and projection are separate

Section 6: after `subscription.cancel()`, a further event is appended and the twin's `tips` stays at 4. The event is still in the log **forever** - the twin simply stopped listening. The log is the truth; the twin is one projection of it. You can build a second twin tomorrow with different logic and replay the same history through it.

## Best practices

- **Never add a setter.** If you are tempted to write `twin.state.attributes["x"] = y`, the design is telling you something.
- **Keep `_apply` pure and total.** Fold events into a new state; handle the empty case (`if not events: return self.state`).
- **Filter with a `SyncPolicy`/specification** so a twin only sees the events it projects from.
- **Cold-start from `replay`** rather than persisting twin state separately.
- **Snapshot before seeding** simulation or optimization.
- **Cancel subscriptions** you no longer need.

## Common mistakes

| Mistake | What happens | Do this instead |
|---|---|---|
| Adding a direct state setter | The twin becomes unreconstructable and untraceable - the whole design collapses | Only `_apply` |
| Persisting twin state as the source of truth | It drifts from the log; cold start disagrees with live | Project from events |
| Forgetting the empty-events guard | Needless new state objects, wrong `captured_at` | `if not events: return self.state` |
| Not filtering events | HT-9's tips land on the wrong pad | Filter with a specification |
| **`snapshot.as_of.utc.isoformat()` unguarded** | `mypy --strict` error - `AsOf.utc` is `datetime \| None` | Narrow with an `assert` first |
| Bare `PredicateSpecification` variable | `mypy --strict`: "Need type annotation" | `x: PredicateSpecification[EventEnvelope[Any]] = ...` |

!!! note "Two `mypy --strict` traps in this lesson"
    Both were caught by the strict gate before this lesson was locked: `AsOf.utc` is optional and needs narrowing, and `PredicateSpecification` needs an explicit type parameter when bound to a bare variable. Neither shows up at runtime - only the type checker finds them.

## Exercises

1. **Prove cold start.** Build a *second* `RomStockpileTwin` from scratch and replay the same history. Does it reach the same state? Why is that guaranteed?
2. **Reproject.** Write a twin that tracks *average tonnes per tip* instead of the total, over the same events. Note you changed the projection without touching a single event - why is that powerful?
3. **Time-travel a twin.** Cold-start with `AsOf` set to minute 12. What is on the pad? Explain the difference from minute 60.
4. **Model a crusher.** Pick an appropriate category base from the eleven and project throughput from `ProductionEvent`s.
5. **Break it deliberately.** Add a `set_tonnes()` method. Now answer: how would you cold-start after a restart? How would you audit a tonne? That is the argument for the constraint.

## Suggested next lesson

**[Lesson 10 - Visualization](10_visualization.md)** - you have measured, characterised, decided, and represented. The last step: show a human, without the platform ever learning what a tonne is.

---

**See also:** [`digital_twin` API Reference](../../api-reference/digital_twin.md) · [`digital_twin` package guide](../../packages/digital_twin.md) · [Digital Twin design specification](../../architecture/08_Digital_Twin_Design_Specification.md)
