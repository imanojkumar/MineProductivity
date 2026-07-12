"""``DashboardRepository``: where dashboards are stored (design spec
§22).

A literal ``type`` alias over ``core.BaseRepository[Dashboard, str]``
-- not a new ABC, not a structural echo -- the fifth occurrence of
this exact reuse in the series (after ``digital_twin.TwinRepository``,
``simulation.SimulationRunRepository``,
``optimization.OptimizationRunRepository``, and
``agents.TaskRepository``). The reference implementation is
``core.InMemoryRepository[Dashboard, str]()``, reused as-is with zero
new persistence code; it provides **no** locking of its own -- a
production-grade implementation MUST serialize concurrent writes for
the same ``id`` (design spec §29). No equivalent repository exists
for ``Report`` -- a produced-once value object, never independently
persisted by this package (§13).
"""

from __future__ import annotations

from mineproductivity.core import BaseRepository

from mineproductivity.visualization.dashboard import Dashboard

__all__ = ["DashboardRepository"]

type DashboardRepository = BaseRepository[Dashboard, str]
