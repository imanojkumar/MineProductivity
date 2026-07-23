# Package Tutorial 11 — Optimization (Deep)

!!! abstract "Milestone 2 · Package Tutorials · Tutorial 11 of 13"
    Deep, full-surface tutorial for `mineproductivity.optimization` — searching a
    governed problem for the **best feasible plan**, seeded from reality and solved
    by a plugin. Authored to **Package Tutorial Template v1.0** under the
    [Package Tutorial Implementation Standard](../../learning/PACKAGE_TUTORIAL_IMPLEMENTATION_STANDARD.md).

## Objective

Master the working surface of `mineproductivity.optimization`: the governed
`OptimizationProblem` (`DecisionVariable`s, `Constraint`s, `Objective`), the
`OptimizationModel` contract and its six paradigm bases, the executor and run,
`PlanComparator`/`SensitivityAnalyzer`, candidate search over simulation, and — the
payoff — **a plugin solver adapter** (optimization ships zero solvers).

All 36 public symbols (`mineproductivity.optimization.__all__`) are accounted for
under the **coverage convention** (§5): **23 [deep]** / **13 [ref]**. Public APIs
only.

## Prerequisites

- Package Tutorials [7 — Analytics](07_analytics.md), [9 — Digital Twin](09_digital_twin.md),
  [10 — Simulation](10_simulation.md): optimization seeds from a twin snapshot,
  delegates statistics to analytics, and searches over simulation experiments (§3).

**No Fundamentals lesson** — first exposure; §1 and §3 carry their own why.

## Running the examples

Every code block below is executed and its output pasted verbatim. Five scripts:

```bash
pip install -e ".[analytics]"
python examples/optimization/01_mip_fleet_allocation.py   # ...and 02–05
```

---

## 1. Why this package exists

Simulation says what *could* happen; optimization says what you *should do* — the
**best feasible plan** given an objective and hard constraints. How many trucks on
day vs night shift to maximise tonnes without exceeding the crusher cap? That is a
governed `OptimizationProblem`: decision variables, constraints, an objective —
solved, feasibility reported, plan returned.

Two refusals, identical to simulation's: it **ships no solver** (LP, MIP, CP,
multi-objective, evolutionary, network are interface-only paradigm contracts — the
platform imports no solver library), and it **owns no statistics** (comparison and
sensitivity delegate to `analytics`). And it **does not choose** — it quantifies
trade-offs; weighing throughput against capital cost is a `decision`-layer call.

## 2. Architectural role

`optimization` sits at the top of the projection chain:

```
… digital_twin ─► simulation ─► optimization ─► agents ─► visualization
```

It seeds from the *real present* (a twin snapshot), evaluates candidate plans —
often by **searching over simulation experiments** — and returns the best feasible
one for an agent workflow or a human to act on.

## 3. Integration with adjacent layers

**`simulation` (Tutorial 10) — candidate evaluation:** a candidate-scenario search
scores each option through a simulation `ExperimentRunner` and reads the outcomes;
optimization builds no `SimulationRun` itself.

**`digital_twin` (Tutorial 9) — the starting condition:** a problem's budget/state
comes from a `TwinSnapshot`, not a hand-authored guess.

**`analytics` (Tutorial 7) — the statistics:** `PlanComparator` and
`SensitivityAnalyzer` summarise through analytics — one definition of mean/CI
platform-wide.

**`registry` (Tutorial 4):** `REGISTRY` is a `registry.Registry`; `@register`,
`by_category`, `by_scope` discover solver adapters.

**`core` (Tutorial 1):** `OptimizationProblem`, `OptimizationResult`,
`DecisionVariable`, `Constraint`, `Objective` are governed value objects.

**Upward to `agents` (Tutorial 12):** optimization is a *tool* an agent workflow
composes — "find the best plan" is a step in an autonomous task.

## 4. Package structure

| Group | Module(s) | Public symbols |
|---|---|---|
| The model contract | `abstractions` | `OptimizationModel`, `OptimizationContext` |
| Paradigm bases | `linear_programming`, `mixed_integer_programming`, `constraint_programming`, `multi_objective`, `evolutionary`, `network_optimization` | `LinearProgrammingModel`, `MixedIntegerProgrammingModel`, `ConstraintProgrammingModel`, `MultiObjectiveModel`, `EvolutionaryMetaheuristicModel`, `NetworkOptimizationModel` |
| Problem definition | `problem` | `OptimizationProblem`, `ProblemStatus`, `DecisionVariable`, `VariableDomain`, `Constraint`, `ConstraintOperator`, `Objective`, `ObjectiveDirection` |
| Execution & run | `executor`, `run`, `state` | `OptimizationExecutor`, `OptimizationRun`, `RunStatus`, `OptimizationState` |
| Analysis & results | `comparison`, `sensitivity`, `result` | `PlanComparator`, `SensitivityAnalyzer`, `OptimizationResult`, `ParetoResult` |
| Metadata, registry, persistence | `metadata`, `_registry`, `discovery`, `persistence` | `OptimizationCategory`, `OptimizationMetadata`, `REGISTRY`, `register`, `by_category`, `by_scope`, `OptimizationRunRepository` |
| Exceptions | `exceptions` | `OptimizationExecutionError`, `OptimizationRunNotFoundError`, `OptimizationValidationError`, `OptimizationVersionConflictError`, `ProblemConflictError` |

## 5. Public APIs

All 36 exports under the **coverage convention**:

**The spine — [deep]**
: `OptimizationModel`, `OptimizationContext`, `MixedIntegerProgrammingModel`,
  `OptimizationProblem`, `ProblemStatus`, `DecisionVariable`, `VariableDomain`,
  `Constraint`, `ConstraintOperator`, `Objective`, `ObjectiveDirection`,
  `OptimizationExecutor`, `OptimizationRun`, `RunStatus`, `OptimizationResult`,
  `PlanComparator`, `SensitivityAnalyzer`, `OptimizationMetadata`,
  `OptimizationCategory`, `REGISTRY`, `register`, `by_category`, `by_scope`

**Everything else — [ref]** — see the table.

### Reference coverage

| Group | Symbols (`[ref]`) | What / when |
|---|---|---|
| Other paradigm bases | `LinearProgrammingModel`, `ConstraintProgrammingModel`, `MultiObjectiveModel`, `EvolutionaryMetaheuristicModel`, `NetworkOptimizationModel` | The other five interface-only paradigm contracts — you implement a solver adapter for one exactly as §13 does for MIP. `MultiObjectiveModel` produces a `ParetoResult`. |
| Results & state | `ParetoResult`, `OptimizationState` | The Pareto frontier of a multi-objective solve; per-run state. |
| Persistence | `OptimizationRunRepository` | Stores completed `OptimizationRun`s. |
| Exceptions | `OptimizationExecutionError`, `OptimizationRunNotFoundError`, `OptimizationValidationError`, `OptimizationVersionConflictError`, `ProblemConflictError` | Solve failure, unknown run, invalid metadata, duplicate code, conflicting problem. All derive from `core.MineProductivityError`. |

## 6. Conceptual model

Five ideas explain the package.

**A. A problem is governed and declarative.** An `OptimizationProblem` states its
`DecisionVariable`s (each over a `VariableDomain`), its `Constraint`s (a
`ConstraintOperator` over a bound), and its `Objective` (an `ObjectiveDirection`) —
data, not solver code.

**B. A model is a solver adapter.** `OptimizationModel` + the six paradigm bases are
interface-only; a concrete adapter wires a real solver (or a simple exact method) to
the contract and registers.

**C. Feasibility is first-class.** An `OptimizationResult` reports whether a feasible
solution exists and, if so, the objective value and the variable assignments — an
infeasible problem is a *result*, not a crash.

**D. Statistics and choice live elsewhere.** `PlanComparator`/`SensitivityAnalyzer`
summarise through `analytics`; which plan to adopt is the `decision` layer's call.

**E. Search over simulation.** A candidate-scenario search scores options by running
them through simulation and comparing outcomes — optimization reads results, it does
not re-run the world.

## 7. Real mining examples

The walkthroughs solve a north-fleet shift allocation (MIP), compare two plans across
ore grades, sweep a fleet-budget constraint to the crusher cap, and search candidate
fleet sizes through simulation — plus a site-pack solver plugin (§13).

## 8. Step-by-step walkthroughs

### 8.1 A MIP fleet-allocation solve

Seed the budget from a **real twin snapshot**; state a governed problem (objective,
caps, decision variables); dispatch through the `OptimizationExecutor`; read the
feasible plan and objective. Running
[`01_mip_fleet_allocation.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/optimization/01_mip_fleet_allocation.py):

```text
--- 1. Start from a real twin snapshot, not a hand-authored guess ---
snapshot of FLEET-NORTH: {'available_trucks': 30}

--- 2. A governed problem: objective, caps, decision variables ---
problem='FLEET.NightShiftAllocation' model='MIP.FleetShiftAllocation' budget from snapshot

--- 4. The solved plan ---
feasible=True  objective=14880 t/shift
  day_trucks: 18 trucks
  night_trucks: 12 trucks
run status COMPLETED: True
(optimum: 18 day trucks @520 + 12 night @460 = 14,880 t/shift)
```

`feasible=True` with the assignment and the objective — a plan a superintendent can
act on, traceable to a governed problem seeded from real fleet state.

### 8.2 Plan comparison and sensitivity

`PlanComparator` solves two plans across five ore grades and summarises **through
analytics**; `SensitivityAnalyzer` re-solves per swept constraint value, leaving the
base problem untouched. Running
[`02_plan_comparison.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/optimization/02_plan_comparison.py)
and
[`03_sensitivity_sweep.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/optimization/03_sensitivity_sweep.py):

```text
--- 2. PlanComparator delegates every statistic to analytics ---
conservative_24: n=5 mean= 4320.0 t/h p50= 4320.0 range=[ 3888.0,  4752.0]
  aggressive_30: n=5 mean= 5400.0 t/h p50= 5400.0 range=[ 4860.0,  5940.0]

--- (sensitivity) One re-solve per value, ordered to match ---
budget=   18 -> throughput= 3150.0 t/h
budget=   26 -> throughput= 4550.0 t/h
budget=   30 -> throughput= 5000.0 t/h
budget=   34 -> throughput= 5000.0 t/h
(the crusher cap flattens the curve past ~28 trucks)

--- The base problem is untouched -- variants were transient copies ---
base 'fleet_budget' bound still: 20.0
```

The plateau past ~28 trucks is a *binding downstream constraint* the objective alone
would not reveal — the reason a sweep exists.

### 8.3 Candidate search over simulation

An optimization search scores each candidate fleet size **through a simulation
`ExperimentRunner`** and compares the score distributions via analytics — reading
outcomes, never building a `SimulationRun` itself. Running
[`04_candidate_scenario_search.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/optimization/04_candidate_scenario_search.py):

```text
--- 2. Compare the candidates' score distributions via analytics ---
 trucks_24: n=8 mean= 4336.1 p50= 4297.0 range=[ 4004.1,  4714.0]
 trucks_27: n=8 mean= 4878.1 p50= 4834.1 range=[ 4504.6,  5303.3]
 trucks_30: n=8 mean= 5420.1 p50= 5371.2 range=[ 5005.1,  5892.5]

--- 3. optimization never built a SimulationRun; it read the outcomes ---
(the winning candidate is the caller's call, informed by these summaries)
```

This is the whole Digital Intelligence chain composing: a twin seeds a simulation,
optimization searches the simulated futures, analytics summarises them, and the
decision stays with the caller.

## 9. Repository example reuse

The five `optimization` scripts were each executed (exit `0`), output above.

| Script | Public API it exercises | Walkthrough |
|---|---|---|
| [`01_mip_fleet_allocation.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/optimization/01_mip_fleet_allocation.py) | `OptimizationProblem`, `DecisionVariable`, `Constraint`, `Objective`, `OptimizationExecutor`, `OptimizationRun`, `OptimizationResult`, `RunStatus` | §8.1 |
| [`02_plan_comparison.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/optimization/02_plan_comparison.py) | `PlanComparator`, `ProblemStatus` | §8.2 |
| [`03_sensitivity_sweep.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/optimization/03_sensitivity_sweep.py) | `SensitivityAnalyzer`, `ConstraintOperator`, `VariableDomain`, `ObjectiveDirection` | §8.2 |
| [`04_candidate_scenario_search.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/optimization/04_candidate_scenario_search.py) | search over `simulation.ExperimentRunner`; `OptimizationCategory` | §8.3 |
| [`05_plugin_solver_adapter.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/optimization/05_plugin_solver_adapter.py) | `MixedIntegerProgrammingModel`, `OptimizationModel`, `OptimizationMetadata`, `register`, `by_category` | §13 |

## 10. Common mistakes

| Mistake | What happens | Do this instead |
|---|---|---|
| Importing a solver library into the package | Violates interface-only; couples the platform to one solver | Wire the solver in a plugin adapter |
| Treating infeasible as an error to raise | A dashboard blanks over a normal outcome | Read `OptimizationResult.feasible` |
| Computing statistics inside optimization | Two definitions of mean/CI | Delegate to `analytics` |
| Hand-authoring the problem's state/budget | The plan is a guess | Seed from a `TwinSnapshot` |
| Mutating the base problem in a sweep | Later solves start wrong | Vary transient copies |
| Making the adopt/reject choice here | Conflates "best feasible" with "what to do" | Return the plan; `decision` weighs it |

## 11. Best practices

- **Declare the problem, not the solve** — variables, constraints, objective as data.
- **Ship the solver as a plugin adapter**; the platform imports no solver library.
- **Report feasibility**; an infeasible problem is a result, not a crash.
- **Seed from a twin snapshot**; delegate statistics to analytics; sweep on copies.
- **Search candidates through simulation**, reading outcomes rather than re-running the world.

## 12. Performance considerations

- **The paradigm chosen matters most** — LP/MIP/CP/evolutionary have different cost
  profiles; the adapter, not the framework, owns that trade-off.
- **A candidate search is N simulation experiments** — parallelise the candidates and
  reuse the seed for comparability.
- **`OptimizationRunRepository`** lets you retrieve a solved run instead of re-solving.
- **Models are stateless** across runs — safe to share.

## 13. Extension points — a solver adapter plugin

`optimization` ships **zero** solvers (interface-only) — the platform imports no
solver library. The extension point is to subclass a paradigm base
(`MixedIntegerProgrammingModel`, `LinearProgrammingModel`, `ConstraintProgrammingModel`,
`MultiObjectiveModel`, `EvolutionaryMetaheuristicModel`, or `NetworkOptimizationModel`),
declare `OptimizationMetadata`, wire your solver, and register — usually as a plugin.
The reused
[`05_plugin_solver_adapter.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/optimization/05_plugin_solver_adapter.py)
discovers a site-pack MIP adapter through the real entry-point path:

```text
--- 1. optimization ships zero built-in solvers (interface-only) ---
site-pack solvers before discovery: []

--- 2. A site pack declares its adapter via a pyproject.toml entry-point ---
discover() -> is_ok: True, loaded entry-points: ('sitepack',)
registered: MIP.SitePackBudgetSolver (mixed_integer_programming)

--- 3. The discovered adapter dispatches like any built-in would ---
objective=27  solution={'trucks': 27.0}
run status COMPLETED: True
```

`by_category(OptimizationCategory...)` then finds every adapter of a paradigm, so a
caller can pick a solver by kind. Ship a solver pack as a plugin (Tutorial 4) and it
appears in `REGISTRY` on install — no framework change, no bundled solver.

!!! note "The platform bundles no solver — on purpose"
    Which solver (open-source, commercial, custom) suits a site depends on scale,
    licensing, and problem shape. Interface-only keeps that choice — and its
    dependencies — in your plugin, not in the base install.

## 14. Exercises

1. **State a problem.** Define an `OptimizationProblem` with two `DecisionVariable`s, one
   `Constraint`, and a maximising `Objective`. What is data here, and what is solver logic?
2. **Read feasibility.** Tighten a constraint until the problem is infeasible; show that
   `OptimizationResult.feasible` is `False` rather than an exception being raised.
3. **Sweep to a cap.** Sweep a constraint bound until the objective flattens; what binding
   constraint does the plateau reveal?
4. **Search candidates.** Score three candidate plans through a simulation runner and
   summarise via analytics; why does optimization not build the `SimulationRun` itself?
5. **Write an adapter.** Sketch a `MixedIntegerProgrammingModel` adapter over a tiny exact
   solver; which method do you implement, and why does the package ship none?

## 15. Reference solutions

??? success "Solution 1 — State a problem"
    The variables, their domains, the constraint (operator + bound), and the objective
    direction are all *data* on the `OptimizationProblem`. The *solving* — how to search
    the feasible region — is the adapter's job, kept out of the problem entirely.

??? success "Solution 2 — Read feasibility"
    An over-tight constraint yields `OptimizationResult(feasible=False, ...)`; the run
    completes and reports it. Infeasibility is a normal answer a plan search must handle,
    not a crash to catch.

??? success "Solution 3 — Sweep to a cap"
    The plateau marks a *binding constraint* elsewhere (a crusher cap): beyond it, adding
    budget buys no objective. A single solve at one budget would show none of that shape.

??? success "Solution 4 — Search candidates"
    Because *evaluating* a candidate is simulation's job (seeded trials with uncertainty),
    optimization reads the simulated outcomes and compares them via analytics — one owner
    for the world model, one for statistics, one (the caller) for the choice.

??? success "Solution 5 — Write an adapter"
    You implement the paradigm base's solve method, wiring your solver to the
    `OptimizationProblem`/`OptimizationResult` contract. The package ships none because
    the right solver depends on your scale and licensing — interface-only keeps that (and
    its dependency) in your plugin.

## 16. Further reading

- **[`optimization` package guide](../../packages/optimization.md)** — the capability-tour view.
- **[`optimization` API reference](../../api-reference/optimization.md)** — every symbol, from source.
- **[Optimization Design Specification](../../architecture/10_Optimization_Design_Specification.md)** · **[ADR-0010](../../adr/ADR-0010-Optimization.md)** — governed problems, the six interface-only paradigm bases, statistics delegated to analytics.
- **Package Tutorials [10 — Simulation](10_simulation.md) · [9 — Digital Twin](09_digital_twin.md) · [7 — Analytics](07_analytics.md).**

---

**Next package tutorial:** AI Agents (deep) — model-independent orchestration of
autonomous work, composing the tools of Unit B.
*(Not yet written — Tutorial 12 of 13.)*
