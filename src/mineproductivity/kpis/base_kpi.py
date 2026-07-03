"""``BaseKPI``: the root of every KPI, and the entire meaning of
"KPI-as-object" (Developer & Cookbook Guide Part III).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any, ClassVar

from mineproductivity.kpis.metadata import KPIMetadata
from mineproductivity.kpis.result import KPIResult

__all__ = ["BaseKPI"]


class BaseKPI(ABC):
    """The root of every KPI. A concrete leaf declares ``meta:
    ClassVar[KPIMetadata]`` and implements :meth:`_compute` -- everything
    else (validation, dependency declaration, result wrapping) is
    inherited.

    This mirrors Cookbook Part I, Ch. 6 exactly: "The category base... and
    the metadata do most of the work; ``_compute`` is the only logic you
    write." Instances are stateless across :meth:`compute` calls and
    therefore safe to share and invoke concurrently from multiple
    threads.
    """

    meta: ClassVar[KPIMetadata]

    @abstractmethod
    def _compute(self, rows: Sequence[Mapping[str, Any]]) -> float | None:
        """Pure function: ``rows`` -> a single scalar result, or ``None``
        if the KPI cannot be computed from the given rows (e.g. a zero
        denominator). MUST NOT raise for a "legitimately uncomputable"
        input -- return ``None`` and let :meth:`compute` attach the
        warning."""

    def compute(self, rows: Sequence[Mapping[str, Any]], window: str | None = None) -> KPIResult:
        """Validate ``rows`` against :meth:`_required_columns`, then call
        :meth:`_compute`, then wrap in a :class:`KPIResult`.

        This method is **not** overridden by leaf KPIs -- it is the one
        place the "qualify, don't coerce" stance (Cookbook Part I Ch. 6)
        is enforced uniformly: a missing required column becomes a
        warning-carrying result, never an exception.
        """
        required = self._required_columns()
        if required:
            missing = sorted(
                {column for column in required if not all(column in row for row in rows)}
            )
            if missing:
                return KPIResult(
                    code=self.meta.code,
                    value=None,
                    unit=self.meta.unit,
                    n=len(rows),
                    warnings=(f"missing required columns: {missing}",),
                )
        value = self._compute(rows)
        return KPIResult(code=self.meta.code, value=value, unit=self.meta.unit, n=len(rows))

    def _required_columns(self) -> tuple[str, ...]:
        """The row keys :meth:`_compute` requires to be present on every
        row before it is called. The default is an empty tuple (no
        pre-check); concrete leaf KPIs override this to declare exactly
        what they need (Standard Library field 9, "Required Events,"
        mapped to concrete column names by the leaf's own author, who
        alone knows which fields its ``_compute`` reads)."""
        return ()
