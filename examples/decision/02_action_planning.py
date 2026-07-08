"""``ActionPrioritizer`` + ``ActionPlanner``: from ranked
recommendations to a dependency-respecting, topologically-ordered
``ActionPlan`` -- and the loud, ``Result.err`` rejection of a cyclic
dependency declaration.

Ranking (design spec §16, "which recommendation is best") and
prioritization (§20, "given limited capacity, which action happens
first") stay two distinct questions throughout -- conflating them is a
recorded anti-pattern (§33).

Run: python examples/decision/02_action_planning.py
"""

from __future__ import annotations

from mineproductivity.decision import (
    ActionPlanner,
    ActionPrioritizer,
    Recommendation,
    WeightedScoreRanking,
)


def main() -> None:
    print("--- 1. Three recommendations, produced earlier by decision strategies ---")
    recommendations = (
        Recommendation(
            model_code="STRATEGY.Threshold",
            policy_code="AVAIL.LowFleetAvailability",
            triggered_rules=("oee_below_target", "oee_trend_declining"),
            summary="Investigate declining fleet availability",
            severity="high",
            evidence=("UTIL.OEE", "TREND.Linear"),
        ),
        Recommendation(
            model_code="STRATEGY.Threshold",
            policy_code="MAINT.OverdueService",
            triggered_rules=("service_interval_exceeded",),
            summary="Schedule overdue haul-truck service",
            severity="critical",
            evidence=("MAINT.MTBF",),
        ),
        Recommendation(
            model_code="STRATEGY.Threshold",
            policy_code="PROD.QueueBuildUp",
            triggered_rules=("queue_time_high",),
            summary="Rebalance truck assignments at the north crusher",
            severity="medium",
            evidence=("HAUL.QueueTime",),
        ),
    )
    for recommendation in recommendations:
        print(f"[{recommendation.severity:>8}] {recommendation.policy_code}")

    print()
    print("--- 2. Ranking: which recommendation is best (spec 07 sec. 16) ---")
    ranked = WeightedScoreRanking().rank(recommendations)
    for item in ranked:
        print(f"rank {item.rank}: {item.recommendation.policy_code} (score {item.score.value:.3f})")

    print()
    print("--- 3. Prioritization: urgency/impact/effort under capacity (spec 07 sec. 20) ---")
    prioritizer = ActionPrioritizer(
        effort_estimates={
            "MAINT.OverdueService": 4.0,  # a service bay and a crew, hours of work
            "PROD.QueueBuildUp": 0.5,  # a dispatcher re-assignment
            "AVAIL.LowFleetAvailability": 2.0,
        }
    )
    prioritized = prioritizer.prioritize(ranked)
    for item, priority in prioritized:
        print(
            f"{item.recommendation.policy_code}: urgency={priority.urgency}"
            f" impact={priority.impact:.3f} effort={priority.effort}"
            f" -> priority_score={priority.priority_score:.3f}"
        )

    print()
    print("--- 4. Planning: dependency-respecting execution order (spec 07 sec. 21) ---")
    # The dispatcher rebalance only makes sense after the overdue truck
    # is back from service; the availability investigation depends on both.
    dependencies = {
        "PROD.QueueBuildUp": ("MAINT.OverdueService",),
        "AVAIL.LowFleetAvailability": ("MAINT.OverdueService", "PROD.QueueBuildUp"),
    }
    plan = ActionPlanner().plan(prioritized, dependencies=dependencies).unwrap()
    for index, action in enumerate(plan.ordered_actions, start=1):
        print(f"{index}. {action.policy_code}: {action.summary}")

    print()
    print("--- 5. A cyclic dependency fails loudly, never silently re-ordered ---")
    cyclic = ActionPlanner().plan(
        prioritized,
        dependencies={
            "MAINT.OverdueService": ("PROD.QueueBuildUp",),
            "PROD.QueueBuildUp": ("MAINT.OverdueService",),
        },
    )
    print(f"is_err: {cyclic.is_err} -> {cyclic.error}")


if __name__ == "__main__":
    main()
