"""Where simulation runs are stored (design spec §24).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``SimulationRunRepository`` is not a new ABC, not a structural echo,
and not a subclass -- it **is** ``core.BaseRepository[SimulationRun, str]``,
used directly, because ``SimulationRun`` genuinely satisfies
``BaseRepository``'s ``TEntity: BaseEntity[Any]`` bound, exactly
mirroring ``digital_twin.TwinRepository``'s own identical reuse
(spec 08 §20; ADR-0009's recorded trade-off). The reference
implementation is ``core.InMemoryRepository[SimulationRun, str]()``,
reused as-is with zero new persistence code; it provides no locking of
its own, and a production-grade backend MUST serialize concurrent
writes for the same ``id`` (design spec §32).
"""

from __future__ import annotations

from mineproductivity.core import BaseRepository

from mineproductivity.simulation.run import SimulationRun

__all__ = ["SimulationRunRepository"]

type SimulationRunRepository = BaseRepository[SimulationRun, str]
"""The storage contract for run instances, keyed by their own identity
-- a literal ``type`` alias over
``core.BaseRepository[SimulationRun, str]``, never a parallel
simulation-specific repository ABC (design spec §24)."""
