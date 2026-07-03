"""``OntologyValidator``: contextual, cross-entity referential validation."""

from __future__ import annotations

import dataclasses
from collections.abc import Callable

from mineproductivity.core import BaseValidator, ValidationResult

from mineproductivity.ontology.entity_type import BaseEntityType, lookup_entity_type

__all__ = ["OntologyValidator"]


class OntologyValidator(BaseValidator[BaseEntityType]):
    """Contextual validation for a constructed
    :class:`~mineproductivity.ontology.entity_type.BaseEntityType`
    instance, separate from the structural field validation every leaf
    type already enforces on construction.

    Checks two kinds of cross-entity reference by field-naming
    convention:

    - A field named ``*_type_code`` (e.g. ``Fleet.equipment_type_code``)
      is checked against this package's own entity type registry --
      ``ontology`` owns that registry, so this resolution never needs
      external help.
    - A field named ``*_id`` (e.g. ``Bench.pit_id``) is checked against
      the optional, injectable ``entity_resolver`` callback -- ``ontology``
      does not persist entity *instances* itself (design spec §4), so
      instance-level resolution can only happen once a caller (a future
      config/datasets loader) supplies one. Without a resolver, instance
      -level references are not checked (structural validation at
      construction is still always enforced regardless).

    An unresolved reference is always a *warning* in the returned
    :class:`~mineproductivity.core.validator.ValidationResult`, never a
    raised exception -- Cookbook Part I, Ch. 8's rule that an orphaned
    reference must never silently halt ingestion of everything else.

    Examples
    --------
    >>> from mineproductivity.ontology import Fleet
    >>> validator = OntologyValidator()
    >>> fleet = Fleet(id="FL-NORTH", mine_id="pilbara-ridge", equipment_type_code="RIGID_HAUL_TRUCK")
    >>> validator.validate(fleet).is_valid
    True
    >>> bad_fleet = Fleet(id="FL-BAD", mine_id="pilbara-ridge", equipment_type_code="NOT_A_REAL_TYPE")
    >>> validator.validate(bad_fleet).is_valid
    False
    """

    def __init__(self, *, entity_resolver: Callable[[str], bool] | None = None) -> None:
        self._entity_resolver = entity_resolver

    def validate(self, candidate: BaseEntityType) -> ValidationResult:
        errors: list[str] = []
        for f in dataclasses.fields(candidate):
            if f.name == "id":
                continue
            value = getattr(candidate, f.name)
            if not isinstance(value, str) or not value:
                continue
            if f.name.endswith("_type_code"):
                if lookup_entity_type(value).is_nothing:
                    errors.append(
                        f"{type(candidate).__name__}.{f.name} references unknown "
                        f"entity type code {value!r}"
                    )
            elif f.name.endswith("_id") and self._entity_resolver is not None:
                if not self._entity_resolver(value):
                    errors.append(
                        f"{type(candidate).__name__}.{f.name} references unresolved id {value!r}"
                    )
        return ValidationResult.success() if not errors else ValidationResult.failure(*errors)
