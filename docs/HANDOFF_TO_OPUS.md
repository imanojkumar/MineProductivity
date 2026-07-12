# MineProductivity — Final Implementation Handoff

**Document:** `docs/HANDOFF_TO_OPUS.md`
**Prepared:** 2026-07-12, at the close of the "Final Architecture Implementation Sprint"
**Prepared by:** Claude Fable 5 (outgoing implementer)
**Addressed to:** Claude Opus 4.8 (incoming permanent owner), and any human engineer reviewing alongside
**Repository state at handoff:** working tree contains the **uncommitted** Phase 10–12 implementations; `__version__ == "1.8.0"`; full gate green (2,986 tests passed, `ruff check` + `ruff format --check` clean, `mypy --strict` clean across 314 source files)

> **Read this first.** Three complete packages (`optimization`, `agents`, `visualization`) exist only in the working tree. Nothing from the sprint has been committed, pushed, or tagged — by explicit instruction. Your first act should be reviewing and committing that work (see §16), not writing new code. The governing process rules live in the repo's own `CLAUDE.md` (four durable rules: architecture stability, single version source, Zenodo Concept DOI, End-of-Phase Standard) — re-read it every session; it overrides habit.

---

## 1. Overall Architecture Status

The platform's architecture is **complete and closed**. All twelve Design Specifications (01–12), their Implementation Checklists, and ADRs (0001–0012) are locked, and **all fourteen architecture packages are implemented**:

```
core → ontology → events → kpis → analytics → decision
     → digital_twin → simulation → optimization → agents → visualization
```

(plus the three cross-cutting infrastructure packages: `registry`, `plugins`, `connectors`).

`visualization` is, by declaration in spec 12 §34, the **final** package — no future package sits above it, and its Future Roadmap deliberately makes no promises on anyone's behalf. The architecture-first methodology (spec → checklist → ADR → implementation, per package, in dependency order) has run to completion. What remains is **release engineering, documentation synchronization, and quality-audit work** — not architecture and not (except where noted in §10–§12) implementation.

Do not redesign anything that is stable. `CLAUDE.md` Rule 1 makes this binding: architecture changes require an actual defect, an internal inconsistency, a dependency-rule violation, or a measurable maintainability issue — never "another design is possible."

## 2. Completed Phases

| Phase | Package | Released version | Status |
|---|---|---|---|
| Foundation | `core`, `ontology`, `events`, `registry`, `plugins`, `connectors`, `kpis` | ≤ 1.4.x | Released, locked |
| 06 | `analytics` | 1.5.0 | Released, locked |
| 07 | `decision` | 1.6.0 | Released, locked (completion pass closed its Examples/Benchmarks gap July 2026) |
| 08 | `digital_twin` | 1.7.0 | Released, locked |
| 09 | `simulation` | 1.8.0 | Released, locked (full package: examples, benchmarks, doc sync, release review) |
| 10 | `optimization` | — | **Implemented, uncommitted**, sprint-mode (see §7) |
| 11 | `agents` | — | **Implemented, uncommitted**, sprint-mode |
| 12 | `visualization` | — | **Implemented, uncommitted**, sprint-mode |

"Sprint-mode" means: complete source + complete unit-test suite + per-package and repo-wide validation gates passed, but the checklist's Examples, Benchmarks, Documentation-sync, Release, and Certification-recording sections were **intentionally deferred** by explicit instruction (§7).

## 3. Completed Packages — Implementation Summary

Counts below are implementation modules + `__init__.py` + `README.md`; test counts are the package's own unit suite.

- **`optimization`** — 19 modules; 36-symbol public API (spec 10 §7, exact); 111 tests. Six interface-only solver-paradigm ABCs (`LinearProgrammingModel`, `MixedIntegerProgrammingModel`, `ConstraintProgrammingModel`, `MultiObjectiveModel`, `EvolutionaryMetaheuristicModel`, `NetworkOptimizationModel` — one abstract method each, zero concrete subclasses). `OptimizationProblem` publish/supersede governance; `OptimizationExecutor` with category-driven dispatch, §11/§14 pairing validation, and an iterative branch for evolutionary models; `PlanComparator`/`SensitivityAnalyzer` delegating **all** statistics to `analytics` (mechanically enforced by test).
- **`agents`** — 20 modules; 41-symbol public API (spec 11 §7, exact); 174 tests. `Agent`/`Tool`/`AgentMemory` interface-only; `PolicyEngine` with a mechanically proven three-outcome contract (proceed / route-to-approval / `PermissionDeniedError`); `Task` lifecycle with the `AWAITING_APPROVAL` state; `TaskExecutor` (policy gate → dispatch → retry per `connectors.RetryPolicy` → persist → audit, plus `resume()` for approval resolution — see §10); `WorkflowEngine` goal decomposition with proven direct composition of `simulation.ExperimentRunner` and `optimization.OptimizationExecutor`/`PlanComparator`; `AgentAuditTrail` mirroring `decision.DecisionAuditTrail`; dual registries (`REGISTRY` + `TOOLS`).
- **`visualization`** — 16 modules; 29-symbol public API (spec 12 §7, exact); 118 tests. `Visualization`/`Renderer` interface-only; eight-member closed `VisualizationCategory` with a flagship fixture per category; `PresentationModel` (backend-independent, carries no rendered bytes); `Dashboard` as the series' only lifecycle-free `BaseEntity` (no `status`, no `with_state()` — deliberate); `DashboardBuilder`/`ReportBuilder` as the series' **first concrete `core.BaseBuilder` subclasses**; `RenderingPipeline` as the single rendering code path for live and exported output (proven by round-trip test); dual registries (`REGISTRY` + `RENDERERS`).

Every package ships the platform's standard mechanical acceptance proofs as tests in its `test_public_api.py`: no-fact-recomputation (forbidden-engine-import scan), immutability, interface purity, dependency direction **both ways** (AST walk of own imports + reverse scan of every lower package), and no-backend-coupling (lowercase source scan for solver/LLM-provider/charting-library strings — even a docstring mention fails).

## 4. Package Dependency Graph

```
                                    ┌──────────────┐
                                    │ visualization │  (final; nothing imports it)
                                    └──────┬───────┘
                                           │ reads AgentAuditEntry + all result types
                                    ┌──────┴───────┐
                                    │    agents     │
                                    └──────┬───────┘
                                           │ reads OptimizationResult; composes ExperimentRunner/
                                           │ OptimizationExecutor (in concrete Agents/tests)
                                    ┌──────┴───────┐
                                    │ optimization  │
                                    └──────┬───────┘
                    simulation ← digital_twin ← decision ← analytics ← kpis
                                           │
                              events ← ontology ← core

   Cross-cutting (importable by any domain package): registry, plugins, connectors
```

Direction rules, all mechanically enforced by tests:

- A package may import only itself, `core`/`ontology`/`events`, the cross-cutting three, and packages strictly below it.
- No lower package imports a higher one (reverse-direction AST scans exist in `optimization`, `agents`, and `visualization` `test_public_api.py`, covering 11/12/13 lower packages respectively).
- `agents` is the only domain package that imports `connectors` (for the `RetryPolicy` value object only, per spec 11 §12) — the placeholder-era claim in old READMEs that nothing above `connectors` touches it is superseded by the locked spec.
- `visualization` imports `agents` only for `AgentAuditEntry` as renderable evidence.

## 5. Interface-Only Packages and Abstractions

The platform ships **zero** concrete implementations of any of the following — each is a deliberate extension point, and interface-purity tests fail if a concrete subclass ever appears in `src/`:

| Package | Interface-only ABCs | Abstract method(s) |
|---|---|---|
| `kpis`…`digital_twin` | (per their own specs — `BaseKPI` has built-ins; see each spec) | — |
| `simulation` | 4 methodology ABCs (`MonteCarloModel`, `DiscreteEventModel`, `SystemDynamicsModel`, replay) | one per category |
| `optimization` | 6 paradigm ABCs | one per category (`_solve_lp`, `_solve_mip`, `_solve_cp`, `_solve_pareto`, `_iterate`, `_solve_network`) |
| `agents` | `Agent`, `Tool`, `AgentMemory` | `_act` (shared); `invoke`; `remember`/`recall` |
| `visualization` | `Visualization`, `Renderer` | `_render` (shared); `render` |

Two shared-method postures coexist by design: `simulation`/`optimization` categories share **no** abstract method (paradigms differ in computational shape); `decision`/`agents`/`visualization` share **one** (`_decide`/`_act`/`_render` — categories are domain/presentation roles, not algorithms). Do not "harmonize" them.

## 6. Registries, Plugin Architecture, and Extension Points

### Registries (type-level: "which types does this installation know")

Every domain package holds a `registry.Registry` specialization in its `_registry.py`, with the identical `@register` decorator pattern (empty-code → `<Pkg>ValidationError`; duplicate code → `<Pkg>VersionConflictError`, raised at registration time, never deferred). Two packages hold **two** registries for orthogonal registrable concepts — never merge them:

- `agents`: `REGISTRY` (`type[Agent]`, name `"agents"`) + `TOOLS` (`type[Tool]`, name `"agents.tools"`)
- `visualization`: `REGISTRY` (`type[Visualization]`, name `"visualization"`) + `RENDERERS` (`type[Renderer]`, name `"visualization.renderers"`)

Keep the three-way distinction sharp everywhere: registry = known **types**; repository (`TaskRepository`, `DashboardRepository`, run repositories) = existing **instances**; `discovery.py` = **query facade** over the instance store (`core.PredicateSpecification` factories, empty-never-raise).

### Governed-artifact stores (process-wide, module-level, deliberately not in `__all__`)

- `simulation.scenario.publish_scenario` / `published_scenario` / `scenario_history`
- `optimization.problem.publish_problem` / `published_problem` / `problem_history`
- `agents.policy.publish_policy` / `published_policy` / `published_policies` / `policy_history`
- `agents.capability.publish_capabilities` / `published_capabilities`

All follow the same Active-is-a-contract rule: changing an `Active` artifact without a version bump raises the package's conflict error (`ScenarioConflictError`/`ProblemConflictError`/`PolicyConflictError`); a bumped republication transitions the prior version to `Superseded` and appends it to history.

### Entry-point groups (wired via `registry.EntryPointDiscovery`/`EntryPointSpec`)

One group per domain package (`mineproductivity.kpis`, `.analytics`, `.decision`, `.digital_twin`, `.simulation`, `.optimization`) plus the dual-registry groups `mineproductivity.agents`, `mineproductivity.agents.tools`, `mineproductivity.visualization`, `mineproductivity.visualization.renderers`. Each of the three new packages has an end-to-end "sitepack" fixture test (temp module + monkeypatched `importlib.metadata.entry_points` + real `EntryPointDiscovery().discover(...)`) proving the platform-side registration path.

### The full extension-point inventory

1. Concrete solver adapters (`optimization`, any of the six paradigms) — subclass + `@register`.
2. Concrete reasoning backends (`agents`) — subclass `Agent`, `@register`. LLM-provider SDKs live in the plugin, **never** in this repo (string-scan enforced).
3. Concrete tools (`agents`) — subclass `Tool`, `@register_tool`.
4. Memory backends (`agents`) — subclass `AgentMemory`; wired per-agent, no registry entry by design.
5. Presentation types (`visualization`) — subclass `Visualization`, `@register`.
6. Rendering backends (`visualization`) — subclass `Renderer`, `@register_renderer`; charting/templating/doc-gen libraries live in the plugin (string-scan enforced).
7. Governed artifacts (scenarios, problems, policies, capability sets, themes) — authored data, no code change.
8. Production persistence — implement `core.BaseRepository[Entity, str]` directly; every `*Repository` in the platform is a literal `type` alias, never a package-specific ABC.
9. Closed-enum categories (`SimulationCategory`, `OptimizationCategory`, `AgentCategory`, `VisualizationCategory`) — adding a member is a governance-reviewed change, not a routine edit.

## 7. Intentionally Deferred Work (the sprint contract)

The final sprint's instructions explicitly prioritized implementation over release artifacts. The following were **deliberately not done** for `optimization`, `agents`, and `visualization`, and are the incoming owner's backlog (details in §13–§15):

- `examples/<pkg>/` scripts (5 per package, per each checklist)
- `benchmark/reports/<pkg>/` latency/throughput reports
- CHANGELOG / README / ROADMAP / `docs/architecture/README.md` / citation-file synchronization
- Version bump(s) and release review (`__version__` is still `1.8.0`; three milestones are unreleased)
- Formal ≥95% coverage measurement and any resulting top-up tests
- Certification recording (the acceptance proofs run as tests; writing them into a PR description remains)

Nothing else was skipped: source, tests, type-safety, and architecture conformance for all three packages are complete.

## 8. Reference Implementations

The platform's runnable "reference implementations" are, by design, its **in-memory infrastructure plus test fixtures** — the packages themselves ship no domain algorithms:

- `core.InMemoryRepository` — the reference `BaseRepository` backend everywhere (no locking of its own; per-id write serialization is the *caller's* contract, see §11).
- `events.bus._InMemoryEventBus` / `events.store._InMemoryEventStore` — reference transport/store, used across decision/digital_twin/simulation/agents tests.
- `PolicyEngine` (agents) and `RenderingPipeline` (visualization) — the only two "engines" in the top three packages with real reference logic; both are concrete and fully tested.
- Test fixtures act as reference plugin implementations: e.g. `MIP.ExecutorBoundEcho` (optimization), the ten per-category flagship agents (`tests/unit/agents/test_executor.py::TestFlagshipCategories`), the eight per-category flagship visualizations (`tests/unit/visualization/test_abstractions.py`), and the sitepack entry-point fixtures in each `test__registry.py`. When writing the deferred `examples/`, start by adapting these fixtures — they are already spec-conformant.
- Cross-layer worked examples live as tests: spec 11 §19 (ShiftSupervisor/Fleet/Maintenance workflow) in `tests/unit/agents/test_workflow.py`; spec 12 §15/§19 (multi-source dashboard, exported report) in `tests/unit/visualization/test_pipeline.py` and `test_export.py`.

## 9. Known Architectural Compromises

These are accepted, documented trade-offs — not bugs. Each is disclosed in the relevant module docstring.

1. **Process-wide, module-level governance stores** (scenarios/problems/policies/capabilities). Global mutable dicts behind a lock. Test isolation relies on unique codes per test (uuid suffixes). There is no reset/clear API and no per-tenant scoping — a production deployment would need a real store behind the same functions.
2. **`agents.TaskExecutor` pulls *every* published policy** and lets `PolicyEngine` filter. A capability-scoped rule (`"capability=<name> -> ..."`) gates only tasks requiring that capability; an *unscoped* rule gates **every task in the process** — documented as a global-freeze capability, but it is also a foot-gun for careless policy authoring and for test cross-contamination if a test ever publishes an unscoped Active deny policy.
3. **Retry backoff sleeps for real** (`time.sleep` in `TaskExecutor._dispatch`). No injectable `sleep_fn` (the spec fixed the constructor surface). Tests avoid delay with `base_delay_s=0.0`.
4. **Audit trails are linear-scan on `query()`** (`decision` and `agents` alike) — disclosed in both docstrings as fine for reference scale, index-later-without-API-change.
5. **The remove-then-add repository swap is not atomic** on the reference `InMemoryRepository`. Every executor translates a mid-swap `NotFoundError`/`DuplicateError` into its package's `ExecutionError` naming the §32 serialization contract. A production repository MUST serialize same-id writes.
6. **`agents` audit records terminal outcomes only** (completed, approval-rejected) — pause/skip marker results are returned but not recorded. Spec 11 §21's "every AgentResult" was read as "every terminal outcome"; revisit at audit if you disagree, it is a two-line change plus tests.
7. **Statelessness of Agents/Visualizations is convention-enforced**, not runtime-enforced — tests demonstrate the pattern and docstrings mandate it, but nothing stops a plugin author from mutating instance state.

## 10. Implementation Decisions That Differ Slightly From the Specifications

Every deviation below resolves a point the locked spec leaves genuinely under-determined; each is disclosed in the module docstring at the cited location. None contradicts an explicit spec sentence.

**optimization**
- Iterative (evolutionary) termination: value-equality convergence OR `problem.parameters["max_iterations"]` (default **100**) — spec says only "convergence or a termination bound" (`executor.py`).
- The §11 LP-continuous-variables rule and §14 objective-count rules are enforced in `OptimizationExecutor._validate_pairing`, not in `OptimizationProblem.validate()` (a problem cannot know its model's category before registration).
- `discovery.by_category` resolves lazily at `list()` time through the published-problem store + `REGISTRY` (runs carry no category field); unpublished/unregistered = no match, never a raise.

**agents**
- **`TaskExecutor.resume(task_id, *, approval, context)` is an added public method** — the spec fixes only `execute()`'s signature but requires the Approved→Running-and-dispatch / Rejected→Failed-with-audited-warning transitions to happen somewhere, while forbidding the executor from *resolving* requests. `resume()` applies an already-resolved `ApprovalRequest`; a `PENDING` one is rejected as structurally invalid. This is the single largest API addition beyond spec text — review it first.
- The policy gate's inputs come from the governance stores: `published_capabilities(task.agent_code)` (no published set ⇒ zero permissions) and `published_policies()`. `published_policies()` and the whole `capability` store are additions the executor's wiring required.
- Reference rule interpretation: `PolicyEngine` treats `rule` strictly as data; the form `"capability=<name> -> <effect>"` scopes applicability to tasks whose `state.attributes["required_capabilities"]` contains `<name>`; any other rule form applies unconditionally. Effects come from the `denies`/`requires_approval` **flags**, never the rule text.
- A task's required capabilities ride in `state.attributes["required_capabilities"]` (the spec's own open-mapping escape hatch).
- §12's `final_state` is the task's current state — the executor never invents state on an agent's behalf; agents communicate via `AgentResult`.
- `AgentAuditEntry.scope` is derived from the task's string-valued `state.attributes` entries (the same vocabulary `by_scope` queries).
- `WorkflowEngine.decompose` is caller-authored: `goal.success_criteria["agent_codes"]` names the agents in order (first = coordinator; delegation chain recorded in `state.attributes["delegation_chain"]`); absent/empty ⇒ zero tasks, mirroring `ExperimentRunner`'s zero-trials convention. Choosing decomposition targets is a reasoning-backend decision the charter excludes.
- `communication.py` does **not** import `events` at runtime (an unused import; composition happens at the caller, proven in `test_communication.py`'s EventBus round-trip). Likewise `workflow.py` does not runtime-import `simulation`/`optimization` — the §13 compositions live in concrete Agents (test-proven), matching the spec's "WorkflowEngine/**the assigned Agent** composes ... directly".
- `Task.validate()` runs via `__post_init__` (`core.BaseEntity` has no validation hook of its own). Same for `Dashboard` in visualization.

**visualization**
- Spec 12 §6 lists **no `metadata.py`**, so `VisualizationCategory`/`VisualizationMetadata` live in `abstractions.py` (the checklist's "matching design spec §6 exactly" wins over the sibling-package convention).
- `DashboardBuilder.build()` assigns a fresh `"DASH-<uuid12>"` id per build — the §12 builder surface names no id-choosing step, and `id` (not `name`) is the repository key.
- `reset()` on both builders clears accumulated steps but keeps construction-time identity (`owner`; `report_code`+`pipeline`) — a reading of `BaseBuilder.reset()`'s "initial state".
- Unknown visualization/renderer codes raise `DashboardNotFoundError` (the spec's own exceptions docstring assigns registry misses to it, despite the name).

**cross-cutting**
- Intra-package import cycles (abstractions ↔ task/result, abstractions ↔ widget/presentation) are broken with `TYPE_CHECKING` imports + postponed annotations. The public API and mypy --strict are unaffected.
- All metadata types use the platform's name-defaults-to-code `_normalize()` convention (`BaseMetadata.name` inherited).

## 11. Known Technical Debt

Beyond §9's accepted compromises:

1. **Coverage for the three new packages is unmeasured** against the ≥95% checklist bar. Known likely gaps: `optimization.executor`'s repository-race branch, `agents.executor._replace`'s race branch, assorted `__repr__`s. Run `pytest --cov=mineproductivity.optimization --cov=mineproductivity.agents --cov=mineproductivity.visualization --cov-branch` and top up.
2. **`analytics` (v1.5.0) still lacks `examples/analytics/` and `benchmark/reports/analytics/`** — a pre-sprint gap (decision's equivalent gap was closed in July 2026; analytics' never was).
3. **Stale placeholder language in auxiliary READMEs.** Each phase historically surfaced "future `X`" / inverted-dependency claims in *other* packages' `src/mineproductivity/*/README.md`. The `agents` and `visualization` package READMEs were rewritten, but a repo-wide grep for `will be depended on by`, `not yet implemented`, `the future` has **not** been done since Phase 09.
4. **Auxiliary placeholder packages** remain 7-line stubs with skeleton-era READMEs: `benchmark`, `certification`, `cli`, `config`, `datasets`, `exceptions`, `io`, `typing`, `utils`, `validation` (under `src/mineproductivity/`). None has a locked spec. Decide their fate before 2.0 (§19).
5. **`examples/ai/` and `examples/visualization/` are README-only placeholders** from the skeleton phase; there is no `examples/optimization/` or `examples/agents/` at all.
6. **Windows/dev-environment quirks** (documented from experience, worth keeping): re-run `./.venv_check/Scripts/python.exe -m pip install -e . -q --no-deps` after *every* `__version__` change or `tests/unit/core/test_public_api.py`'s metadata test fails; run `scripts/quality/check_docs.py` only from an env with the package installed; avoid long bash heredocs (command-length limit) and use `python -X utf8` for any scripted file generation (cp1252 mangles `§`).
7. **Test-module import discipline:** never `import tests.unit.<pkg>.test_x` from another test module — double-execution under two identities re-registers registry fixtures and fails ~10 tests. Each test file owns its uniquely-coded fixtures.

## 12. Documentation Synchronization Still Required

Per `CLAUDE.md` Rule / End-of-Phase Standard step 2, for Phases 10–12 (none done yet):

- `README.md` — Project Status milestone table, "What's New", architecture/dependency tables, any per-package status lines
- `ROADMAP.md` — phase statuses for 10/11/12 → implemented/released
- `CHANGELOG.md` — entries for each released version (§16)
- `docs/architecture/README.md` — implementation-status annotations (three known spots per prior phases)
- `docs/design/1{0,1,2}_*.md` checklists — `**Status:** Not started` headers are now false; update, and tick or explicitly-defer boxes honestly (do **not** tick Examples/Benchmarks/Coverage boxes until the artifacts exist)
- Citation files at each version bump: `CITATION.cff`, `docs/citation/CITATION.md`, `docs/citation/MineProductivity.bib` — always the **Concept DOI `10.5281/zenodo.21172767`** (CLAUDE.md Rule 3)
- Sweep for stale cross-README claims (§11 item 3); verify the root README dependency diagram shows `agents → connectors (RetryPolicy)` and `visualization → agents` correctly
- Validation: `python scripts/quality/check_docs.py` from `.venv_check` — 0 broken links, 0 failed snippets

## 13. Release Engineering Still Required

- Review + commit the sprint working tree (nothing is committed).
- Version review per SemVer and repo convention (one MINOR per milestone) — see §16 for the recommended sequence. Update `src/mineproductivity/__init__.py.__version__` **only** (single source; `pyproject.toml` reads it via `[tool.hatch.version]`), then reinstall editable before running tests.
- Full End-of-Phase Standard per released phase (CLAUDE.md Rule 4): Architecture QA → repo sync → `check_docs.py` → `ruff` + `mypy --strict` + full `pytest` + `scripts/quality/smoke_test.py` + `scripts/quality/perf_smoke.py` → version review → release-readiness report.
- Certification recording: write the §35/§33 acceptance-proof results into each release's PR description (the proofs already run as tests; this is transcription).
- Tag/GitHub-release/Zenodo archival per whatever the repo's release history shows for 1.5.0–1.8.0.

## 14. Benchmarks and Examples Still Outstanding

Per the locked checklists (file names are contractual):

| Package | Examples (5 each) | Benchmarks |
|---|---|---|
| `optimization` | `01_mip_fleet_allocation.py`, `02_plan_comparison.py`, `03_sensitivity_sweep.py`, `04_candidate_scenario_search.py`, `05_plugin_solver_adapter.py` | run-repository latency; parallel re-solve throughput → `benchmark/reports/optimization/` |
| `agents` | `01_single_agent_task.py`, `02_policy_gated_approval.py`, `03_multi_agent_workflow.py`, `04_hypothesis_and_plan_search.py`, `05_plugin_agent_and_tool.py` | `TaskRepository` get/list latency; `WorkflowEngine` parallel throughput → `benchmark/reports/agents/` |
| `visualization` | `01_single_widget_render.py`, `02_multi_source_dashboard.py`, `03_export_report.py`, `04_simulation_playback.py`, `05_plugin_visualization_and_renderer.py` | `DashboardRepository` latency; multi-widget parallel render throughput → `benchmark/reports/visualization/` |
| `analytics` (pre-existing gap) | `examples/analytics/` (mirror decision's completion pass) | `benchmark/reports/analytics/` |

All examples must pass `mypy --strict` + `ruff` (checklist requirement). Adapt the test fixtures (§8) rather than inventing new model behavior. Benchmark report format: mirror `benchmark/reports/simulation/2026-07-08-simulation-v1.8.0.md`.

## 15. Recommended Audit Sequence

Run **before** any release commit, in this order (cheap-to-expensive, dependency order within):

1. **Working-tree review** — read the three new packages against their checklists box-by-box, `optimization → agents → visualization`. Priority review targets: `agents.TaskExecutor.resume()` (§10's biggest addition), `PolicyEngine`'s reference rule interpretation, `WorkflowEngine.decompose`'s caller-authored strategy, the terminal-only audit decision (§9 item 6).
2. **Mechanical gates** — `ruff check .`, `ruff format --check .`, `mypy --strict src/mineproductivity`, full `pytest`, `smoke_test.py`, `perf_smoke.py` (all green at handoff; re-verify on your machine).
3. **Coverage pass** — measure the three packages, top up to ≥95%, attach reports.
4. **Checklist reconciliation** — update the three checklist files' statuses honestly; diff checklist-vs-tree for *every* package (memory shows "feature-complete" claims have hidden gaps before — that is how the decision and analytics gaps happened).
5. **Docs sweep** — §12 in full, including the stale-language grep.
6. **Examples + benchmarks** — §14 (these double as end-to-end audit of the public APIs; write them before releasing, they routinely surface API paper-cuts while fixing is still cheap).

## 16. Recommended Release Sequence

Preserve the repo's one-MINOR-per-milestone convention — three milestones, three releases, oldest layer first, each with its own End-of-Phase Standard and CHANGELOG entry:

1. **v1.9.0 — Optimization** (commit sprint's optimization source+tests; examples/benchmarks/docs for it; bump; release)
2. **v1.10.0 — AI Agents** (same treatment)
3. **v1.11.0 — Visualization** (same; note in CHANGELOG this completes the architecture)
4. **v2.0.0** — see §19.

A single combined "v1.9.0 architecture-complete" release is defensible if you prefer fewer releases, but it breaks the established milestone↔version mapping and makes the CHANGELOG history lie about cadence; I recommend against it. Either way: commit the three packages as three logically separate commits even if released together — the tree at handoff mixes them.

Remember after each bump: editable reinstall into `.venv_check`, citation-file sync, Concept DOI unchanged.

## 17. Recommended Repository Cleanup Sequence

After the three releases, before 2.0:

1. Stale-language grep sweep across all `src/mineproductivity/*/README.md` + root docs (§11 item 3).
2. `examples/ai/` — placeholder from the skeleton era; either populate as agents-adjacent examples or remove and let `examples/agents/` own the space (removal needs a broken-link check via `check_docs.py`).
3. Decide each auxiliary placeholder package's fate (§11 item 4): implement (only `cli` has an obvious post-architecture purpose), or delete the stubs and record the removal in an ADR. Do not leave nine 7-line stubs in a 2.0.
4. `benchmark/` *source package* stub vs. the top-level `benchmark/` directory — resolve the naming shadow.
5. Verify no `__pycache__`, scratch, or `.venv_check` artifacts are tracked.
6. Re-run the full gate + `check_docs.py` after every deletion.

## 18. Future Implementation Hooks (do not build without cause)

- The four domain-specific `VisualizationCategory` members are the anticipated landing zones for real UI work (simulation playback, twin view, plan comparison, agent explanation) — all shapes already serialize via `core.serialization` with no bespoke contracts.
- `agents` spec 11 §19 explicitly leaves a `PlanningAgent → OptimizationExecutor → ShiftSupervisorAgent` composition "possible without being designed" — build it as a plugin/example, never as new platform code.
- Audit-trail indexing (§9 item 4) and production repository backends (§6 item 8) can land without any public-API change.
- **Post-v2.0 proposal, do not implement:** the analytics maturity assessment framework recorded in `ROADMAP.md`'s Future Architecture Proposals (packaging deliberately undecided — possibly `mineproductivity.assessment`, possibly an application on top). It is a proposal, not a phase.

## 19. Recommended Version 2.0 Release Plan

2.0 should be the **certification milestone**, not a feature release. Gate it on:

1. v1.9.0–v1.11.0 shipped clean (§16), all docs synchronized (§12), all examples/benchmarks landed (§14), analytics gap closed.
2. Repository cleanup complete (§17) — in particular, an explicit ADR-recorded decision on every placeholder package. A 2.0 with undocumented dead stubs is not a 2.0.
3. The "Reference Implementation Blueprint fully satisfied" milestone tracked in `ROADMAP.md` formally assessed: every checklist for every package either fully ticked or carrying an explicit, linked deferral.
4. A repository-wide acceptance-proof run recorded as a single certification document (e.g. `docs/certification/2.0-certification.md`): all per-package proofs + full gate outputs + coverage figures.
5. SemVer honesty check: 2.0.0 with **zero breaking changes** is legitimate here as a stability declaration ("architecture complete and locked; public APIs now stable-by-contract") — say exactly that in the CHANGELOG. If the audit (§15) forces any breaking API fix (e.g. you reject `TaskExecutor.resume()` and reshape approval application), 2.0 is where it lands, with migration notes.
6. Zenodo: archive 2.0, keep the Concept DOI in all citations, and update `CITATION.cff` version + date.

After 2.0: the platform is a stable substrate; new value ships as plugins (solvers, reasoning backends, renderers, connectors' vendor adapters) and applications (`cli`, dashboards), evaluated against the locked specs — plus whatever the maturity-assessment proposal becomes, as its own governed design cycle.

---

*Everything asserted here about test/gate status was verified on 2026-07-12 against the working tree: 2,986 passed, ruff clean, `mypy --strict` clean (314 files), 403 of those tests belonging to the three uncommitted packages. Trust the tree over this document wherever they disagree — and check `src/mineproductivity/<pkg>/__init__.py` line counts (implemented ≈ 90+, stub ≈ 7) before believing any status claim, including mine.*
