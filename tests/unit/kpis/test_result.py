"""Tests for mineproductivity.kpis.result."""

from __future__ import annotations

import pytest

from mineproductivity.kpis.backends import PandasBackend, get_active_backend, set_active_backend
from mineproductivity.kpis.result import KPIResult


class TestKPIResultConstruction:
    def test_minimal_construction(self) -> None:
        result = KPIResult(code="PROD.TPH", value=1212.1, unit="t/h", n=48)
        assert result.value == 1212.1
        assert result.n == 48
        assert result.warnings == ()

    def test_none_value_with_warnings(self) -> None:
        result = KPIResult(
            code="PROD.TPH", value=None, unit="t/h", warnings=("zero operating hours",)
        )
        assert result.value is None
        assert result.warnings == ("zero operating hours",)

    def test_scope_is_frozen_into_a_read_only_mapping(self) -> None:
        result = KPIResult(code="X", value=1.0, unit="u", scope={"shift": "A"})
        assert result.scope["shift"] == "A"
        with pytest.raises(TypeError):
            result.scope["shift"] = "B"  # type: ignore[index]

    def test_structural_equality(self) -> None:
        a = KPIResult(code="X", value=1.0, unit="u")
        b = KPIResult(code="X", value=1.0, unit="u")
        assert a == b


class TestKPIResultBackendDelegation:
    def teardown_method(self) -> None:
        set_active_backend(PandasBackend())

    def test_to_frame_delegates_to_the_active_backend(self) -> None:
        result = KPIResult(code="PROD.TPH", value=1212.1, unit="t/h", n=48)
        frame = result.to_frame()
        assert len(frame) == 1

    def test_to_frame_uses_whatever_backend_is_currently_active(self) -> None:
        from mineproductivity.kpis.backends import NumPyBackend

        set_active_backend(NumPyBackend())
        result = KPIResult(code="PROD.TPH", value=1212.1, unit="t/h", n=48)
        frame = result.to_frame()
        assert frame["value"][0] == 1212.1
        assert isinstance(get_active_backend(), NumPyBackend)

    def test_plot_raises_not_implemented_by_design(self) -> None:
        result = KPIResult(code="PROD.TPH", value=1.0, unit="t/h")
        with pytest.raises(NotImplementedError):
            result.plot()

    def test_pareto_raises_not_implemented_by_design(self) -> None:
        result = KPIResult(code="PROD.TPH", value=1.0, unit="t/h")
        with pytest.raises(NotImplementedError):
            result.pareto()
