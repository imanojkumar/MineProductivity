"""The ``mineproductivity.ontology`` exception hierarchy."""

from __future__ import annotations

from mineproductivity.core import MineProductivityError, NotFoundError, ValidationError

__all__ = ["OntologyValidationError", "RelationshipError", "UnknownEntityTypeError"]


class OntologyValidationError(ValidationError):
    """A :class:`~mineproductivity.ontology.entity_type.BaseEntityType`
    instance failed structural or contextual validation."""


class UnknownEntityTypeError(NotFoundError):
    """``EntityTypeRegistry.lookup(code)`` found no registered type for ``code``."""


class RelationshipError(MineProductivityError):
    """A :class:`~mineproductivity.ontology.relationship.Relationship`
    references a ``source_id``/``target_id`` that cannot be resolved, or
    declares a :class:`~mineproductivity.ontology.relationship.RelationshipKind`
    invalid for the two entity types involved."""
