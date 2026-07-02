"""MineProductivity — a metadata-first, ontology-driven, event-sourced
platform for mining productivity intelligence.

The ``mineproductivity.core`` package contains the platform's foundational
framework primitives (entities, value objects, identifiers, specifications,
repositories, and friends). The ``mineproductivity.events`` package now
implements the immutable, append-only event model (Event Sourcing) built on
it, per the locked Event Framework Design Specification. Every other
subsystem package is still a structural placeholder (``mineproductivity.
ontology`` carries only the one minimal shared contract ``events`` requires
-- see Documentation Governance Rule #005). See the root README.md and
docs/architecture/README.md for the governing architecture, and
ROADMAP.md for the implementation phasing.
"""

__version__ = "0.3.0"
__all__ = ["__version__"]
