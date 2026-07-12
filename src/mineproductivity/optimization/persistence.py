"""Where optimization runs are stored (design spec §24).

Reuse audit: ``OptimizationRunRepository`` **is**
``core.BaseRepository[OptimizationRun, str]`` -- a literal ``type``
alias, mirroring ``simulation.SimulationRunRepository``/
``digital_twin.TwinRepository`` (spec 09 §24, spec 08 §20). The
reference implementation is ``core.InMemoryRepository``, unchanged,
with zero new persistence code; it provides no locking of its own, and
a production backend MUST serialize concurrent writes for the same
``id`` (design spec §32).
"""

from __future__ import annotations

from mineproductivity.core import BaseRepository

from mineproductivity.optimization.run import OptimizationRun

__all__ = ["OptimizationRunRepository"]

type OptimizationRunRepository = BaseRepository[OptimizationRun, str]
"""The storage contract for run instances, keyed by their own identity
(design spec §24)."""
