# Learning Suite — Fundamentals v1.0

**Release:** Learning Suite, Milestone 1 (Fundamentals)
**Status:** Certified with minor recommendations · Released
**Nature:** Educational documentation. No production code changed; the framework remains frozen at `v2.0.0`.

## Overview

MineProductivity's reference documentation explains *what each package does*. The **Learning Suite** answers a different question: **how does a practitioner learn to think in this framework?**

Fundamentals is the first milestone — ten lessons that teach the platform from first principles, in the order the architecture itself is layered, using real mining problems rather than toy `Foo`/`Bar` examples. By the end, a reader can model a mine, measure it, characterise it, decide on it, project its live state, and present it — and knows which decisions the platform deliberately leaves to a plugin author.

## Highlights

- **Ten runnable lessons + ten full tutorials**, following the platform's own locked dependency chain.
- **One continuous mining story.** A north fleet (`FL-NORTH`) is measured (Lesson 06), found to be degrading ~12.4 t/h per shift (Lesson 07), and escalated through a versioned, audited policy (Lesson 08) — so the layers are taught as one narrative, not ten disconnected demos.
- **Real domain throughout.** CAT 793F haul trucks, hydraulic shovels, ROM stockpiles, benches, 2×12 shifts, ore/waste, OEE, cycle legs (queue/spot/load/haul/dump/return).
- **Honest about design.** Where the platform deliberately ships an interface and no implementation — forecasting, root-cause analysis, renderers — the lessons say so and explain *why*, rather than inventing a concrete class to make a demo tidy.
- **Every number is real.** Tutorial "Expected output" is pasted from an actual run, never imagined.

## Lessons

| # | Lesson | Package | Core idea |
|---|---|---|---|
| 01 | [Hello, MineProductivity](../tutorials/fundamentals/01_hello.md) | `kpis` | A KPI is a governed object you look up, not a formula you retype |
| 02 | [Entities](../tutorials/fundamentals/02_entities.md) | `core` | HT-214 is still HT-214 after it is refuelled and rebuilt |
| 03 | [Value objects](../tutorials/fundamentals/03_value_objects.md) | `core` | An ore grade has no identity — and cannot exist invalid |
| 04 | [Events](../tutorials/fundamentals/04_events.md) | `events` | Append-only facts; last June's report still reconciles |
| 05 | [Ontology](../tutorials/fundamentals/05_ontology.md) | `ontology` | Why two sites can't compare TPH without a shared vocabulary |
| 06 | [KPIs](../tutorials/fundamentals/06_kpis.md) | `kpis` | The guardrail that stops you averaging a ratio |
| 07 | [Analytics](../tutorials/fundamentals/07_analytics.md) | `analytics` | Characterise a drifting fleet without re-deriving anything |
| 08 | [Decision](../tutorials/fundamentals/08_decision.md) | `decision` | Explained, audited recommendations from a versioned policy |
| 09 | [Digital Twin](../tutorials/fundamentals/09_digital_twin.md) | `digital_twin` | Live state that is always a projection of the log |
| 10 | [Visualization](../tutorials/fundamentals/10_visualization.md) | `visualization` | Show a human — without the layer knowing what a tonne is |

## Tutorials

Each lesson pairs with a tutorial in a fixed **eleven-section format**: Title · Objective · Prerequisites · Concepts covered · Complete runnable example · Expected output · Explanation · Best practices · Common mistakes · Exercises · Suggested next lesson.

The scripts live under [`examples/fundamentals/`](https://github.com/imanojkumar/MineProductivity/tree/main/examples/fundamentals); the tutorials render on the docs site under **Tutorials → Fundamentals**.

## Learning philosophy

Binding constraints on every lesson (from the [Learning Roadmap](../learning/LEARNING_ROADMAP.md)):

1. **Why before how** — establish the engineering problem before showing an API.
2. **The domain is real** — no `Person`/`Car`/`Foo`.
3. **Verification-first authoring** — APIs are read from the implementation before a lesson is written, never recalled.
4. **Every example executes** — exit `0`, `ruff`/`mypy --strict` clean, before it is written up.
5. **Teach the layer, in layer order** — a reader never meets a concept before its foundation.
6. **Reuse over duplication** — compose the real APIs; never re-implement framework logic.
7. **Honest about design** — name the interface-only extension points and explain the refusal.
8. **Locked once validated** — a validated lesson is revisited only for a genuine defect.

## Engineering methodology

The suite was built like software, not prose. Lessons were authored **verification-first**: every public API was read from the implementation or an existing example before use, and every script was executed and gated before its tutorial was written. That discipline paid for itself — several invented-API assumptions were caught by execution rather than shipped, and the resulting corrections became the "Common mistakes" sections. Progress was tracked in a live tracker with a carry-forward verified-API table, so no signature was ever re-derived across sessions.

## Validation summary

At release, across the whole repository:

| Gate | Result |
|---|---|
| `ruff check .` | Passed |
| `ruff format --check .` | Clean |
| `mypy --strict` | 0 issues (314 source files + 10 lessons) |
| All 10 lessons execute | Exit `0` |
| `mkdocs build --strict` | 0 warnings |
| `check_docs.py` | 0 broken links, 0 failed snippets |
| `pytest` | 2,986 passed — no regression |
| Production code (`src/`) | Untouched |

## Certification summary

Fundamentals passed four independent reviews (Engineering QA, Educational, Mining Domain, Documentation/UX). The three Class-A findings raised were corrected and re-validated: a truck-spec inaccuracy (CAT 793F standardised at its ~226 t payload), an operationally implausible headline figure (replaced with a realistic 40-cycle shift → 733.33 t/h), and the use of private framework methods in teaching code (replaced with public contracts). Final status: **Certified with minor recommendations**.

## Known limitations

- **Fundamentals covers 8 of the 11 packages.** `simulation`, `optimization`, and `agents` are intentionally deferred to **Milestone 2 (Package Tutorials)**.
- **No automated lesson-execution test yet.** Lessons are currently protected by release-time validation, not CI. Adding a `pytest` harness that runs all ten is the top recommendation for the next cycle.
- **Exercises ship without solutions.** Hints/solutions are a planned enhancement.
- These and the remaining minor recommendations are tracked in [`docs/learning/LEARNING_PROGRESS.md`](https://github.com/imanojkumar/MineProductivity/blob/main/docs/learning/LEARNING_PROGRESS.md).

## Milestone 2 preview — Package Tutorials

The next milestone goes *deeper*, one package at a time, and covers the three packages Fundamentals defers:

- Per-package depth for `core`, `ontology`, `events`, `kpis`, `analytics`, `decision`, `digital_twin`, and — newly — **`simulation`, `optimization`, `agents`**, plus `visualization`.
- Plugin-authoring walkthroughs for each interface-only extension point (solvers, reasoning backends, renderers, forecasters).
- The full `KPIEngine`-over-an-event-store path that Fundamentals links out to.

The complete six-milestone plan (Fundamentals → Package Tutorials → Mining Workflows → Reference Applications → AI Examples → Research Examples) is in the [Learning Roadmap](../learning/LEARNING_ROADMAP.md).

---

*Start learning: [Lesson 01 — Hello, MineProductivity](../tutorials/fundamentals/01_hello.md).*
