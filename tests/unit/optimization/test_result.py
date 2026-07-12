"""Tests for mineproductivity.optimization.result."""

from __future__ import annotations

from datetime import timezone

import pytest

from mineproductivity.core.serialization import DataclassSerializer, to_dict
from mineproductivity.optimization.result import OptimizationResult, ParetoResult


class TestOptimizationResult:
    def test_defaults(self) -> None:
        result = OptimizationResult()
        assert result.run_id == ""
        assert result.feasible is True
        assert result.objective_value is None
        assert dict(result.solution) == {}
        assert result.computed_at.tzinfo is timezone.utc

    def test_infeasibility_is_a_flag_never_an_exception_shape(self) -> None:
        """Design spec §28."""
        result = OptimizationResult(
            feasible=False, warnings=("constraint set admits no feasible point",)
        )
        assert result.feasible is False
        assert result.warnings

    def test_solution_is_frozen(self) -> None:
        result = OptimizationResult(solution={"trucks": 7.0})
        with pytest.raises(TypeError):
            result.solution["more"] = 1.0  # type: ignore[index]

    def test_round_trips_via_dataclass_serializer(self) -> None:
        serializer = DataclassSerializer(OptimizationResult)
        original = OptimizationResult(objective_value=42.0, solution={"trucks": 7.0})
        assert serializer.deserialize(serializer.serialize(original)) == original

    def test_to_dict_generic_no_bespoke_method(self) -> None:
        assert "to_dict" not in OptimizationResult.__dict__
        assert to_dict(OptimizationResult())["feasible"] is True


class TestParetoResult:
    def test_front_carries_the_trade_off_surface(self) -> None:
        """Design spec §18: the envelope defaults stay untouched; the
        surface lives entirely in ``front``."""
        pareto = ParetoResult(
            front=(
                OptimizationResult(objective_value=1.0),
                OptimizationResult(objective_value=2.0),
            )
        )
        assert issubclass(ParetoResult, OptimizationResult)
        assert len(pareto.front) == 2
        assert pareto.objective_value is None
