# Tutorials

Every tutorial is backed by **runnable, self-contained example scripts** in the repository - read them, then run them. Each page below reuses that example set's own guide.

!!! info "Running any tutorial"
    ```bash
    pip install -e ".[analytics]"   # analytics extra covers every example
    python examples/<topic>/<script>.py
    ```
    Each script exits `0` and prints its own output; there is nothing to configure.

## Start here - Fundamentals

**New to MineProductivity? Start with the Learning Suite.** Ten lessons that teach the platform from first principles, in the order the architecture itself is layered, using real mining problems - haul trucks, shovels, ROM stockpiles, shifts, OEE. Each lesson is a runnable script plus a full tutorial.

| # | Lesson | You will learn |
|---|---|---|
| [01](fundamentals/01_hello.md) | Hello MineProductivity | A KPI is a governed object you look up, not a formula you retype |
| [02](fundamentals/02_entities.md) | Entities | HT-214 is still HT-214 after it is refuelled and rebuilt |
| [03](fundamentals/03_value_objects.md) | Value objects | An ore grade has no identity - and cannot exist invalid |
| [04](fundamentals/04_events.md) | Events | Append-only facts, and why last June's report still reconciles |
| [05](fundamentals/05_ontology.md) | Ontology | Why two sites can't compare TPH without a shared vocabulary |
| [06](fundamentals/06_kpis.md) | KPIs | The guardrail that stops you averaging a ratio (1,200 vs 1,233.3 t/h) |
| [07](fundamentals/07_analytics.md) | Analytics | Characterise a drifting fleet without re-deriving anything |
| [08](fundamentals/08_decision.md) | Decision | Explained, audited recommendations from a versioned policy |
| [09](fundamentals/09_digital_twin.md) | Digital Twin | Live state that is always a projection of the log |
| [10](fundamentals/10_visualization.md) | Visualization | Show a human - without the layer knowing what a tonne is |

The suite's plan and progress live in the [Learning Roadmap](../learning/LEARNING_ROADMAP.md) and [Learning Progress](../learning/LEARNING_PROGRESS.md).

---

The sections below are **per-package walkthroughs** - deeper capability tours of each package's API, complementing the Fundamentals path above.

## Foundation

- [Quick tour](quickstart.md) - the five-minute, whole-platform script.
- [Core](core.md) - entities, value objects, repositories, factories/builders, validation, serialization.
- [Events](events.md) - first event, replay/time-travel, corrections.
- [Ontology](ontology.md) - equipment modelling, structural modelling, contextual validation.
- [Registry](registry.md) - the register → discover → lookup mechanism every plugin shares.
- [Connectors](connectors.md) - CSV ingestion, REST with retry/auth-refresh.
- [KPIs](kpis.md) - single-KPI execution, composite `UTIL.OEE`, batch summary, discovery.

## Intelligence

- [Decision](decision.md) - audited pipelines, action prioritization, real-time sessions, plugin strategies.
- [Digital Twin](digital_twin.md) - cold-start + live synchronization, discovery, snapshots, plugin twin types.
- [Simulation](simulation.md) - snapshot-seeded Monte Carlo, scenario comparison, sensitivity sweeps.
- [Optimization](optimization.md) - MIP fleet allocation, plan comparison, sensitivity, candidate search, plugin solvers.
- [AI Agents](agents.md) - single tasks, policy-gated approval, multi-agent workflows, plugin agents/tools.
- [Visualization](visualization.md) - single-widget render, multi-source dashboards, exported reports, plugins.
