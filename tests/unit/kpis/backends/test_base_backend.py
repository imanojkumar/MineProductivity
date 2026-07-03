"""Tests for mineproductivity.kpis.backends.base_backend."""

from __future__ import annotations

import pytest

from mineproductivity.kpis.backends.base_backend import ExecutionBackend
from mineproductivity.kpis.backends.pandas_backend import PandasBackend
from mineproductivity.kpis.result import KPIResult


class TestExecutionBackendIsAbstract:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            ExecutionBackend()  # type: ignore[abstract]


class TestResultToFrame:
    def test_builds_a_one_row_table_from_a_result(self) -> None:
        backend = PandasBackend()
        result = KPIResult(code="PROD.TPH", value=1212.1, unit="t/h", n=48)
        frame = backend.result_to_frame(result)
        assert len(frame) == 1
        assert frame["code"].iloc[0] == "PROD.TPH"
        assert frame["value"].iloc[0] == 1212.1


class TestPlotAndParetoRaiseByDesign:
    def test_plot_result_raises_not_implemented(self) -> None:
        backend = PandasBackend()
        result = KPIResult(code="X", value=1.0, unit="u")
        with pytest.raises(NotImplementedError, match="visualization"):
            backend.plot_result(result)

    def test_pareto_result_raises_not_implemented(self) -> None:
        backend = PandasBackend()
        result = KPIResult(code="X", value=1.0, unit="u")
        with pytest.raises(NotImplementedError, match="visualization"):
            backend.pareto_result(result)
