---
title: MineProductivity
hide:
  - navigation
---

# MineProductivity

**Enterprise-grade Python framework for mining analytics, Digital Twins, optimization and AI** 

[Get started :material-rocket-launch:](getting-started/installation.md){ .md-button .md-button--primary }
[View on GitHub :fontawesome-brands-github:](https://github.com/imanojkumar/MineProductivity){ .md-button }

!!! success "Architecture complete & locked - certified `v2.0.0`"
    All eleven domain packages plus the three cross-cutting infrastructure packages are implemented, tested (**2,986 passing tests**, `mypy --strict` clean across 314 files), documented, and released. Public APIs are **stable by contract**. New value ships as plugins and applications - not as changes to the locked packages.

## Why MineProductivity?

<div class="grid cards" markdown>

-   :material-sitemap: __Ontology-first__

    A shared, explicit domain vocabulary (assets, processes, events, KPIs) precedes any code that operates on it.

-   :material-timeline-clock: __Event-first__

    The system of record is an immutable event stream; all derived state (KPIs, twins, analytics) is a rebuildable projection.

-   :material-tag-multiple: __Metadata-first__

    Every KPI, dataset, and model ships with machine-readable metadata (units, provenance, versioning) before it ships with logic.

-   :material-puzzle: __Plugin-first__

    Connectors, KPIs, analytics, agents, and renderers are discovered through a registry/plugin system - never hard-wired into the core.

-   :material-layers-triple: __Clean architecture__

    Dependencies point inward toward `core`/`ontology`. Layering is mechanically enforced by per-package tests, both directions.

-   :material-shield-check: __Enterprise quality__

    Strict typing, 99% branch coverage, cross-platform CI, and a recorded certification gate.

</div>

## The platform at a glance

The locked dependency chain - lower layers never import higher ones:

``` mermaid
graph TD
    core --> ontology --> events --> kpis --> analytics --> decision
    decision --> digital_twin --> simulation --> optimization --> agents --> visualization
    registry -.-> kpis
    plugins -.-> kpis
    connectors -.-> kpis
```

## Explore the documentation

<div class="grid cards" markdown>

-   :material-rocket: __[Quick Start](getting-started/quick-start.md)__

    One truck, one shift, one KPI - the platform end-to-end in ~50 lines.

-   :material-school: __[Learning Suite - Fundamentals](tutorials/fundamentals/01_hello.md)__

    **New here? Start with this.** Ten lessons teaching the platform from first principles, using real mining problems.

-   :material-book-multiple: __[Tutorials](tutorials/index.md)__

    Runnable, package-by-package walkthroughs from Foundation to Intelligence.

-   :material-book-open-variant: __[Packages](packages/index.md)__

    Per-package architecture, dependency rules, and extension guides.

-   :material-api: __[API Reference](api-reference/index.md)__

    Symbol-level reference generated from the packages' own docstrings.

-   :material-floor-plan: __[Architecture Handbook](architecture/README.md)__

    The twelve locked design specifications and the ADRs behind them.

-   :material-certificate: __[Certification](certification/2.0-certification.md)__

    The v2.0.0 enterprise certification record and quality-gate results.

</div>

## Install

```bash
pip install git+https://github.com/imanojkumar/MineProductivity.git
```

The base install has **zero third-party dependencies**. Optional extras add capability only where you need it - see [Installation](getting-started/installation.md).

## Citation

If you use MineProductivity in research or industry, please [cite it](project/citation.md) via the Zenodo Concept DOI [`10.5281/zenodo.21172767`](https://doi.org/10.5281/zenodo.21172767).
