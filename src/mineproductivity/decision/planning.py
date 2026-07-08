"""``ActionPlanner``: sequences a set of prioritized actions, respecting
declared dependencies, into an ``ActionPlan`` (design spec §21).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``kpis.DependencyGraph`` is deliberately **not** reused for the
topological ordering this module needs -- the design spec is explicit
about this (§21, §33's own anti-pattern entry: "Forcing ``ActionPlanner``
to reuse ``kpis.DependencyGraph`` by encoding actions as fake KPI codes
merely to reuse its topological-sort code"). ``DependencyGraph`` is
tightly coupled to ``Registry[str, type[BaseKPI]]``/
``KPIMetadata.dependencies``, a shape that does not fit arbitrary
action-to-action dependencies. A repository-wide search of ``core`` and
``registry`` (the only two packages a genuinely general DAG-ordering
utility could legitimately live in, per §21's own closing note: "a
genuinely more general DAG-ordering utility, if ever needed
platform-wide, belongs in ``core``, not duplicated here") confirms
neither module defines one today -- this module's own narrow,
self-contained ordering implementation is therefore genuinely required,
not a case of skipped reuse.

The "action's identifying key" ``dependencies`` maps from/to is
``Recommendation.policy_code`` -- reusing exactly the same keying
convention ``prioritization.ActionPrioritizer`` already established for
its own ``effort_estimates`` mapping, rather than inventing a second
per-action identifier scheme.

``core.Result`` is reused verbatim for this module's own fallible
return type, exactly as every other fallible operation in this
platform (``Registry.register``, ``DependencyGraph.topological_order``
by way of ``KPICircularDependencyError``) is expressed.
"""

from __future__ import annotations

import heapq
import itertools
from collections.abc import Mapping, Sequence
from types import MappingProxyType

from mineproductivity.core import Result

from mineproductivity.decision.exceptions import DecisionValidationError
from mineproductivity.decision.result import ActionPlan, ActionPriority, RankedRecommendation

__all__ = ["ActionPlanner"]


class ActionPlanner:
    """Sequences a set of prioritized actions, respecting declared
    dependencies, into an ``ActionPlan``. Implements its own narrow
    topological ordering rather than reusing ``kpis.DependencyGraph``,
    which is tightly coupled to ``Registry[str, type[BaseKPI]]`` and
    ``KPIMetadata.dependencies`` -- a shape that does not fit arbitrary
    action-to-action dependencies (§3.3, §21).

    ``dependencies`` is an optional, caller-supplied mapping from an
    action's identifying key (``Recommendation.policy_code``) to the
    keys it depends on -- when empty (the default), :meth:`plan`
    degrades to simply ordering actions by ``ActionPriority.priority_score``,
    so a caller with no dependency information to supply pays no
    complexity cost. A dependency entry naming a key absent from
    ``prioritized`` is silently ignored (the referenced action is not a
    candidate this call is planning over). :meth:`plan` returns
    ``Result.err`` on a detected cycle rather than silently dropping or
    arbitrarily breaking it -- the same "fail loudly on a cycle" posture
    ``kpis.DependencyGraph.detect_cycle`` already established for KPI
    dependencies, applied here to this package's own, structurally
    different dependency shape. For the identical reason, ``plan`` also
    returns ``Result.err`` when two entries in ``prioritized`` share a
    ``policy_code`` -- since the identifying key is the only handle
    ``dependencies`` (and this method's own de-duplication) has for an
    action, silently keeping only one would silently drop the other from
    the plan (a defect caught during this phase's own QA review, before
    it could ship).

    Ordering uses a priority queue (``heapq``) over the ready frontier
    rather than a plain FIFO/DFS traversal, so the emitted order always
    respects ``priority_score`` (descending) among actions that are
    simultaneously eligible -- ``O((V+E) log V)``, a small, disclosed
    deviation from the plain ``O(V+E)`` bound a tie-break-free
    topological sort achieves, required because respecting priority
    order among ready actions is this method's own stated purpose, not
    an afterthought. Ties break by input order (a stable-sort-shaped
    guarantee, mirroring ``ranking.WeightedScoreRanking``'s own stable
    tie-break discipline).

    Examples
    --------
    >>> from mineproductivity.decision.result import DecisionScore, Recommendation
    >>> rec_a = Recommendation(
    ...     policy_code="A", triggered_rules=(), summary="Do A", severity="high", evidence=(),
    ... )
    >>> rec_b = Recommendation(
    ...     policy_code="B", triggered_rules=(), summary="Do B", severity="medium", evidence=(),
    ... )
    >>> ranked_a = RankedRecommendation(
    ...     recommendation=rec_a, score=DecisionScore(value=0.9, components={}), rank=1,
    ... )
    >>> ranked_b = RankedRecommendation(
    ...     recommendation=rec_b, score=DecisionScore(value=0.5, components={}), rank=2,
    ... )
    >>> priority_a = ActionPriority(urgency=0.75, impact=0.9, effort=1.0)
    >>> priority_b = ActionPriority(urgency=0.5, impact=0.5, effort=1.0)
    >>> plan = ActionPlanner().plan(
    ...     [(ranked_a, priority_a), (ranked_b, priority_b)], dependencies={"A": ("B",)},
    ... )
    >>> [action.policy_code for action in plan.unwrap().ordered_actions]
    ['B', 'A']
    """

    def plan(
        self,
        prioritized: Sequence[tuple[RankedRecommendation, ActionPriority]],
        *,
        dependencies: Mapping[str, tuple[str, ...]] = MappingProxyType({}),
    ) -> Result[ActionPlan]:
        policy_codes = [item[0].recommendation.policy_code for item in prioritized]
        if len(policy_codes) != len(set(policy_codes)):
            duplicates = sorted({code for code in policy_codes if policy_codes.count(code) > 1})
            return Result.err(
                DecisionValidationError(
                    "ActionPlanner.plan requires each action's policy_code to be unique "
                    f"among prioritized (duplicates: {duplicates})"
                )
            )
        keyed = {item[0].recommendation.policy_code: item for item in prioritized}
        in_degree = dict.fromkeys(keyed, 0)
        dependents: dict[str, list[str]] = {key: [] for key in keyed}
        for key, deps in dependencies.items():
            if key not in keyed:
                continue
            for dep in deps:
                if dep not in keyed:
                    continue
                dependents[dep].append(key)
                in_degree[key] += 1

        counter = itertools.count()
        ready: list[tuple[float, int, str]] = []
        for key in keyed:
            if in_degree[key] == 0:
                heapq.heappush(ready, (-keyed[key][1].priority_score, next(counter), key))

        ordered_keys: list[str] = []
        while ready:
            _, _, key = heapq.heappop(ready)
            ordered_keys.append(key)
            for dependent in dependents[key]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    heapq.heappush(
                        ready, (-keyed[dependent][1].priority_score, next(counter), dependent)
                    )

        if len(ordered_keys) != len(keyed):
            return Result.err(
                DecisionValidationError("ActionPlanner.plan detected a cyclic action dependency")
            )

        ordered_actions = tuple(keyed[key][0].recommendation for key in ordered_keys)
        priorities = {key: keyed[key][1] for key in ordered_keys}
        return Result.ok(ActionPlan(ordered_actions=ordered_actions, priorities=priorities))

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"
