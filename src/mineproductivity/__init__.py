"""MineProductivity — a metadata-first, ontology-driven, event-sourced
platform for mining productivity intelligence.

The ``mineproductivity.core`` package contains the platform's foundational
framework primitives (entities, value objects, identifiers, specifications,
repositories, and friends). The ``mineproductivity.events`` package
implements the immutable, append-only event model (Event Sourcing) built on
it, per the locked Event Framework Design Specification. The
``mineproductivity.ontology`` package implements the full typed,
machine-readable domain vocabulary (ten sub-ontology families,
relationships, contextual validation, and the Knowledge Graph projection
contract) per the locked Ontology Framework Design Specification. The
``mineproductivity.registry`` and ``mineproductivity.plugins`` packages
implement the plugin-first discovery-and-lifecycle backbone (the generic
``Registry`` mechanism, entry-point discovery, and version-gated,
isolation-guaranteed plugin activation) per the locked Registry Framework
Design Specification. The ``mineproductivity.connectors`` package
implements the vendor-neutral ingestion boundary (the ``FMSConnector``
contract, reference file/network/streaming connectors, and
documentation-only OEM adapter shapes) per the locked Connector Framework
Design Specification. The ``mineproductivity.kpis`` package now implements
the metric backbone -- the metadata-first, self-describing KPI Engine (the
``BaseKPI``/``CompositeKPI`` object model, dependency-graph orchestration,
pluggable execution backends, and the 12-KPI Standard Library reference
implementation) per the locked KPI Engine Design Specification. The
``mineproductivity.analytics`` package implements the statistical and
analytical computation layer built directly on ``kpis`` -- trend, baseline,
and benchmark analysis, rolling and aggregate statistics, data-quality
scoring, batch/streaming/incremental execution modes, and the plugin
registry -- per the locked Analytics Engine Design Specification. The
``mineproductivity.decision`` package implements the platform's
prescriptive layer built directly on ``analytics`` -- rule/policy-driven
decision strategies, ranking, explanation, prioritization, action
planning, alerting, real-time and batch decision execution, and an
append-only decision audit trail -- per the locked Decision Intelligence
Design Specification. The ``mineproductivity.digital_twin``,
``mineproductivity.simulation``, and ``mineproductivity.optimization``
packages implement the stateful representation, projection, and
prescriptive-search layers respectively, ``mineproductivity.agents``
implements the model-independent agent-orchestration layer, and
``mineproductivity.visualization`` implements the presentation layer --
the final package in the architecture -- each per its own locked design
specification. Every package in the locked dependency chain is now
implemented. See the root README.md and docs/architecture/README.md for
the governing architecture, and ROADMAP.md for the implementation
phasing.
"""

__version__ = "2.0.0"
__all__ = ["__version__"]
