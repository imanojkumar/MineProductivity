# Lesson 01 - Hello, MineProductivity

## Objective

Confirm your install and compute a real mining KPI - a haul truck's tonnes-per-hour across a full shift - **without writing a single formula yourself**.

By the end you will understand the single idea the whole platform is built on: a KPI is a *governed object you look up*, not arithmetic you retype.

## Prerequisites

- Python 3.12+
- MineProductivity installed: `pip install mineproductivity`

No prior lesson required. This is the entry point.

## Concepts covered

| Concept | Why it exists |
|---|---|
| `kpis.REGISTRY` | A discoverable catalogue of every governed KPI. You resolve `"PROD.TPH"` by code, so two engineers cannot silently mean two different things. |
| `KPIResult` | A measurement carries **provenance** - code, unit, row count, warnings - not just a float. |
| Governed identifiers | `PROD.TPH` is a contract. The formula, unit, and validity rules live inside the object. |

## Complete runnable example

**[:material-file-code: `examples/fundamentals/01_hello_mineproductivity/hello.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/fundamentals/01_hello_mineproductivity/hello.py)**

```bash
python examples/fundamentals/01_hello_mineproductivity/hello.py
```

The heart of it:

```python
from mineproductivity.kpis import REGISTRY

# Look the KPI up by its governed code -- never retype the formula.
tph = REGISTRY.get("PROD.TPH")()

# One CAT 793F's shift: ~220 t per load, ~18 min (0.3 h) per cycle, 40 cycles.
cycles = [{"payload_t": 220.0, "operating_h": 0.3} for _ in range(40)]
result = tph.compute(cycles)

print(f"PROD.TPH = {result.value:.2f} {result.unit}")   # 733.33 t/h
print(result.code, result.unit, result.n, result.warnings)
```

## Expected output

```text
--- 1. Confirm the install ---
mineproductivity 2.0.0

--- 2. A KPI is looked up by its governed identifier, not written by hand ---
resolved TonnesPerHour from the code 'PROD.TPH'

--- 3. Compute it: one CAT 793F's shift -- 40 haul cycles ---
40 cycles x 220 t = 8,800 t over 12.0 h
PROD.TPH = 733.33 t/h

--- 4. The result carries provenance, not just a bare float ---
code    : PROD.TPH
unit    : t/h
n       : 40 (rows that fed the computation)
warnings: ()

--- 5. The Standard Library is discoverable ---
12 KPIs are registered. The first five:
  COST.FuelPerTonne
  DISP.TotalDelayHours
  ENERGY.FuelConsumed
  HAUL.TruckCycleTime
  MAINT.MTTR

Nothing above hard-coded 'payload / hours'. The formula, its unit,
and its validity rules live inside the governed KPI object.
```

## Explanation

**Why look a KPI up instead of just dividing 8,800 by 12?**

Because in a real operation that division is never the whole story. Does "operating hours" include the 40 minutes the truck idled at the crusher queue? Does it include the fuelling stop? Does the night shift count it the same way as the day shift? When those answers live in three different spreadsheets, the same truck produces three different "tonnes per hour" figures and nobody can reconcile them.

`REGISTRY.get("PROD.TPH")` returns a **governed object** that has already answered those questions. The formula, the unit (`t/h`), the direction (higher is better), and the events it requires are all attached to it and versioned with it.

Notice the result is not a bare `733.33`. It is a `KPIResult` carrying `code`, `unit`, `n` (how many rows fed it), and `warnings`. That provenance is what lets a downstream layer - or an auditor - trust the number without reading your source code.

The `733.33 t/h` here is **one truck's shift**, not a fleet rate: a CAT 793F carrying ~220 t per load, turning a cycle roughly every 18 minutes, forty times across a 12-hour shift - 8,800 t moved. A fleet of several such trucks is what produces the ~1,300 t/h figures you will meet in Lesson 06. Lesson 06 also shows what happens when you aggregate rates like this across shifts - and why doing it naively is the most expensive mistake in mining reporting.

## Best practices

- **Always resolve by code.** `REGISTRY.get("PROD.TPH")` - never copy a formula into your script.
- **Read the whole `KPIResult`.** Check `warnings` and `n` before trusting `value`. An `n` of 1 when you expected 40 cycles means your scope was wrong.
- **Let the registry tell you what exists.** `sorted(REGISTRY)` is the catalogue; you never need a wiki page listing KPI names.

## Common mistakes

| Mistake | What happens | Do this instead |
|---|---|---|
| Re-implementing `payload / hours` inline | Your number silently diverges from every other system's | `REGISTRY.get("PROD.TPH")().compute(rows)` |
| Reading `.value` and discarding the rest | You miss `warnings` telling you the data was incomplete | Inspect `warnings` and `n` |
| Assuming a missing KPI raises | Some paths return a warning-carrying result with `value=None` | Guard `if result.value is not None` |
| Hard-coding the unit in your own output | Drifts when the KPI's unit changes | Print `result.unit` |

## Exercises

1. **Discover the library.** Print all 12 registered codes. Which namespaces exist (`PROD.`, `UTIL.`, `HAUL.`, …)? What operational question does each namespace answer?
2. **Shorten the shift.** Recompute with 27 cycles instead of 40 (an 8-hour shift). Does the *rate* change? Why not - and what does that tell you about what a ratio KPI actually measures?
3. **Break it deliberately.** Pass `operating_h = 0.0`. What does the result carry - an exception, or a warning? What does that choice tell you about the framework's philosophy?
4. **Inspect provenance.** Drop to three cycles. What does `n` become, and what does that tell a reviewer about how much evidence stands behind the number?

## Suggested next lesson

**[Lesson 02 - Entities](02_entities.md)** - a truck is still the same truck after it is refuelled, relocated, and rebuilt. How the platform models identity that outlives state.

---

**See also:** [`kpis` API Reference](../../api-reference/kpis.md) · [`kpis` package guide](../../packages/kpis.md) · [KPI Engine design specification](../../architecture/05_KPI_Engine_Design_Specification.md)
