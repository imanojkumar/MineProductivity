# Package Tutorial 10 — Simulation (Deep)

!!! abstract "Milestone 2 · Package Tutorials · Tutorial 10 of 13"
    Deep, full-surface tutorial for `mineproductivity.simulation` — hypothetical
    futures over a **governed scenario**, seeded from a real twin snapshot. Authored
    to **Package Tutorial Template v1.0** under the
    [Package Tutorial Implementation Standard](../../learning/PACKAGE_TUTORIAL_IMPLEMENTATION_STANDARD.md).

## Objective

Master the working surface of `mineproductivity.simulation`: the governed
`Scenario`, the `SimulationModel` contract and its four methodology bases, the
`SimulationExecutor`/`SimulationRun`, `ExperimentRunner` over seeded trials,
`ScenarioComparator`/`SensitivityAnalyzer`, `seed_from_replay`, and — the payoff —
**a plugin `MonteCarloModel`** (simulation ships zero).

All 34 public symbols (`mineproductivity.simulation.__all__`) are accounted for
under the **coverage convention** (§5): **21 [deep]** / **13 [ref]**. Public APIs
only.

## Prerequisites

- Package Tutorials [3 — Events](03_events.md), [7 — Analytics](07_analytics.md),
  [9 — Digital Twin](09_digital_twin.md): simulation seeds from a twin snapshot,
  delegates statistics to analytics, and replays from the event log (§3).

**No Fundamentals lesson** — first exposure; §1 and §3 carry their own why.

## Running the examples

Every code block below is executed and its output pasted verbatim. Four scripts:

```bash
pip install -e ".[analytics]"
python examples/simulation/01_monte_carlo_experiment.py   # ...and 02, 03, 04
```

---

## 1. Why this package exists

Decision and analytics tell you what *has* happened; something has to answer
"**what if?**" — what if we add three trucks to the night shift, what feed rate
would the crusher see. `simulation` answers it with discipline: a **governed
`Scenario`** (named, versioned, with explicit parameters and horizon) executed as
many seeded, independent trials, **seeded from a real twin snapshot** rather than a
hand-typed guess.

Two refusals keep it honest. It **owns no statistics** — summarising 500 trials is
`analytics`' job, so there is one definition of "mean" and "p90" in the platform.
And it **ships no models** — Monte Carlo, discrete-event, system-dynamics, and
calibration are interface-only contracts, because *how* your mine behaves is your
modelling decision, not the framework's.

## 2. Architectural role

`simulation` sits above `digital_twin`, below `optimization`:

```
… decision ─► digital_twin ─► simulation ─► optimization ─► …
```

It takes the *real present* (a `TwinSnapshot`) and projects *possible futures*;
`optimization` then searches those futures for the best plan. It re-derives no
statistics (analytics) and invents no starting state (digital_twin).

## 3. Integration with adjacent layers

**`digital_twin` (Tutorial 9) — the starting condition:** an experiment begins from
a `TwinSnapshot` (a real, evidence-backed state), and `seed_from_replay` reconstructs
that seed from the event log. No hand-authored initial state.

**`analytics` (Tutorial 7) — the statistics:** trial results are summarised through
analytics (`describe`/percentile/`confidence_interval`); simulation deliberately
owns no statistical code, so "p90" means the same here as everywhere.

**`events` (Tutorial 3):** `seed_from_replay` folds the log to a starting state,
reusing the replay machinery.

**`registry` (Tutorial 4):** `REGISTRY` is a `registry.Registry`; `@register`,
`by_category`, `by_scope` discover models.

**`core` (Tutorial 1):** `Scenario`, `SimulationResult`, `SimulationRun` are
governed value objects; execution returns governed results.

**Upward to `optimization` (Tutorial 11):** an `ExperimentRunner` is exactly what an
optimization search evaluates candidate scenarios against.

## 4. Package structure

| Group | Module(s) | Public symbols |
|---|---|---|
| The model contract | `abstractions` | `SimulationModel`, `SimulationContext` |
| Methodology bases | `montecarlo`, `discrete_event`, `system_dynamics`, `calibration` | `MonteCarloModel`, `DiscreteEventModel`, `SystemDynamicsModel`, `CalibrationModel` |
| Scenario & run | `scenario`, `run`, `state`, `caching` | `Scenario`, `ScenarioStatus`, `SimulationRun`, `RunStatus`, `SimulationState`, `SimulationStateCache` |
| Execution & clock | `executor`, `clock` | `SimulationExecutor`, `SimulationClock`, `TimeProgressionMode` |
| Experiments & analysis | `experiment`, `comparison`, `sensitivity` | `Experiment`, `ExperimentRunner`, `ExperimentResult`, `ScenarioComparator`, `SensitivityAnalyzer` |
| Seed & results | `replay`, `result` | `seed_from_replay`, `SimulationResult` |
| Metadata, registry, persistence | `metadata`, `_registry`, `discovery`, `persistence` | `SimulationCategory`, `SimulationMetadata`, `REGISTRY`, `register`, `by_category`, `by_scope`, `SimulationRunRepository` |
| Exceptions | `exceptions` | `ScenarioConflictError`, `SimulationExecutionError`, `SimulationRunNotFoundError`, `SimulationValidationError`, `SimulationVersionConflictError` |

## 5. Public APIs

All 34 exports under the **coverage convention**:

**The spine — [deep]**
: `SimulationModel`, `SimulationContext`, `MonteCarloModel`, `Scenario`,
  `ScenarioStatus`, `SimulationExecutor`, `SimulationRun`, `RunStatus`,
  `SimulationResult`, `Experiment`, `ExperimentRunner`, `ExperimentResult`,
  `ScenarioComparator`, `SensitivityAnalyzer`, `seed_from_replay`,
  `SimulationMetadata`, `SimulationCategory`, `REGISTRY`, `register`, `by_category`,
  `by_scope`

**Everything else — [ref]** — see the table.

### Reference coverage

| Group | Symbols (`[ref]`) | What / when |
|---|---|---|
| Other methodology bases | `DiscreteEventModel`, `SystemDynamicsModel`, `CalibrationModel` | The other three interface-only methodology contracts (each ships zero implementations) — you extend one exactly as §13 extends `MonteCarloModel`. |
| Clock & state | `SimulationClock`, `TimeProgressionMode`, `SimulationState`, `SimulationStateCache` | Time progression for a run; per-run state and its cache. |
| Persistence | `SimulationRunRepository` | Stores completed `SimulationRun`s for retrieval. |
| Exceptions | `ScenarioConflictError`, `SimulationExecutionError`, `SimulationRunNotFoundError`, `SimulationValidationError`, `SimulationVersionConflictError` | Conflicting scenario, execution failure, unknown run, invalid metadata, duplicate code. All derive from `core.MineProductivityError`. |

## 6. Conceptual model

Five ideas explain the package.

**A. A scenario is governed.** A `Scenario` is named, versioned (`v1.0.0`), and
carries explicit `parameters` and a horizon — so "the night-shift surge scenario" is
a reproducible object, not a script someone edited.

**B. A model is metadata + one method.** `SimulationModel` declares
`meta: SimulationMetadata` and a category-specific compute; the four bases
(`MonteCarloModel`, …) are interface-only.

**C. Experiments are many seeded trials.** `ExperimentRunner` dispatches N
independent, **seeded** runs (reproducible), each a `SimulationRun` with a
`RunStatus` and `SimulationResult`.

**D. Statistics live in analytics.** Simulation produces raw trial outputs; you
summarise them through `analytics` — one definition of mean/p90 platform-wide.

**E. Start from reality.** An experiment seeds from a `TwinSnapshot` (via
`seed_from_replay`), and comparison/sensitivity vary *copies* — the base scenario is
never mutated.

## 7. Real mining examples

The walkthroughs project a north fleet's throughput: a 500-trial Monte Carlo of a
night-shift surge, a baseline-vs-surge comparison, a truck-count sensitivity sweep,
and a site-pack drill-penetration model plugin (§13).

## 8. Step-by-step walkthroughs

### 8.1 A seeded Monte Carlo experiment

Start from a **real twin snapshot**; a governed `Scenario` names the model,
parameters, and horizon; `ExperimentRunner` dispatches 500 independent seeded
trials; and the summary goes **through analytics** — simulation owns no statistics.
Running
[`01_monte_carlo_experiment.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/simulation/01_monte_carlo_experiment.py):

```text
--- 1. Start from a real twin snapshot, not a hand-authored guess ---
snapshot of FLEET-NORTH: {'tonnes_per_hour': 4200.0}

--- 2. A governed Scenario names the model, parameters, and horizon ---
scenario='FLEET.NightShiftSurge' v1.0.0 parameters={'trucks_added': 3}

--- 3. 500 independent, concurrently-dispatched, seeded trials ---
experiment 'FLEET.NightShiftSurge@1.0.0': 500 runs completed

--- 4. Summarize through analytics -- simulation owns no statistics ---
n=500 mean=4724.7 t/h
p50=4723.6 p90=5124.6
range=[4267.4, 5209.9]
```

The trials are *seeded*, so the run is reproducible; the summary is `analytics`'
`describe`, so the numbers mean exactly what they mean everywhere else.

### 8.2 Scenario comparison

Two governed scenarios differing in one assumption (24 vs 27 trucks), 200 trials
each, one analytics-backed summary per scenario — and the **judgment stays with the
caller** (adding trucks is a decision-layer question, not simulation's). Running
[`02_scenario_comparison.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/simulation/02_scenario_comparison.py):

```text
--- 3. One analytics-backed summary per scenario ---
baseline: mean= 4089.6 t/h  p90= 4455.4  n=200
   surge: mean= 4600.9 t/h  p90= 5012.3  n=200

--- 4. The judgment stays with the caller (a decision-layer question) ---
observed mean uplift from 3 extra trucks: +511.2 t/h
```

### 8.3 Sensitivity sweep

`SensitivityAnalyzer` runs one experiment per swept parameter value, ordered to
match; distributional treatment is again analytics' job; and the **base scenario is
untouched** — variants were transient copies. Running
[`03_sensitivity_sweep.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/simulation/03_sensitivity_sweep.py):

```text
--- 2. One run per swept value, ordered to match ---
trucks=20 -> feed= 3531.9 t/h
trucks=24 -> feed= 4238.3 t/h
trucks=28 -> feed= 4944.6 t/h
trucks=32 -> feed= 5045.5 t/h
trucks=36 -> feed= 5045.5 t/h
(the crusher cap flattens the curve past ~28 trucks)

--- 4. The base scenario is untouched -- variants were transient copies ---
base parameters still: {'trucks': 20}
```

The flattening past ~28 trucks is the whole point of a sweep — it shows the
crusher cap that a single run would hide.

## 9. Repository example reuse

The four `simulation` scripts were each executed (exit `0`), output above.

| Script | Public API it exercises | Walkthrough |
|---|---|---|
| [`01_monte_carlo_experiment.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/simulation/01_monte_carlo_experiment.py) | `Scenario`, `Experiment`, `ExperimentRunner`, `ExperimentResult`, `SimulationRun`, `seed_from_replay` | §8.1 |
| [`02_scenario_comparison.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/simulation/02_scenario_comparison.py) | `ScenarioComparator`, `Scenario`, `ScenarioStatus`, `SimulationResult` | §8.2 |
| [`03_sensitivity_sweep.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/simulation/03_sensitivity_sweep.py) | `SensitivityAnalyzer`, `SimulationExecutor`, `RunStatus` | §8.3 |
| [`04_plugin_simulation_model.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/simulation/04_plugin_simulation_model.py) | `MonteCarloModel`, `SimulationModel`, `SimulationCategory`, `SimulationMetadata`, `register`, `by_category` | §13 |

## 10. Common mistakes

| Mistake | What happens | Do this instead |
|---|---|---|
| Computing statistics inside a model | Two definitions of "mean/p90" | Summarise trial output through `analytics` |
| Hand-authoring the initial state | The result is a guess, not evidence | Seed from a `TwinSnapshot` / `seed_from_replay` |
| Unseeded / stateful RNG across trials | Non-reproducible experiments | Seed every trial; keep models stateless |
| Mutating the base scenario in a sweep | Later runs start from the wrong state | Vary transient copies; leave the base intact |
| Expecting a built-in simulation model | Ships zero (interface-only) | Register a `MonteCarloModel`/etc plugin |
| Making the decision inside simulation | Conflates "what if" with "what to do" | Return results; the caller (decision) judges |

## 11. Best practices

- **Always seed from a twin snapshot** — a real starting condition, not a guess.
- **Summarise through analytics** — never re-implement statistics.
- **Seed every trial** for reproducibility; keep models stateless.
- **Version your scenarios**; vary copies, never the base.
- **Let the caller judge** — simulation informs a decision, it does not make one.

## 12. Performance considerations

- **Trials are independent and concurrently dispatched** — an experiment scales
  across cores; the `SimulationStateCache` avoids recomputing shared setup.
- **`seed_from_replay` caps cold-seed cost** by folding from a snapshot rather than genesis.
- **A sweep is N experiments** — order them and reuse the base seed for comparability.
- **Models are stateless** across runs — safe to share and parallelise.

## 13. Extension points — a plugin `SimulationModel`

`simulation` ships **zero** models (interface-only) — the methodology is your
choice. The extension point is to subclass a methodology base (`MonteCarloModel`,
`DiscreteEventModel`, `SystemDynamicsModel`, or `CalibrationModel`), declare
`SimulationMetadata`, implement its compute, and register — usually as a plugin. The
reused
[`04_plugin_simulation_model.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/simulation/04_plugin_simulation_model.py)
discovers a site-pack drill-penetration model through the real entry-point path:

```text
--- 1. simulation ships zero built-in models (interface-only) ---
site-pack models before discovery: []

--- 2. A site pack declares its model via a pyproject.toml entry-point ---
discover() -> is_ok: True, loaded entry-points: ('sitepack',)
registered: MONTECARLO.SitePackDrillPenetration (monte_carlo)

--- 3. The discovered model executes like any built-in would ---
penetration: 28.94 m/h
run status: True
```

Each methodology base is the same "declare metadata, implement the method, register"
idiom; `by_category` then finds every model of a kind. Ship a model pack as a plugin
(Tutorial 4) and it appears in `REGISTRY` on install.

!!! note "Simulation informs; it does not decide, or count"
    Two contracts are pushed outward on purpose: statistics belong to `analytics`
    (one definition platform-wide), and the *act* on a result belongs to the
    `decision` layer. Simulation's job is only to project a governed scenario into
    seeded futures.

## 14. Exercises

1. **Seed from reality.** Take a `TwinSnapshot` and start an experiment from it. Why is
   this preferable to a hand-typed initial `tonnes_per_hour`?
2. **Compare two scenarios.** Build a baseline and a variant differing in one parameter;
   run 200 trials each and report the mean uplift. Why does the *judgment* stay with you?
3. **Sweep to a cap.** Sweep a parameter until the output flattens; what real constraint
   does the plateau reveal that a single run would hide?
4. **Prove reproducibility.** Run the same seeded experiment twice; are the summaries
   identical? What makes that guaranteed?
5. **Implement a model.** Sketch a `MonteCarloModel` for a metric you know; which base
   method do you implement, and why does simulation not ship one for you?

## 15. Reference solutions

??? success "Solution 1 — Seed from reality"
    A `TwinSnapshot` is an evidence-backed condition folded from the event log, so the
    experiment starts from *what was actually true*, not a number someone guessed —
    which is the difference between a defensible study and a plausible-looking one.

??? success "Solution 2 — Compare two scenarios"
    `ScenarioComparator` runs both and summarises each through analytics; the uplift is
    an *observation*. Whether +500 t/h justifies three more trucks weighs cost, capacity,
    and risk — a `decision`-layer call, which is why simulation returns evidence, not a verdict.

??? success "Solution 3 — Sweep to a cap"
    The plateau reveals a binding constraint downstream (here a crusher feed cap): past
    ~28 trucks, more trucks add queue, not throughput. A single run at 24 trucks would
    show none of that.

??? success "Solution 4 — Prove reproducibility"
    Identical, because every trial is seeded — the RNG stream is a function of the seed,
    so the same seed yields the same trials and the same analytics summary.

??? success "Solution 5 — Implement a model"
    You implement the methodology base's compute (e.g. a Monte-Carlo trial function);
    simulation ships none because the right model depends on your mine's physics and data
    — a stable contract lets your plugin slot in without a framework change.

## 16. Further reading

- **[`simulation` package guide](../../packages/simulation.md)** — the capability-tour view.
- **[`simulation` API reference](../../api-reference/simulation.md)** — every symbol, from source.
- **[Simulation Design Specification](../../architecture/09_Simulation_Design_Specification.md)** · **[ADR-0009](../../adr/ADR-0009-Simulation.md)** — governed scenarios, the interface-only methodology bases, statistics delegated to analytics.
- **Package Tutorials [9 — Digital Twin](09_digital_twin.md) · [7 — Analytics](07_analytics.md).**

---

**Next package tutorial:** Optimization (deep) — searching seeded futures for the
best feasible plan.
*(Not yet written — Tutorial 11 of 13.)*
