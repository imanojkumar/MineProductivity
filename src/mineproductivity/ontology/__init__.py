"""mineproductivity.ontology — The explicit, machine-readable domain vocabulary for mining productivity: asset types, process types, relationships, and schema definitions that all other packages model against.

The full Ontology Framework (entity types, registry, relationships,
reasoning) has not been implemented yet -- it is scheduled for its own
milestone; see ``docs/architecture/02_Ontology_Framework_Design_Specification.md``.

Per Documentation Governance Rule #005, exactly one minimum shared
contract has been published ahead of that milestone because the
Event Framework's locked design specification requires it:
``DelayCategory``, the closed six-value delay taxonomy. No other
ontology concept, business logic, service, or registry exists in this
package yet. See ``ontology/reference/delay_taxonomy.py`` and the
accompanying README.md for the full design intent of this package.
"""

from __future__ import annotations

from mineproductivity.ontology.reference import DelayCategory

__all__ = ["DelayCategory"]
