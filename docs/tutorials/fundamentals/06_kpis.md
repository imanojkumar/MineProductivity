# Lesson 06 - KPIs

## Objective

Understand a KPI as a **governed object** carrying its own formula, unit, and aggregation rule - and meet the guardrail that prevents the most expensive mistake in mining reporting: averaging a ratio.

## Prerequisites

- [Lesson 04 - Events](04_events.md) (the facts a KPI consumes)
- [Lesson 05 - Ontology](05_ontology.md) (what those facts are about)

## Concepts covered

| Concept | Why it exists |
|---|---|
| `meta` - the governed schema | `official_name`, `operational_question`, `formula`, `unit`, `direction`, `required_events`, `dependencies`, `aggregation`. Everything needed to *trust* a number without reading its source. |
| Leaf vs `CompositeKPI` | Some KPIs are measured; some are derived from others. |
| `DependencyGraph` | A composite declares dependencies; the graph resolves execution order. Cycles are rejected at registration. |
| `Aggregation` | **How** a KPI may legally be combined. This is a governed field, not the caller's choice. |
| `KPIAggregationError` | The structural guardrail against averaging ratios. |

## Complete runnable example

**[:material-file-code: `examples/fundamentals/06_kpis/kpis.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/fundamentals/06_kpis/kpis.py)**

```bash
python examples/fundamentals/06_kpis/kpis.py
```

The moment that matters - the framework refusing to let you be wrong:

```python
from mineproductivity.kpis import REGISTRY, Aggregation
from mineproductivity.kpis.aggregation import combine_results   # NOT a top-level export
from mineproductivity.kpis.exceptions import KPIAggregationError

# A-shift: 15,600 t in 12 h. B-shift: 6,600 t in 6 h.
tph = REGISTRY.get("PROD.TPH")()
a_rows = [{"payload_t": 15_600.0, "operating_h": 12.0}]   # -> 1,300 t/h
b_rows = [{"payload_t": 6_600.0,  "operating_h": 6.0}]    # -> 1,100 t/h

try:
    combine_results([tph.compute(a_rows), tph.compute(b_rows)],
                    Aggregation.RATIO, code="PROD.TPH", unit="t/h")
except KPIAggregationError as exc:
    print(exc)   # ratio KPIs cannot be combined by averaging already-computed results

# The only correct answer: re-derive from the union of the raw rows.
correct = tph.compute([*a_rows, *b_rows])   # 1,233.3 t/h
```

## Expected output

```text
--- 1. A KPI describes itself: governed metadata, machine-readable ---
PROD.TPH -- Tonnes Per Hour  [leaf, aggregation=ratio]
  question : At what rate is this asset producing material?
  formula  : sum(payload_t) / sum(operating_h)
  unit     : t/h  (direction: higher_is_better)
  needs    : CYCLE

--- 2. Compute it: one CAT 793F's shift -- 40 cycles of 220 t ---
PROD.TPH = 733.33 t/h (n=40 cycles)

--- 3. A composite KPI declares dependencies; the graph resolves them ---
UTIL.OEE -- Overall Equipment Effectiveness  [composite, aggregation=derived]
  question : Overall, how effectively was this asset's scheduled time converted to output?
  formula  : UTIL.PA * UTIL.UA * UTIL.Performance
  unit     : ratio  (direction: higher_is_better)
  needs    : MAINTENANCE, PRODUCTION
  depends  : UTIL.PA, UTIL.UA, UTIL.Performance
  resolution order: UTIL.PA -> UTIL.UA -> UTIL.Performance -> UTIL.OEE
  (the engine computes each leaf first, then combines -- you never
   wire this by hand, and a cycle is rejected at registration time)

--- 4. Why aggregation is a governed field: NEVER average a ratio ---
  A-shift: 1,300 t/h over 12 h
  B-shift: 1,100 t/h over 6 h
  naive mean of the two rates : 1,200.0 t/h   <-- WRONG

  The framework refuses to make that mistake for you:
    KPIAggregationError: PROD.TPH: ratio KPIs cannot be combined by averaging already-computed results -- re-derive from the union of raw rows instead

  The only correct answer re-derives from the union of the raw rows:
    PROD.TPH over both shifts = 1,233.3 t/h   <-- correct
  (22,200 t moved in 18 h. The naive average over-reports by ~2.5%
   because it forgets the shifts were different lengths.)

--- 5. The rule is structural, not advisory ---
  ADDITIVE tonnes DO combine by summing: 22,200 t
  each KPI declares its own rule: PROD.TPH -> ratio
  (you cannot 'accidentally' average a RATIO -- the metadata decides,
   not the caller's convenience. The error above is the guardrail.)

--- 6. The Standard Library is discoverable and self-documenting ---
  12 KPIs registered; composite ones: ['UTIL.OEE']
  (see examples/kpis/ for full KPIEngine execution over an event store)
```

## Explanation

### The ratio trap - worth reading twice

This is the most important paragraph in the Fundamentals suite.

A-shift ran **12 hours at 1,300 t/h**. B-shift ran **6 hours at 1,100 t/h**. What was the day's tonnes per hour?

The instinctive answer - average them - gives **1,200 t/h**. It is wrong. The day moved `12 × 1,300 + 6 × 1,100 = 22,200 t` in `18 h`, so the rate is `22,200 / 18 = ` **1,233.3 t/h**. The naive average silently over-reports by ~2.5% because it forgets the shifts were different lengths.

At a 40 Mt/a operation, a systematic 2.5% error in reported rate is tens of thousands of tonnes of phantom production per year - the kind of number that survives into a board pack and a reserve statement.

**What the framework does about it is the lesson.** It does not warn. It does not compute a weighted mean and hope you noticed. It **raises `KPIAggregationError` and refuses**, telling you to re-derive from the union of the raw rows. There is no "convenience" path to the wrong answer.

Contrast section 5: `PROD.Tonnes` is `ADDITIVE`, so it *does* combine by summing - 22,200 t, exactly as you would expect. The difference is not the caller's judgement; it is the KPI's own declared `aggregation` field. Metadata decides.

### Why "metadata-first" is not bureaucracy

Section 1 prints everything a reviewer needs: the operational question the KPI answers, the formula, the unit, the direction, and which events it requires. None of that came from a wiki that drifted; it is attached to the object and versioned with it. That is what "self-describing" buys you.

### Composites and the dependency graph

`UTIL.OEE = UTIL.PA × UTIL.UA × UTIL.Performance`. You never wire that by hand. `DependencyGraph(REGISTRY).topological_order("UTIL.OEE")` returns the execution order, and the `KPIEngine` walks it - computing each leaf first, then combining. A dependency cycle is rejected *at registration time*, not discovered at 3 a.m.

Note `UTIL.OEE` is `DERIVED` and needs the **engine** to resolve its dependencies; it is not computable via a bare `.compute(rows)`. See [`examples/kpis/02_composite_oee.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/kpis/02_composite_oee.py) for engine execution over a real event store.

## Best practices

- **Read `meta.aggregation` before combining anything.** It tells you what is legal.
- **To roll a ratio up, re-derive from raw rows** - never post-process computed results.
- **Let `DependencyGraph` resolve composites.** Never hand-order `PA → UA → Performance`.
- **Use the engine for anything scoped to a shift/window** ([`_dataset.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/kpis/_dataset.py) shows the canonical wiring).
- **Treat `KPIAggregationError` as a design message**, not an obstacle to route around.

## Common mistakes

| Mistake | What happens | Do this instead |
|---|---|---|
| **Averaging a ratio across shifts** | Silently wrong by a few percent - forever, and in the board pack | Re-derive: `tph.compute([*a_rows, *b_rows])` |
| `from mineproductivity.kpis import combine_results` | `ImportError` - it is **not** a top-level export | `from mineproductivity.kpis.aggregation import combine_results` |
| Expecting `combine_results(RATIO)` to return a weighted mean | It **raises**. It does not silently do the right thing for you | Catch it, then re-derive from raw rows |
| Calling `.compute()` on `UTIL.OEE` | A composite needs its dependencies resolved | Use the `KPIEngine` |
| Weighting by row count instead of hours | Still wrong - the weight is *operating hours*, not number of rows | Re-derive from raw rows and let the formula weight correctly |

!!! danger "The guardrail is the feature"
    This lesson's first draft *assumed* `combine_results(..., RATIO, ...)` would return the correct weighted mean. It does not - it raises. The framework is stricter than expected, and that strictness is the whole point: there is no accidental path to 1,200 t/h.

## Exercises

1. **Feel the error.** Compute the 1,200 vs 1,233.3 difference for a 40 Mt/a operation. How many phantom tonnes per year does the naive average invent?
2. **Find every ratio.** Iterate `REGISTRY` and print each KPI's `meta.aggregation`. Which are `RATIO`? Those are the ones you can never average.
3. **Try to cheat.** Attempt `combine_results` with `Aggregation.AVERAGE` on two `PROD.TPH` results. Does it work? *Should* it? What does your answer say about where domain rules belong?
4. **Trace a composite.** Print `DependencyGraph(REGISTRY).topological_order("UTIL.OEE")`. Now read `UTIL.OEE`'s `meta.formula`. Why must `PA` compute before `OEE`?
5. **Run the real engine.** Work through [`examples/kpis/01_simple_execution.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/kpis/01_simple_execution.py) to see `PROD.TPH` scoped to a shift over a real event store.

## Suggested next lesson

**[Lesson 07 - Analytics](07_analytics.md)** - you can measure the rate. Now answer the question a superintendent actually asks next: *is it drifting?*

---

**See also:** [`kpis` API Reference](../../api-reference/kpis.md) · [`kpis` package guide](../../packages/kpis.md) · [KPI Engine design specification](../../architecture/05_KPI_Engine_Design_Specification.md)
