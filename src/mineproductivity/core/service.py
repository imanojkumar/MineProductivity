"""``BaseService``: a marker base for stateless application/domain services."""

from __future__ import annotations

from abc import ABC

__all__ = ["BaseService"]


class BaseService(ABC):
    """Marker base class for stateless application/domain services.

    A "service" in Domain-Driven Design is an operation that does not
    naturally belong to any single
    :class:`~mineproductivity.core.entity.BaseEntity` or
    :class:`~mineproductivity.core.value_object.BaseValueObject` --
    typically because it coordinates several of them (repositories,
    factories, other aggregates). ``BaseService`` intentionally declares
    no abstract methods: the shape of a service's public API is entirely
    use-case-specific. Subclass it to document intent and to give
    tooling/tests a common type to discover services by.

    Examples
    --------
    >>> class TransferService(BaseService):
    ...     def transfer(self, amount: int) -> int:
    ...         return amount
    >>> TransferService().transfer(5)
    5
    """
