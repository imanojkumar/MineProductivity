# MineProductivity Learning Suite - Roadmap

> **Status: LOCKED.** This document is the stable master plan for the Learning
> Suite. It changes only when the *learning architecture* itself changes - not
> when individual lessons are written, validated, or reordered. Live execution
> state lives in [`LEARNING_PROGRESS.md`](LEARNING_PROGRESS.md), never here.

## 1. Purpose

MineProductivity is a locked, certified framework (`v2.0.0`). Its reference
documentation explains *what each package does*. The Learning Suite exists to
answer a different question: **how does a practitioner learn to think in this
framework?**

The Suite teaches the platform from first principles, using real mining
problems, in the order the architecture itself is layered - so that by the end a
reader can model a mine, measure it, reason about it, and extend it without
guessing.

## 2. Audience

Four groups read this material, and every lesson must serve all four:

| Reader | What they arrive with | What they need from us |
|---|---|---|
| **Mining engineer** | Deep domain truth; limited framework vocabulary | Why the software models the pit the way it does |
| **Data scientist** | Statistics and Python; partial domain context | Where the governed facts come from, and what they may/may not re-derive |
| **Software engineer** | Architecture fluency; little mining context | What a haul cycle, OEE, or bench actually *is* |
| **Researcher** | Rigour and reproducibility | Provenance, determinism, and how to extend without forking |

## 3. Learning philosophy

These are binding constraints on every lesson, not aspirations.

1. **Why before how.** A lesson that only shows API calls has failed. Each one
   must first establish the *engineering problem* the concept solves.
2. **The domain is real.** Haul trucks, shovels, crushers, benches, shifts, ore
   and waste, OEE. Never `Person`, `Car`, `Animal`, `Foo`.
3. **Verification-first authoring.** Public APIs are read from the
   implementation and existing examples *before* a lesson is written. Signatures
   are never recalled or guessed.
4. **Every example executes.** A lesson is not written until its script runs to
   exit `0` and passes `ruff`, `ruff format --check`, and `mypy --strict`.
5. **Teach the layer, in layer order.** The Suite follows the platform's own
   locked dependency chain. A reader never meets a concept before its
   foundation.
6. **Reuse over duplication.** Lessons compose the framework's real APIs and
   existing example assets. They never re-implement framework logic, and never
   introduce a helper that already exists.
7. **Honest about design.** Where the architecture deliberately ships an
   interface and no implementation, the lesson says so and explains the
   reasoning, rather than inventing a concrete class to make a demo tidy.
8. **Locked once validated.** A validated lesson is frozen. It is revisited only
   for a genuine defect - never for taste or refactoring.

## 4. Repository organization

The Suite is deliberately separate from the package demos that already exist.

| Location | Role | Audience posture |
|---|---|---|
| `examples/fundamentals/NN_topic/` | **Learning Suite lessons** - a progressive, self-contained teaching path. Each lesson runs standalone. | "Teach me the framework." |
| `examples/<package>/` | **Pre-existing API demos** - per-package capability showcases (`core`, `events`, `kpis`, `decision`, …). Authoritative API references. | "Show me this package's surface." |
| `examples/workflows/` | **Milestone 3** - end-to-end mining workflows spanning packages. | "Solve my problem." |
| `benchmark/`, `notebooks/` | Existing performance and notebook assets. Reused, not duplicated. | - |

Lessons are self-contained by design: each lives in its own directory and does
not import across lesson boundaries. This is pedagogy, not duplication - a
learner must be able to run lesson 04 without having run lesson 03. Framework
logic is always reused; only *narrative scaffolding* is repeated.

## 5. Documentation organization

| Location | Role |
|---|---|
| `docs/tutorials/fundamentals/NN_topic.md` | The tutorial for each lesson, in the fixed format below |
| `docs/tutorials/index.md` | Tutorial hub; links Fundamentals alongside the package walkthroughs |
| `docs/learning/LEARNING_ROADMAP.md` | This document (locked) |
| `docs/learning/LEARNING_PROGRESS.md` | Live execution tracker and checkpoint |
| `mkdocs.yml` | Navigation; Fundamentals appears as a section under Tutorials |

Every tutorial cross-links to: its runnable script on GitHub, the relevant
[API Reference](../api-reference/index.md), the
[Architecture Handbook](../architecture/README.md) section that governs the
concept, and the next lesson.

### Fixed lesson format

Every tutorial contains these sections, in this order:

1. Title · 2. Objective · 3. Prerequisites · 4. Concepts covered ·
5. Complete runnable example · 6. Expected output · 7. Explanation ·
8. Best practices · 9. Common mistakes · 10. Exercises ·
11. Suggested next lesson

## 6. Milestones

| # | Milestone | Scope | Depends on |
|---|---|---|---|
| **1** | **Fundamentals** | 10 lessons + 10 tutorials teaching the platform from first principles | - |
| **2** | **Package Tutorials** | Depth per package: `core`, `ontology`, `events`, `kpis`, `analytics`, `decision`, `digital_twin`, `simulation`, `optimization`, `agents`, `visualization` | 1 |
| **3** | **Mining Workflows** | Cross-package, problem-led: fleet productivity, crusher performance, shift analytics, dispatch, maintenance | 1, 2 |
| **4** | **Reference Applications** | Runnable applications built *on* the framework (dashboards, productivity cockpit, executive reporting) - plugin/application layer only | 2, 3 |
| **5** | **AI Examples** | Agent-layer teaching: root-cause analysis, KPI explanation, copilot patterns - reasoning backends stay plugins | 2, 3 |
| **6** | **Research Examples** | Reproducibility-led: Monte Carlo studies, benchmark studies, sensitivity analysis | 2, 3 |

### Milestone 1 - Fundamentals (deliverables)

| # | Lesson | Package taught |
|---|---|---|
| 01 | Hello MineProductivity | install, `kpis.REGISTRY` |
| 02 | Entities | `core.BaseEntity` |
| 03 | Value objects | `core.BaseValueObject` |
| 04 | Events | `events` |
| 05 | Ontology | `ontology` |
| 06 | KPIs | `kpis` |
| 07 | Analytics | `analytics` |
| 08 | Decision | `decision` |
| 09 | Digital Twin | `digital_twin` |
| 10 | Visualization | `visualization` |

Each lesson ships one runnable script under `examples/fundamentals/` and one
tutorial under `docs/tutorials/fundamentals/`.

## 7. Completion criteria

A milestone is complete only when **all** of the following hold. Partial
completion is reported honestly against this list; it is never rounded up.

**Per lesson**
- [ ] Script exists, is self-contained, and uses only verified public APIs
- [ ] Script executes to exit `0`
- [ ] `ruff check` clean
- [ ] `ruff format --check` clean
- [ ] `mypy --strict` clean
- [ ] Uses mining-domain concepts exclusively
- [ ] Tutorial exists with all eleven sections
- [ ] Tutorial's expected output matches the script's real output

**Per milestone**
- [ ] Every lesson above passes
- [ ] Navigation updated (`mkdocs.yml`, tutorial hub)
- [ ] `mkdocs build --strict` passes (0 warnings)
- [ ] `scripts/quality/check_docs.py` passes (0 broken links, 0 failed snippets)
- [ ] Full `pytest` suite still green (no regression in production code)
- [ ] `src/` unmodified, unless a genuine defect was found and recorded
- [ ] `LEARNING_PROGRESS.md` updated to reflect true state

## 8. Governance

- **This roadmap is locked.** Amend only for a change in learning architecture
  (a new milestone, a changed format, a restructured layout).
- **The implementation is the single source of truth.** Where any plan,
  document, or prompt conflicts with the verified code, the code wins and the
  document is corrected.
- **Production code is out of scope.** The Suite never modifies `src/` except to
  correct a genuine, demonstrated defect, recorded in the progress tracker.
- **Work is resumable.** Every session ends with `LEARNING_PROGRESS.md` updated
  and a checkpoint naming the exact next step.

## References

- [Architecture Handbook](../architecture/README.md) · [ADRs](../adr/index.md)
- [API Reference](../api-reference/index.md) · [Packages](../packages/index.md)
- [Engineering Rules](../governance/ENGINEERING_RULES.md)
