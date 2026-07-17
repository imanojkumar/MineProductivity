# Lesson 08 - Decision

## Objective

Turn a measured drift into an **explained, audited recommendation** driven by a versioned policy - and understand why the platform refuses to guess *why* the fleet is degrading.

## Prerequisites

- [Lesson 06 - KPIs](06_kpis.md) and [Lesson 07 - Analytics](07_analytics.md). This lesson continues their story: FL-NORTH is at 1,150 t/h against a 1,250 target, declining ~12.4 t/h per shift.

## Concepts covered

| Concept | Why it exists |
|---|---|
| `Policy` | A **versioned, governed** rule set - not an `if` buried in a script. |
| `Rule` (`PredicateSpecification`) | A named, testable predicate over the evidence. |
| `Threshold` | Declarative limits that say *by how much* something breached. |
| `DecisionPipeline` + stages | `RuleEngineStage` → `ModelStage` → `ExplanationStage` → ranking, composed. |
| `Recommendation` | Carries `triggered_rules`, `summary`, `evidence`, `explanation`. |
| `DecisionAuditTrail` | Append-only accountability record. |
| Interface-only `RootCauseAnalyzer` / `WhatIfEngine` | Zero implementations, on purpose (ADR-0007). |

## Complete runnable example

**[:material-file-code: `examples/fundamentals/08_decision/decision.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/fundamentals/08_decision/decision.py)**

```bash
python examples/fundamentals/08_decision/decision.py
```

The policy is a governed object, versioned like any other:

```python
from mineproductivity.core import PredicateSpecification
from mineproductivity.decision import Policy, Rule, Threshold

rules: dict[str, Rule] = {
    "tph_below_target": PredicateSpecification(
        lambda ctx: any(r.value is not None and r.value < TPH_TARGET for r in ctx.kpi_results)
    ),
    "tph_trend_declining": PredicateSpecification(
        lambda ctx: any(
            isinstance(r, TrendResult) and r.direction == "decreasing"
            for r in ctx.analytics_results
        )
    ),
}
policy = Policy(
    code="PROD.NorthFleetUnderTarget",
    rules=rules,
    thresholds={
        "tph_below_target": Threshold(field="value", comparator="<", limit=TPH_TARGET),
        "tph_trend_declining": Threshold(field="trend.slope", comparator="<", limit=0.0),
    },
    strategy_code="STRATEGY.Threshold",
)
```

## Expected output

```text
--- 1. Evidence, gathered -- never recomputed here ---
KPI fact  : PROD.TPH = 1,150.0 t/h (target 1,250)
Analytics : TREND.Linear direction='decreasing' r^2=0.974
(the decision layer will consume these two facts and derive neither)

--- 2. A versioned, governed Policy -- not an `if` buried in a script ---
policy 'PROD.NorthFleetUnderTarget' v1.0.0
rules  : ['tph_below_target', 'tph_trend_declining']
(versioned: an auditor can ask which policy version produced a call)

--- 3. One audited pipeline run: evaluate rules, then recommend ---
triggered: ('tph_below_target', 'tph_trend_declining')
summary  : Policy 'PROD.NorthFleetUnderTarget' triggered by rule(s): tph_below_target, tph_trend_declining
evidence : ('PROD.TPH', 'TREND.Linear')

--- 4. Declarative thresholds confirm the breach independently ---
  value < 1250.0  (observed 1,150.0000)
  trend.slope < 0.0  (observed -0.0003)
(the rule said 'this fired'; the threshold says 'by how much')

--- 5. Explain and rank -- an unexplained recommendation is not usable ---
rank=1 score=0.755
  premise: Rule 'tph_below_target' triggered under policy 'PROD.NorthFleetUnderTarget'
  premise: Rule 'tph_trend_declining' triggered under policy 'PROD.NorthFleetUnderTarget'
  premise: PROD.TPH = 1150.0
  premise: TREND.Linear observed

--- 6. The audit trail is the accountability record ---
1 audited entry for shift A-2026-06-28
(append-only: six months later an incident review can reconstruct
 exactly which policy version fired, on what evidence, and why)

--- 7. What this package deliberately does NOT decide ---
decision.RootCauseAnalyzer and decision.WhatIfEngine are interfaces
with ZERO implementations (ADR-0007). The platform will tell you the
fleet is under target and declining -- it will not guess WHY without
a plugin that encodes your site's causal model. That refusal is the
feature: a fabricated root cause is worse than none.
```

## Explanation

### Why a `Policy` object instead of an `if` statement

`if tph < 1250: alert()` works - until you need to answer these questions:

- *Which* threshold was in force last June? (The target changed in April.)
- Who approved it, and when?
- The alert fired at 03:40; on what evidence?
- Why did the same conditions not fire an alert the week before?

A `Policy` is **versioned** (`v1.0.0`) and governed, so every one of those has an answer. An `if` in a cron script has none.

### Rules and thresholds do different jobs

This trips people up. Section 3's **rule** answers a boolean: *did this fire?* Section 4's **threshold** answers a magnitude: *by how much?* - `value < 1250.0 (observed 1,150.0)`.

You need both. "The fleet breached target" prompts a shrug; "the fleet is 100 t/h under a 1,250 target and losing 12.4 t/h per shift" prompts a decision. The rule triggers the workflow; the threshold gives the human the size of the problem.

### An unexplained recommendation is unusable

Section 5 is the part most alerting systems get wrong. The `ExplanationStage` attaches **premises**: which rules fired, under which policy, on which evidence, with what values. A recommendation that says only "fleet underperforming" gets ignored by shift three. One that says *"rule X triggered under policy Y because PROD.TPH = 1150.0 and TREND.Linear was observed decreasing"* can be argued with - and being arguable is what makes it trustworthy.

The `WeightedScoreRanking` then puts it in priority order (`rank=1`, `score=0.755`), because a superintendent with fourteen alerts needs to know which one to read first.

### The audit trail is the point

`DecisionAuditTrail` is append-only. Six months later, an incident review can reconstruct exactly which policy version fired, on what evidence, and why. This is the same discipline as the event log in Lesson 04, applied to *decisions* rather than *facts*.

### The refusal (ADR-0007)

`RootCauseAnalyzer` and `WhatIfEngine` are interfaces with **zero implementations**.

The platform will tell you FL-NORTH is under target and declining. It will **not** tell you *why*. Why not? Because the honest answer depends on your site: is it haul distance growth as the pit deepens? A shovel with a failing swing motor? Wet-season road conditions? Operator rotation? A generic framework guessing among those would be inventing a causal claim it has no basis for - and **a fabricated root cause is worse than none**, because people act on it.

Encode your site's causal model in a plugin; the contract is waiting.

## Best practices

- **Version your policies.** The target *will* change; you need to know what was in force when.
- **Name rules for what they mean** (`tph_below_target`), not `rule_1`. The name lands in the audit trail and the explanation.
- **Always attach thresholds**, not just rules - magnitude drives triage.
- **Always run the `ExplanationStage`.** An unexplained recommendation gets ignored.
- **Consume evidence; never re-derive it.** The decision layer reads `KPIResult` and `TrendResult`.
- **Audit every operationally-actionable run.**

## Common mistakes

| Mistake | What happens | Do this instead |
|---|---|---|
| Business rules as inline `if`s | No version, no audit, no explanation | A governed `Policy` |
| Re-deriving the KPI inside a rule | A second definition of the metric appears | Read `ctx.kpi_results` |
| Rules without thresholds | "It breached" - but nobody knows if it is 1 t/h or 100 | Add `Threshold` |
| Skipping explanation | Alert fatigue; the recommendation is ignored | `ExplanationStage` |
| Expecting a built-in root-cause engine | `RootCauseAnalyzer` has zero implementations | Write a site-specific plugin |
| Not auditing | Unreconstructable six months later | `DecisionAuditTrail` |

## Exercises

1. **Change the target.** Set `TPH_TARGET = 1_100.0` and re-run. Which rules fire now? What does that tell you about why the threshold must be versioned with the policy?
2. **Add a third rule.** Fire only when `r_squared > 0.9` - i.e. only escalate when the decline is *convincing*, not noisy. Why is this a better alerting policy than trend direction alone?
3. **Read the audit.** Print the full audit entry, including `recorded_at`. What could an incident review reconstruct from it? What could it *not*?
4. **Design the refusal away - then reconsider.** Sketch a `RootCauseAnalyzer` for your site. What data would it need that this framework does not have? Does that change your view of ADR-0007?
5. **Rank several.** Build three recommendations at different severities and rank them. Does the order match your operational intuition?

## Suggested next lesson

**[Lesson 09 - Digital Twin](09_digital_twin.md)** - you have measured, characterised, and decided against *history*. Now: what is true **right now**?

---

**See also:** [`decision` API Reference](../../api-reference/decision.md) · [`decision` package guide](../../packages/decision.md) · [Decision Intelligence design specification](../../architecture/07_Decision_Intelligence_Design_Specification.md) · [ADR-0007](../../adr/ADR-0007-Decision-Intelligence.md)
