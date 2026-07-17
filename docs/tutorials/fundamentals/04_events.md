# Lesson 04 - Events

## Objective

Record haul cycles as immutable facts, query them back, and **travel in time** - proving that a report run today for last June still reconciles with the report that was run last June.

## Prerequisites

- [Lesson 02 - Entities](02_entities.md) and [Lesson 03 - Value objects](03_value_objects.md)

## Concepts covered

| Concept | Why it exists |
|---|---|
| Canonical events (`CycleEvent`, …) | A typed fact with domain behaviour - a cycle knows how to sum its own six legs. |
| `EventEnvelope` | Identity, version, and **three timestamps**: when it happened, when it reached us, when we computed on it. |
| Append-only `EventStore` | Facts are never updated. A correction is a *new event*. |
| `EventValidator` | Scores **confidence**; it does not silently discard data. |
| `AsOf` + `replay` | Reconstruct exactly what was true at any moment. |

## Complete runnable example

**[:material-file-code: `examples/fundamentals/04_events/events.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/fundamentals/04_events/events.py)**

```bash
python examples/fundamentals/04_events/events.py
```

The three timestamps are not bureaucracy - they are how you tell "the truck hauled at 06:14" from "we found out at 09:00":

```python
EventEnvelope(
    event_id=EventID.generate(),
    version=EventVersion(),
    payload=cycle,
    event_time_utc=moment,       # when it happened in the pit
    processing_time_utc=moment,  # when we computed on it
    ingestion_time_utc=moment,   # when it reached us
    metadata=EventMetadata(name="haul-cycle", source_system="fms"),
)
```

## Expected output

```text
--- 1. A canonical event is a typed fact, with domain behaviour ---
cycle_min : 19.5 (the six legs, summed by the event itself)
duration_h: 0.325

--- 2. Validation scores confidence; it does not silently drop data ---
is_valid=True confidence=1.0

--- 3. Append-only: the store accepts facts, it never updates them ---
5 cycle events appended (4 for HT-214, 1 for HT-9)

--- 4. Query the facts back by scope ---
HT-214 moved 875t across 4 cycles

--- 5. Time travel: what was true as of 06:18? ---
as of 06:18 HT-214 had moved 875t (4 events visible)
(the same query, run later, still reproduces this number exactly)

--- 6. A correction is a NEW event, never an edit ---
HT-214 now has 5 events totalling 1103t
(the original 220.0t fact still exists -- nothing was overwritten)

--- 7. The proof: the past did not change when the present did ---
  as of 06:18 : 875t across 4 cycles  (unchanged)
  as of now   : 1103t across 5 cycles
Re-running the SAME as-of query after the correction returns the SAME
number. That is reproducibility: a report run today for last June
still reconciles with the report that was run last June.
```

## Explanation

**A shift report is an opinion. A haul cycle that happened at 06:14 is a fact.**

MineProductivity keeps the facts and treats everything else - KPIs, twins, dashboards - as a *projection* of them. That single decision is what makes the rest of the platform trustworthy.

**Why append-only?** Because the alternative destroys your audit. Suppose the FMS reported 220 t and the weightometer later says it was really 228 t. The tempting move is to update the row. Do that, and last month's production report can never be reproduced - the number it was based on no longer exists. Your auditor asks "why did June change?" and nobody can answer.

Instead, the correction is a **new event** (section 6). The original 220 t fact still exists. Section 7 is the payoff: replaying `AsOf(06:18)` *after* the correction still returns **875 t**, while "now" returns **1103 t**. The past did not move when the present did.

**Why three timestamps?** Mining data arrives late and out of order. A truck hauls at 06:14 (`event_time_utc`); the FMS batch uploads at 09:00 (`ingestion_time_utc`); your KPI job runs at 09:05 (`processing_time_utc`). If you only kept one timestamp you could not answer "what did we *know* at 07:00?" - which is exactly the question an incident review asks.

**Why score confidence instead of rejecting?** Real pit data is messy. A validator that silently drops a suspicious cycle produces a tidy, wrong number. `validate_with_confidence` keeps the fact and attaches a confidence score, letting the layers above decide. Qualify, don't coerce - a theme you will meet again in Lesson 10.

## Best practices

- **Never update a fact.** Append a correcting event. Always.
- **Set `event_time_utc` to when it happened in the pit** - not when your script ran. Getting this wrong silently corrupts every time-based KPI.
- **Everything UTC.** A 2×12 roster crossing a DST boundary will find any local-time assumption.
- **Use `AsOf` for any historical report.** Do not filter `>= start and < end` by hand; `replay` exists for this.
- **Check `append(...).is_ok`.** It returns a `Result`, not an exception.

## Common mistakes

| Mistake | What happens | Do this instead |
|---|---|---|
| Editing an event to "fix" it | Historical reports become irreproducible; the audit trail is destroyed | Append a new, correcting event |
| Using ingestion time as event time | Late-arriving data lands in the wrong shift and your TPH is wrong for both | Set `event_time_utc` to the pit reality |
| Naive (tz-less) datetimes | Silent hour shifts across DST and site timezones | Always `tzinfo=timezone.utc` |
| Dropping "bad" data at validation | A tidy number that is quietly wrong | `validate_with_confidence` and let the caller decide |
| Ignoring the `Result` from `append` | Silent failures | `assert store.append(env).is_ok` |

!!! note "Why the correction still reads 875 t as of 06:18"
    The correcting event was appended with an `event_time_utc` of minute 60 - *after* the 06:18 cut-off. `replay(AsOf(06:18))` therefore cannot see it. That is not a quirk; it is the definition of a point-in-time query.

## Exercises

1. **Prove irreproducibility is prevented.** Add a second correction at minute 90, then re-run the `AsOf(06:18)` replay. Does the historical number move? Why not?
2. **Ask a different question.** Replay `AsOf` at minute 16 instead of 18. How many events are visible, and how many tonnes? Explain the difference from first principles.
3. **Late arrival.** Append a cycle whose `event_time_utc` is minute 15 but whose `ingestion_time_utc` is minute 300 (it arrived late). Does `AsOf(06:18)` see it? Should a report run at 06:18 have seen it? What does that tell you about which timestamp `replay` uses?
4. **Model a delay.** Look up `DelayEvent` in the [`events` API Reference](../../api-reference/events.md) and append one for a crusher blockage. Which KPIs would consume it?

## Suggested next lesson

**[Lesson 05 - Ontology](05_ontology.md)** - you now have facts. But a fact about *what*? The ontology is the shared vocabulary that makes a tonne at one pit mean the same as a tonne at another.

---

**See also:** [`events` API Reference](../../api-reference/events.md) · [`events` package guide](../../packages/events.md) · [Event Framework design specification](../../architecture/01_Event_Framework_Design_Specification.md) · [`events` replay demo](https://github.com/imanojkumar/MineProductivity/blob/main/examples/events/02_replay.py)
