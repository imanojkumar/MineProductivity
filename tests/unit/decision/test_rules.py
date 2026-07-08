"""Tests for mineproductivity.decision.rules."""

from __future__ import annotations

from mineproductivity.core import PredicateSpecification
from mineproductivity.kpis import KPIResult

from mineproductivity.decision.abstractions import DecisionContext
from mineproductivity.decision.policy import Policy
from mineproductivity.decision.rules import Rule, RuleEngine, RuleEngineStage


def _context(value: float = 1.0) -> DecisionContext:
    return DecisionContext(
        kpi_results=(KPIResult(code="UTIL.OEE", value=value, unit=""),),
        analytics_results=(),
        scope={},
    )


_ALWAYS_TRUE: Rule = PredicateSpecification(lambda ctx: True)
_ALWAYS_FALSE: Rule = PredicateSpecification(lambda ctx: False)


class TestRuleComposition:
    """Design spec §11: zero new composition operators -- reuses
    core.BaseSpecification's own &/|/~ exactly."""

    def test_and_composition(self) -> None:
        rule = _ALWAYS_TRUE & _ALWAYS_TRUE
        assert rule.is_satisfied_by(_context())

    def test_and_composition_short_circuits_false(self) -> None:
        rule = _ALWAYS_TRUE & _ALWAYS_FALSE
        assert not rule.is_satisfied_by(_context())

    def test_or_composition(self) -> None:
        rule = _ALWAYS_FALSE | _ALWAYS_TRUE
        assert rule.is_satisfied_by(_context())

    def test_not_composition(self) -> None:
        rule = ~_ALWAYS_FALSE
        assert rule.is_satisfied_by(_context())

    def test_predicate_specification_reads_context_fields(self) -> None:
        rule: Rule = PredicateSpecification(
            lambda ctx: any(r.value is not None and r.value < 0.65 for r in ctx.kpi_results)
        )
        assert rule.is_satisfied_by(_context(0.5))
        assert not rule.is_satisfied_by(_context(0.9))


class TestRuleEngineEvaluate:
    def test_empty_rules_returns_empty_sequence(self) -> None:
        assert RuleEngine().evaluate({}, _context()) == ()

    def test_single_triggered_rule(self) -> None:
        triggered = RuleEngine().evaluate({"always": _ALWAYS_TRUE}, _context())
        assert triggered == ("always",)

    def test_single_non_triggered_rule(self) -> None:
        triggered = RuleEngine().evaluate({"never": _ALWAYS_FALSE}, _context())
        assert triggered == ()

    def test_only_satisfied_rules_are_returned(self) -> None:
        triggered = RuleEngine().evaluate({"yes": _ALWAYS_TRUE, "no": _ALWAYS_FALSE}, _context())
        assert triggered == ("yes",)

    def test_result_is_in_stable_sorted_order(self) -> None:
        rules = {"zebra": _ALWAYS_TRUE, "alpha": _ALWAYS_TRUE, "mango": _ALWAYS_TRUE}
        triggered = RuleEngine().evaluate(rules, _context())
        assert triggered == ("alpha", "mango", "zebra")

    def test_a_malformed_rule_is_isolated_from_the_rest(self) -> None:
        """Rule-isolation proof (design spec §34): a single rule raising
        during is_satisfied_by must never prevent evaluation of the
        remaining rules in the same Policy."""

        class _BrokenRule:
            def is_satisfied_by(self, candidate: object) -> bool:
                raise ValueError("boom")

        rules = {"broken": _BrokenRule(), "healthy": _ALWAYS_TRUE}  # type: ignore[dict-item]
        triggered = RuleEngine().evaluate(rules, _context())  # type: ignore[arg-type]
        assert triggered == ("healthy",)

    def test_multiple_malformed_rules_are_all_isolated(self) -> None:
        class _BrokenRule:
            def is_satisfied_by(self, candidate: object) -> bool:
                raise RuntimeError("boom")

        rules = {
            "broken_a": _BrokenRule(),
            "broken_b": _BrokenRule(),
            "healthy": _ALWAYS_TRUE,
        }
        triggered = RuleEngine().evaluate(rules, _context())  # type: ignore[arg-type]
        assert triggered == ("healthy",)


class TestRuleEngineStage:
    def _policy(self, **overrides: object) -> Policy:
        fields: dict[str, object] = {
            "code": "TEST.Policy",
            "rules": {"always": _ALWAYS_TRUE},
            "strategy_code": "STRATEGY.Threshold",
        }
        fields.update(overrides)
        return Policy(**fields)  # type: ignore[arg-type]

    def test_process_attaches_triggered_rule_names(self) -> None:
        stage = RuleEngineStage(policy=self._policy())
        context = _context()
        result = stage.process(context)
        assert result.triggered_rules == ("always",)

    def test_process_returns_the_same_context_object(self) -> None:
        stage = RuleEngineStage(policy=self._policy())
        context = _context()
        result = stage.process(context)
        assert result is context

    def test_process_with_no_triggered_rules(self) -> None:
        stage = RuleEngineStage(policy=self._policy(rules={"never": _ALWAYS_FALSE}))
        context = _context()
        result = stage.process(context)
        assert result.triggered_rules == ()

    def test_repr_includes_policy(self) -> None:
        stage = RuleEngineStage(policy=self._policy())
        assert "TEST.Policy" in repr(stage)
