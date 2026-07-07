"""Tests for mineproductivity.analytics.quality."""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import pytest

from mineproductivity.events.store import _InMemoryEventStore

from mineproductivity.analytics.abstractions import AnalyticsContext
from mineproductivity.analytics.pipeline import AnalyticsPipeline, ModelStage, PipelineStage
from mineproductivity.analytics.quality import (
    DataQualityScorer,
    DataQualityStage,
    MissingDataPolicy,
)
from mineproductivity.analytics.result import AnalyticsResult, DataQualityScore
from mineproductivity.analytics.timeseries import TimeSeries, TimeSeriesPoint
from mineproductivity.analytics.trend import LinearTrendModel

DAY_1 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _context() -> AnalyticsContext:
    return AnalyticsContext(event_store=_InMemoryEventStore())


def _series(
    rows: list[dict[str, str]],
    *,
    values: list[float] | None = None,
    step: timedelta = timedelta(days=1),
) -> TimeSeries:
    vals = values if values is not None else [1.0] * len(rows)
    return TimeSeries(
        points=tuple(
            TimeSeriesPoint(timestamp=DAY_1 + step * i, value=v, scope=scope)
            for i, (scope, v) in enumerate(zip(rows, vals, strict=True))
        )
    )


class TestDataQualityScorerCompleteData:
    def test_fully_present_and_valid_rows_score_perfectly(self) -> None:
        rows = [
            {"payload_t": 220.0, "operating_h": 8.0},
            {"payload_t": 210.0, "operating_h": 7.5},
        ]
        score = DataQualityScorer().score(rows, required_columns=("payload_t", "operating_h"))
        assert isinstance(score, DataQualityScore)
        assert score.completeness == 1.0
        assert score.validity == 1.0
        assert score.overall_score == 1.0
        assert score.reasons == ()


class TestDataQualityScorerMissingObservations:
    def test_all_rows_missing_the_required_column_scores_zero(self) -> None:
        rows = [{"payload_t": None}, {"other_field": 1.0}]
        score = DataQualityScorer().score(rows, required_columns=("payload_t",))
        assert score.completeness == 0.0
        assert score.validity == 0.0
        assert score.overall_score == 0.0
        assert len(score.reasons) == 2

    def test_missing_key_and_explicit_none_are_both_missing(self) -> None:
        rows = [{"payload_t": None}, {}]
        score = DataQualityScorer().score(rows, required_columns=("payload_t",))
        assert score.completeness == 0.0
        assert all("missing required column" in reason for reason in score.reasons)


class TestDataQualityScorerPartiallyMissing:
    def test_hand_counted_completeness_and_validity(self) -> None:
        """4 rows x 2 required columns = 8 slots. payload_t missing on row
        1; operating_h is present but invalid (NaN) on row 2. Hand count:
        7/8 present -> completeness=0.875; of the 7 present, 6 valid ->
        validity=6/7."""
        rows = [
            {"payload_t": 220.0, "operating_h": 8.0},
            {"payload_t": None, "operating_h": 7.0},
            {"payload_t": 200.0, "operating_h": float("nan")},
            {"payload_t": 190.0, "operating_h": 6.0},
        ]
        score = DataQualityScorer().score(rows, required_columns=("payload_t", "operating_h"))
        assert score.completeness == pytest.approx(7 / 8)
        assert score.validity == pytest.approx(6 / 7)
        assert score.overall_score == pytest.approx((7 / 8) * (6 / 7))
        assert len(score.reasons) == 2
        assert any("row 1" in r and "missing" in r for r in score.reasons)
        assert any("row 2" in r and "invalid" in r for r in score.reasons)


class TestDataQualityScorerEmptyInputs:
    def test_empty_rows_scores_vacuously_perfect_with_a_reason(self) -> None:
        score = DataQualityScorer().score([], required_columns=("payload_t",))
        assert score.completeness == 1.0
        assert score.validity == 1.0
        assert score.overall_score == 1.0
        assert "no rows to score" in score.reasons[0]

    def test_empty_required_columns_scores_vacuously_perfect_with_a_reason(self) -> None:
        score = DataQualityScorer().score([{"payload_t": 1.0}], required_columns=())
        assert score.completeness == 1.0
        assert score.validity == 1.0
        assert score.overall_score == 1.0
        assert "no required columns" in score.reasons[0]

    def test_both_empty(self) -> None:
        score = DataQualityScorer().score([], required_columns=())
        assert score.overall_score == 1.0


class TestDataQualityScorerValidity:
    def test_nan_and_infinite_numbers_are_invalid(self) -> None:
        rows = [{"x": float("nan")}, {"x": float("inf")}, {"x": float("-inf")}]
        score = DataQualityScorer().score(rows, required_columns=("x",))
        assert score.completeness == 1.0  # all present
        assert score.validity == 0.0  # none valid

    def test_blank_string_is_invalid_but_present(self) -> None:
        rows = [{"pit": "   "}, {"pit": "north"}]
        score = DataQualityScorer().score(rows, required_columns=("pit",))
        assert score.completeness == 1.0
        assert score.validity == 0.5

    def test_boolean_value_is_trivially_valid(self) -> None:
        rows = [{"flag": True}, {"flag": False}]
        score = DataQualityScorer().score(rows, required_columns=("flag",))
        assert score.validity == 1.0

    def test_finite_int_is_valid(self) -> None:
        rows = [{"n": 5}]
        score = DataQualityScorer().score(rows, required_columns=("n",))
        assert score.validity == 1.0

    def test_a_present_value_of_an_unrecognized_type_is_trivially_valid(self) -> None:
        """Only numeric and string values get a generic basic-sanity
        check (kpis spec §10.3's own scope boundary: this is not a
        domain-semantic validator) -- any other present, non-null type
        (e.g. a list) is trivially valid."""
        rows = [{"tags": ["a", "b"]}]
        score = DataQualityScorer().score(rows, required_columns=("tags",))
        assert score.validity == 1.0


class TestMissingDataPolicyEnum:
    def test_exactly_four_members(self) -> None:
        assert {member.name for member in MissingDataPolicy} == {
            "EXCLUDE",
            "FLAG_ONLY",
            "FORWARD_FILL",
            "MEAN_FILL",
        }

    def test_values_are_lowercase_snake_case(self) -> None:
        assert MissingDataPolicy.EXCLUDE.value == "exclude"
        assert MissingDataPolicy.FLAG_ONLY.value == "flag_only"
        assert MissingDataPolicy.FORWARD_FILL.value == "forward_fill"
        assert MissingDataPolicy.MEAN_FILL.value == "mean_fill"


class TestDataQualityStageFlagOnly:
    def test_series_passes_through_unchanged(self) -> None:
        series = _series([{"pit": "north"}, {}, {"pit": "south"}])
        stage = DataQualityStage(required_columns=("pit",))
        result = stage.process(series, context=_context())
        assert isinstance(result, TimeSeries)
        assert result == series


class TestDataQualityStageExclude:
    def test_incomplete_points_are_dropped(self) -> None:
        series = _series([{"pit": "north"}, {}, {"pit": "south"}])
        stage = DataQualityStage(
            required_columns=("pit",), missing_data_policy=MissingDataPolicy.EXCLUDE
        )
        result = stage.process(series, context=_context())
        assert isinstance(result, TimeSeries)
        assert len(result) == 2
        assert all(point.scope.get("pit") for point in result.points)

    def test_dropping_everything_yields_a_legal_empty_series(self) -> None:
        series = _series([{}, {}])
        stage = DataQualityStage(
            required_columns=("pit",), missing_data_policy=MissingDataPolicy.EXCLUDE
        )
        result = stage.process(series, context=_context())
        assert isinstance(result, TimeSeries)
        assert len(result) == 0

    def test_excludes_on_non_finite_required_value_too(self) -> None:
        """EXCLUDE is not limited to scope columns -- a non-finite
        ``value`` is exactly as "missing" as an absent scope key when
        ``"value"`` itself is declared required."""
        series = _series([{}, {}], values=[1.0, float("nan")])
        stage = DataQualityStage(
            required_columns=("value",), missing_data_policy=MissingDataPolicy.EXCLUDE
        )
        result = stage.process(series, context=_context())
        assert isinstance(result, TimeSeries)
        assert len(result) == 1
        assert result.points[0].value == 1.0

    def test_blank_scope_value_is_excluded_same_as_absent(self) -> None:
        series = _series([{"pit": "north"}, {"pit": "  "}])
        stage = DataQualityStage(
            required_columns=("pit",), missing_data_policy=MissingDataPolicy.EXCLUDE
        )
        result = stage.process(series, context=_context())
        assert isinstance(result, TimeSeries)
        assert len(result) == 1


class TestDataQualityStageForwardFill:
    def test_missing_scope_column_is_carried_forward(self) -> None:
        series = _series([{"pit": "north"}, {}, {}])
        stage = DataQualityStage(
            required_columns=("pit",), missing_data_policy=MissingDataPolicy.FORWARD_FILL
        )
        result = stage.process(series, context=_context())
        assert isinstance(result, TimeSeries)
        assert [p.scope.get("pit") for p in result.points] == ["north", "north", "north"]

    def test_leading_gap_with_no_prior_value_stays_unfilled(self) -> None:
        series = _series([{}, {"pit": "north"}])
        stage = DataQualityStage(
            required_columns=("pit",), missing_data_policy=MissingDataPolicy.FORWARD_FILL
        )
        result = stage.process(series, context=_context())
        assert isinstance(result, TimeSeries)
        assert "pit" not in result.points[0].scope

    def test_non_finite_value_is_carried_forward(self) -> None:
        series = _series([{}, {}], values=[10.0, float("nan")])
        stage = DataQualityStage(
            required_columns=("value",), missing_data_policy=MissingDataPolicy.FORWARD_FILL
        )
        result = stage.process(series, context=_context())
        assert isinstance(result, TimeSeries)
        assert result.points[1].value == 10.0

    def test_blank_scope_value_is_filled_and_does_not_poison_later_points(self) -> None:
        """Regression: a present-but-blank required scope value must be
        treated as missing (same as an absent key) for fill purposes,
        and must never overwrite the last genuinely valid observation --
        otherwise a later, truly-absent point would incorrectly inherit
        the blank instead of the last real value."""
        series = _series([{"pit": "north"}, {"pit": "   "}, {}])
        stage = DataQualityStage(
            required_columns=("pit",), missing_data_policy=MissingDataPolicy.FORWARD_FILL
        )
        result = stage.process(series, context=_context())
        assert isinstance(result, TimeSeries)
        assert [p.scope.get("pit") for p in result.points] == ["north", "north", "north"]


class TestDataQualityStageMeanFill:
    def test_non_finite_value_is_replaced_by_the_series_mean_of_finite_values(self) -> None:
        series = _series([{}, {}, {}], values=[10.0, float("nan"), 20.0])
        stage = DataQualityStage(
            required_columns=("value",), missing_data_policy=MissingDataPolicy.MEAN_FILL
        )
        result = stage.process(series, context=_context())
        assert isinstance(result, TimeSeries)
        assert result.points[1].value == pytest.approx(15.0)  # mean of 10.0, 20.0

    def test_all_values_non_finite_leaves_them_unfilled(self) -> None:
        series = _series([{}, {}], values=[float("nan"), float("inf")])
        stage = DataQualityStage(
            required_columns=("value",), missing_data_policy=MissingDataPolicy.MEAN_FILL
        )
        result = stage.process(series, context=_context())
        assert isinstance(result, TimeSeries)
        assert math.isnan(result.points[0].value)
        assert math.isinf(result.points[1].value)

    def test_missing_scope_column_degrades_to_forward_fill_since_no_mean_exists_for_strings(
        self,
    ) -> None:
        series = _series([{"pit": "north"}, {}])
        stage = DataQualityStage(
            required_columns=("pit",), missing_data_policy=MissingDataPolicy.MEAN_FILL
        )
        result = stage.process(series, context=_context())
        assert isinstance(result, TimeSeries)
        assert result.points[1].scope["pit"] == "north"


class TestDataQualityStageGating:
    def test_score_at_or_above_min_score_passes_through_as_a_timeseries(self) -> None:
        series = _series([{"pit": "north"}, {"pit": "south"}])
        stage = DataQualityStage(required_columns=("pit",), min_score=1.0)
        result = stage.process(series, context=_context())
        assert isinstance(result, TimeSeries)

    def test_score_below_min_score_gates_with_the_dataqualityscore_itself(self) -> None:
        series = _series([{"pit": "north"}, {}])
        stage = DataQualityStage(required_columns=("pit",), min_score=0.9)
        result = stage.process(series, context=_context())
        assert isinstance(result, DataQualityScore)
        assert result.overall_score < 0.9

    def test_default_min_score_of_zero_never_gates(self) -> None:
        series = _series([{}, {}])  # every point missing every required column
        stage = DataQualityStage(required_columns=("pit",))
        result = stage.process(series, context=_context())
        assert isinstance(result, TimeSeries)

    def test_gating_short_circuits_a_non_terminal_pipeline_stage(self) -> None:
        """When DataQualityStage gates and is followed by a ModelStage,
        AnalyticsPipeline.run's existing non-terminal-AnalyticsResult
        rule (established in the Foundation phase) rejects the pipeline
        run -- reused, not reinvented, for the 'gates a pipeline on a
        threshold' behavior design spec §25 describes."""
        series = _series([{"pit": "north"}, {}], values=[1.0, 2.0])
        pipeline = AnalyticsPipeline(
            stages=(
                DataQualityStage(required_columns=("pit",), min_score=0.9),
                ModelStage(LinearTrendModel()),
            )
        )
        result = pipeline.run(series, context=_context())
        assert result.is_err

    def test_acceptable_score_flows_through_to_a_terminal_modelstage(self) -> None:
        """The design spec §9 worked example's exact shape: DataQualityStage
        followed by ModelStage, quality acceptable -> the pipeline
        completes successfully with the model's own result, not the
        DataQualityScore."""
        series = _series(
            [{"pit": "north"}, {"pit": "north"}, {"pit": "north"}], values=[1.0, 2.0, 3.0]
        )
        pipeline = AnalyticsPipeline(
            stages=(
                DataQualityStage(required_columns=("pit",)),
                ModelStage(LinearTrendModel()),
            )
        )
        result = pipeline.run(series, context=_context())
        assert result.is_ok
        trend = result.unwrap()
        assert trend.model_code == LinearTrendModel.meta.code


class TestDataQualityStageEmptySeries:
    def test_empty_series_scores_vacuously_and_passes_through(self) -> None:
        stage = DataQualityStage(required_columns=("pit",))
        result = stage.process(TimeSeries(points=()), context=_context())
        assert isinstance(result, TimeSeries)
        assert len(result) == 0

    def test_empty_series_with_a_high_min_score_still_never_gates(self) -> None:
        """An empty series has nothing to score, so DataQualityScorer's
        own vacuous-perfect-score convention applies -- gating never
        fires regardless of min_score."""
        stage = DataQualityStage(required_columns=("pit",), min_score=1.0)
        result = stage.process(TimeSeries(points=()), context=_context())
        assert isinstance(result, TimeSeries)


class TestDataQualityStageSinglePoint:
    def test_single_complete_point(self) -> None:
        series = _series([{"pit": "north"}])
        stage = DataQualityStage(required_columns=("pit",), min_score=1.0)
        result = stage.process(series, context=_context())
        assert isinstance(result, TimeSeries)
        assert len(result) == 1

    def test_single_incomplete_point_with_forward_fill_has_nothing_to_fill_from(self) -> None:
        series = _series([{}])
        stage = DataQualityStage(
            required_columns=("pit",), missing_data_policy=MissingDataPolicy.FORWARD_FILL
        )
        result = stage.process(series, context=_context())
        assert isinstance(result, TimeSeries)
        assert "pit" not in result.points[0].scope


class TestDataQualityStageBoundaryConditions:
    def test_score_exactly_equal_to_min_score_does_not_gate(self) -> None:
        series = _series([{"pit": "north"}, {}])  # completeness=0.5, validity=1.0 -> overall=0.5
        stage = DataQualityStage(required_columns=("pit",), min_score=0.5)
        result = stage.process(series, context=_context())
        assert isinstance(result, TimeSeries)

    def test_score_just_below_min_score_gates(self) -> None:
        series = _series([{"pit": "north"}, {}])  # overall=0.5
        stage = DataQualityStage(required_columns=("pit",), min_score=0.500001)
        result = stage.process(series, context=_context())
        assert isinstance(result, DataQualityScore)


class TestDataQualityStageMetadata:
    def test_repr_includes_constructor_state(self) -> None:
        stage = DataQualityStage(
            required_columns=("pit", "shift"),
            missing_data_policy=MissingDataPolicy.EXCLUDE,
            min_score=0.8,
        )
        text = repr(stage)
        assert "pit" in text
        assert "EXCLUDE" in text or "exclude" in text
        assert "0.8" in text

    def test_is_a_pipeline_stage(self) -> None:
        assert isinstance(DataQualityStage(required_columns=()), PipelineStage)


class TestPublicApiValidation:
    def test_symbols_are_exported(self) -> None:
        import mineproductivity.analytics as analytics

        assert "DataQualityScorer" in analytics.__all__
        assert "DataQualityStage" in analytics.__all__
        assert "MissingDataPolicy" in analytics.__all__
        assert analytics.DataQualityScorer is DataQualityScorer
        assert analytics.DataQualityStage is DataQualityStage
        assert analytics.MissingDataPolicy is MissingDataPolicy

    def test_dataqualityscore_result_type_is_reused_not_duplicated(self) -> None:
        score = DataQualityScorer().score([], required_columns=())
        assert isinstance(score, AnalyticsResult)
        assert isinstance(score, DataQualityScore)
