# ADR-0013: Placeholder Package Rationalization (Post-v2.0 Proposal)

| | |
|---|---|
| **Status** | Proposed - deferred to post-v2.0 governance review |
| **Date** | 2026-07-12 |
| **Deciders** | Chief Software Architect, MineProductivity |
| **Governs** | The nine structural placeholder packages under `src/mineproductivity/` |
| **Related documents** | [`ROADMAP.md`](../../ROADMAP.md); [`docs/governance/ENGINEERING_RULES.md`](../governance/ENGINEERING_RULES.md); root [`README.md`](../../README.md) |

> **This ADR proposes; it does not act.** No package is removed by this
> document. Placeholder rationalization is explicitly out of scope for the
> v2.0 certification release and is recorded here so the recommendation and
> its rationale survive until a future governance review acts on it. Removing
> a placeholder is a separate, ADR-gated change with its own release cycle.

## Context

Nine packages under `src/mineproductivity/` remain 7-line structural
placeholders left from the Phase-0 repository skeleton - each an
`__init__.py` stub with a skeleton-era `README.md`, no locked Design
Specification, no Implementation Checklist, and no code:

`benchmark`, `certification`, `cli`, `config`, `datasets`, `exceptions`,
`io`, `typing`* , `utils`, `validation`.

(*The earlier handoff also named a `typing` stub; it does not exist in the
tree. The actual count is nine.)

The eleven **domain** packages of the locked architecture
(`core → … → visualization`) plus the three cross-cutting infrastructure
packages (`registry`, `plugins`, `connectors`) are all implemented, tested,
and released as of v1.11.0. The nine placeholders are the only remaining
skeleton artifacts. A production 2.0 that ships nine empty stubs with
skeleton READMEs presents an inconsistent, unfinished surface to a
first-time reader - but removing packages is itself an architectural change,
and the Architecture Stability rule requires that such changes be
deliberate, justified, and reviewed, not bundled opportunistically into a
certification release.

## Decision (proposed, not yet enacted)

Defer any placeholder removal until after v2.0. When a future governance
review takes this up, evaluate each placeholder against a single test -
*does it have a concrete, chartered future purpose that justifies its
continued presence as a named package?* - and sort them into three groups:

**Group A - Retain and eventually implement (clear purpose):**

- `cli` - a command-line interface is a natural post-architecture
  application layer with an obvious user-facing purpose. `pyproject.toml`
  previously shipped a `[project.scripts]` entry point for it (removed in
  v0.7.1 because the target did not exist yet). Retain; implement behind its
  own Design Specification when scheduled.
- `certification` - a conformance/certification suite has a defined role in
  the Reference Implementation Blueprint (Phase 7). `scripts/quality/`
  provides interim standalone substitutes. Retain; implement when Phase 7 is
  scheduled.

**Group B - Resolve a naming shadow:**

- `benchmark` (source package) shadows the top-level `benchmark/` directory,
  which already hosts real, run scenarios and reports. The source-package
  stub serves no purpose the top-level directory does not already serve.
  Recommend removing the `src/mineproductivity/benchmark/` stub (or, if a
  harness package is later wanted, giving it a distinct name), so the two
  `benchmark` locations stop colliding conceptually.

**Group C - Remove unless a concrete need is demonstrated:**

- `config`, `io`, `utils`, `exceptions`, `validation`, `datasets` - generic
  cross-cutting names with no locked specification and no demonstrated need.
  `core` already defines its own internal exception hierarchy directly and
  does not depend on a separate `exceptions` package; `validation` is covered
  within each package; `datasets` is served by per-package test fixtures.
  Recommend removal, each recorded in its own follow-up ADR, unless a
  concrete, specified need arises first.

## Consequences

- **If enacted (post-v2.0):** a cleaner, fully-intentional package surface;
  the root README's "24 subsystems" framing and the cross-cutting-layer list
  updated to match; no dead stubs in a certified platform.
- **If never enacted:** the placeholders remain harmless but present a
  slightly unfinished surface; documentation must continue to describe them
  honestly as placeholders rather than implying they are usable.
- **In all cases:** the v2.0 certification proceeds with the placeholders
  retained and honestly documented. Their fate is a deliberate, separate,
  ADR-gated decision - never a silent deletion.

## Status Tracking

This ADR remains **Proposed** until a governance review either accepts it
(scheduling the Group B/C removals as their own changes) or supersedes it.
Its revisit trigger is the first maintenance cycle after v2.0 ships.
