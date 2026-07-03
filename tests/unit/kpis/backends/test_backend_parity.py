"""Backend parity tests (design spec §29, §37.4): identical
``KPIResult.value`` across all four ``ExecutionBackend`` implementations
for every registered KPI, within documented floating-point tolerance."""

from __future__ import annotations

import pytest

from mineproductivity.kpis._registry import REGISTRY
from mineproductivity.kpis.backends import (
    DuckDBBackend,
    ExecutionBackend,
    NumPyBackend,
    PandasBackend,
    PolarsBackend,
)
from mineproductivity.kpis.composite import CompositeKPI
from mineproductivity.kpis.metadata import Aggregation

_BACKENDS: tuple[ExecutionBackend, ...] = (
    PandasBackend(),
    NumPyBackend(),
    PolarsBackend(),
    DuckDBBackend(),
)

_LEAF_CODES_WITH_FIXTURE_ROWS: dict[str, list[dict[str, object]]] = {
    "PROD.TPH": [
        {"payload_t": 15600.0, "operating_h": 12.0},
        {"payload_t": 6600.0, "operating_h": 6.0},
    ],
    "MAINT.MTTR": [{"duration_h": 3.0}, {"duration_h": 5.0}],
    "HAUL.TruckCycleTime": [
        {
            "queue_min": 1.5,
            "spot_min": 0.5,
            "load_min": 2.5,
            "haul_min": 8.0,
            "dump_min": 1.0,
            "return_min": 6.0,
        }
    ],
    "DISP.TotalDelayHours": [{"duration_h": 2.0}, {"duration_h": 1.5}],
    "QUAL.OreProportion": [{"material_type": "ore"}, {"material_type": "waste"}],
}


class TestBackendParityForEveryLeafKPI:
    @pytest.mark.parametrize("code", sorted(_LEAF_CODES_WITH_FIXTURE_ROWS))
    def test_all_four_backends_produce_the_identical_value(self, code: str) -> None:
        rows = _LEAF_CODES_WITH_FIXTURE_ROWS[code]
        kpi_cls = REGISTRY.get(code)
        assert not issubclass(kpi_cls, CompositeKPI)
        columns = tuple(dict.fromkeys(key for row in rows for key in row))

        values: set[float] = set()
        for backend in _BACKENDS:
            table = backend.assemble(rows, columns)
            round_tripped = list(backend.to_rows(table))
            result = kpi_cls().compute(round_tripped)
            assert result.value is not None
            values.add(round(result.value, 6))
        assert len(values) == 1, f"{code}: backend parity violated -- {values}"


class TestGroupAndAggregateParityAcrossBackends:
    def test_additive_grouping_matches_across_all_four_backends(self) -> None:
        rows = [
            {"equipment_id": "HT-1", "payload_t": 100.0},
            {"equipment_id": "HT-1", "payload_t": 50.0},
            {"equipment_id": "HT-2", "payload_t": 200.0},
        ]
        columns = ("equipment_id", "payload_t")

        totals_by_backend: dict[str, dict[str, float]] = {}
        for backend in _BACKENDS:
            table = backend.assemble(rows, columns)
            grouped = backend.group_and_aggregate(table, ("equipment_id",), Aggregation.ADDITIVE)
            result_rows = list(backend.to_rows(grouped))
            totals_by_backend[type(backend).__name__] = {
                row["equipment_id"]: row["payload_t"] for row in result_rows
            }

        reference = totals_by_backend["PandasBackend"]
        for name, totals in totals_by_backend.items():
            assert totals == reference, (
                f"{name} disagrees with PandasBackend: {totals} != {reference}"
            )
