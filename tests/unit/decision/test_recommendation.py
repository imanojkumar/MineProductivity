"""Tests for mineproductivity.decision.recommendation.

Design spec §6 gives this module no public classes, functions, or API of
its own -- the ``Recommendation`` *type* lives in ``result.py`` (tested
in ``test_result.py``); this module holds only the generation logic
``ThresholdDecisionStrategy`` delegates to (the delegation itself is
covered end-to-end in ``test_strategy.py``). What is tested here is the
generation contract: field-for-field traceability to the ``Policy``/
rule names/evidence supplied (§15), tuple coercion of sequence inputs,
and the module's deliberately empty public surface.
"""

from __future__ import annotations

from mineproductivity.core import PredicateSpecification

from mineproductivity.decision import recommendation as recommendation_module
from mineproductivity.decision.policy import Policy
from mineproductivity.decision.recommendation import build_recommendation
from mineproductivity.decision.result import Recommendation


def _policy(code: str = "AVAIL.LowFleetAvailability") -> Policy:
    return Policy(
        code=code,
        rules={"low_oee": PredicateSpecification(lambda ctx: True)},
        strategy_code="STRATEGY.Threshold",
    )


class TestBuildRecommendation:
    def test_returns_a_recommendation(self) -> None:
        built = build_recommendation(
            policy=_policy(),
            triggered_rules=("low_oee",),
            evidence=("UTIL.OEE",),
            severity="high",
            model_code="STRATEGY.Threshold",
        )
        assert isinstance(built, Recommendation)

    def test_traceable_to_policy_rules_and_evidence(self) -> None:
        built = build_recommendation(
            policy=_policy(),
            triggered_rules=("low_oee", "negative_trend"),
            evidence=("UTIL.OEE", "TREND.Linear"),
            severity="critical",
            model_code="STRATEGY.Threshold",
        )
        assert built.policy_code == "AVAIL.LowFleetAvailability"
        assert built.triggered_rules == ("low_oee", "negative_trend")
        assert built.evidence == ("UTIL.OEE", "TREND.Linear")
        assert built.severity == "critical"
        assert built.model_code == "STRATEGY.Threshold"

    def test_summary_names_the_policy_and_every_triggered_rule(self) -> None:
        built = build_recommendation(
            policy=_policy(),
            triggered_rules=("low_oee", "negative_trend"),
            evidence=(),
            severity="medium",
            model_code="STRATEGY.Threshold",
        )
        assert (
            built.summary
            == "Policy 'AVAIL.LowFleetAvailability' triggered by rule(s): low_oee, negative_trend"
        )

    def test_sequence_inputs_are_coerced_to_tuples(self) -> None:
        built = build_recommendation(
            policy=_policy(),
            triggered_rules=["low_oee"],
            evidence=["UTIL.OEE"],
            severity="low",
            model_code="STRATEGY.Threshold",
        )
        assert built.triggered_rules == ("low_oee",)
        assert built.evidence == ("UTIL.OEE",)

    def test_explanation_is_not_prefilled(self) -> None:
        """Explanations are attached later by ``ExplanationBuilder``/
        ``ExplanationStage`` (§17), never fabricated at generation time."""
        built = build_recommendation(
            policy=_policy(),
            triggered_rules=("low_oee",),
            evidence=(),
            severity="low",
            model_code="STRATEGY.Threshold",
        )
        assert built.explanation is None


class TestModulePublicSurface:
    def test_module_exports_nothing_publicly(self) -> None:
        """Design spec §6: Public Classes: None, Public Functions: None,
        Public API: None -- ``build_recommendation`` is package-internal."""
        assert recommendation_module.__all__ == []

    def test_build_recommendation_is_not_top_level_public_api(self) -> None:
        import mineproductivity.decision as decision

        assert "build_recommendation" not in decision.__all__
