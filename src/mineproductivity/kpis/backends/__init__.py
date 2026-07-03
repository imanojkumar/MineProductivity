"""Vectorized execution backends: one pluggable
:class:`~mineproductivity.kpis.backends.base_backend.ExecutionBackend`
strategy per vectorization library, selected by process-level
configuration (design spec §28), never hard-coded.
"""

from __future__ import annotations

from mineproductivity.kpis.backends.base_backend import ExecutionBackend
from mineproductivity.kpis.backends.duckdb_backend import DuckDBBackend
from mineproductivity.kpis.backends.numpy_backend import NumPyBackend
from mineproductivity.kpis.backends.pandas_backend import PandasBackend
from mineproductivity.kpis.backends.polars_backend import PolarsBackend

__all__ = [
    "DuckDBBackend",
    "ExecutionBackend",
    "NumPyBackend",
    "PandasBackend",
    "PolarsBackend",
    "get_active_backend",
    "set_active_backend",
]

#: The process-selected ExecutionBackend (design spec §9's internal API,
#: ``kpis.backends._active_backend``). Default: pandas, per the
#: Developer Documentation's "pandas... will feel immediately familiar"
#: positioning (design spec §28) -- overridable via :func:`set_active_backend`.
_active_backend: ExecutionBackend = PandasBackend()


def get_active_backend() -> ExecutionBackend:
    """Return the process's currently active :class:`ExecutionBackend`."""
    return _active_backend


def set_active_backend(backend: ExecutionBackend) -> None:
    """Set the process's active :class:`ExecutionBackend` -- a
    ``config``-sourced setting in production (design spec §28); exposed
    directly here since the future ``config`` package does not exist yet
    (Documentation Governance Rule #005: only the minimal contract this
    package needs, not a forward dependency on ``config``)."""
    global _active_backend
    _active_backend = backend
