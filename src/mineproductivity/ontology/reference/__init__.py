"""mineproductivity.ontology.reference — cross-domain reference/taxonomy data.

This subpackage holds closed, governed vocabularies that are ontology
*data*, not ontology *entities* -- see ``delay_taxonomy`` for the first
and, at this milestone, only member.
"""

from __future__ import annotations

from mineproductivity.ontology.reference.delay_taxonomy import DelayCategory

__all__ = ["DelayCategory"]
