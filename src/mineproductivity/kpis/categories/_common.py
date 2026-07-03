"""Shared namespace-conformance enforcement for every category base
class (design spec §10.4: "Each category base contributes no behavior
beyond documentation and a namespace convention check").
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mineproductivity.kpis.exceptions import KPIValidationError

if TYPE_CHECKING:
    from mineproductivity.kpis.base_kpi import BaseKPI

__all__ = ["enforce_namespace"]


def enforce_namespace(cls: "type[BaseKPI]", *namespaces: str) -> None:
    """Raise if ``cls`` declares its own ``meta`` whose ``code`` does not
    start with one of ``namespaces`` -- runs from each category base's
    ``__init_subclass__``, so a namespace violation fails at class
    -definition (import) time, not first use. More than one namespace is
    accepted for the categories the design specification itself
    describes as spanning several controlled namespaces (e.g.
    ``EnergyKPI`` covers ``ENERGY``/``CARBON``/``WATER``).

    Abstract intermediate classes that do not yet declare their own
    ``meta`` (only inherit the unset ``ClassVar`` from ``BaseKPI``) are
    skipped -- the check only applies once a class actually claims a
    ``code``.
    """
    if "meta" not in cls.__dict__:
        return
    code = cls.meta.code
    if not any(code == namespace or code.startswith(f"{namespace}.") for namespace in namespaces):
        raise KPIValidationError(
            f"{cls.__name__}.meta.code {code!r} must start with one of {namespaces!r}"
        )
