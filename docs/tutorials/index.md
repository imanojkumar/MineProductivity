# Tutorials

Every tutorial is backed by **runnable, self-contained example scripts** in the repository - read them, then run them. Each page below reuses that example set's own guide.

!!! info "Running any tutorial"
    ```bash
    pip install -e ".[analytics]"   # analytics extra covers every example
    python examples/<topic>/<script>.py
    ```
    Each script exits `0` and prints its own output; there is nothing to configure.

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
