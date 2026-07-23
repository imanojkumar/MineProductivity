# Package Tutorial 12 — AI Agents (Deep)

!!! abstract "Milestone 2 · Package Tutorials · Tutorial 12 of 13"
    Deep, full-surface tutorial for `mineproductivity.agents` — **model-independent
    orchestration** of autonomous work: governed tasks, policy-gated capabilities,
    tools, and multi-agent workflows composing the whole of Unit B. Authored to
    **Package Tutorial Template v1.0** under the
    [Package Tutorial Implementation Standard](../../learning/PACKAGE_TUTORIAL_IMPLEMENTATION_STANDARD.md).

## Objective

Master the working surface of `mineproductivity.agents`: the interface-only
`Agent`/`Tool`/`AgentMemory`, the governed `Task` lifecycle with `AwaitingApproval`
and `resume()`, the `TaskExecutor` (gate → act → persist → audit), the
`PolicyEngine`/`AgentPolicy`/capabilities, the `WorkflowEngine`, the dual
`REGISTRY`/`TOOLS` registries, and — the payoff — **a plugin agent and tool**.

All 41 public symbols (`mineproductivity.agents.__all__`) are accounted for under
the **coverage convention** (§5): **25 [deep]** / **16 [ref]**. Public APIs only.

## Prerequisites

- Package Tutorials [8 — Decision](08_decision.md), [10 — Simulation](10_simulation.md),
  [11 — Optimization](11_optimization.md): an agent *composes* these as tools, and
  audits like decision does (§3).

**No Fundamentals lesson** — first exposure; §1 and §3 carry their own why.

## Running the examples

Every code block below is executed and its output pasted verbatim. Five scripts:

```bash
pip install -e ".[analytics]"
python examples/agents/01_single_agent_task.py   # ...and 02–05
```

---

## 1. Why this package exists

The layers below give you governed measurement, characterisation, decisions, twins,
simulation, and optimization. An **agent** orchestrates them into autonomous work: a
`Task` with a `Goal`, dispatched through an executor that **gates it against policy,
acts, persists, and audits** — the same accountability discipline as `decision`,
applied to *action*.

Two commitments define it. It is **model-independent**: `Agent`, `Tool`, and
`AgentMemory` are interface-only contracts — an LLM SDK, a rules engine, or a plain
heuristic lives in *your* plugin, never in the package. And **authority is
governed**: a `PolicyEngine` can gate a capability behind human approval or deny it
outright, so an autonomous system can never do more than a policy permits.

## 2. Architectural role

`agents` sits near the top, orchestrating everything beneath it:

```
… decision ─► digital_twin ─► simulation ─► optimization ─► agents ─► visualization
```

An agent's tools *are* the lower layers: a planning agent runs a simulation and an
optimization to test a hypothesis; a triage agent reads KPIs and decisions. Agents
add no new domain computation — they **compose** governed capabilities under policy.

## 3. Integration with adjacent layers

**`simulation` (T10) & `optimization` (T11) — agent tools:** a `WorkflowEngine`
planning agent composes a simulation experiment and an optimization search directly
(example 04) — "test a hypothesis, then find the best plan" is one autonomous task.

**`decision` (T8) — the accountability pattern:** an `AgentResult` carries an
explanation and lands in an append-only `AgentAuditTrail`, exactly as a
`Recommendation` does — every actionable run is reconstructable.

**`registry` (T4) — dual registries:** `REGISTRY` (agents) and `TOOLS` (tools) are
`registry.Registry`s; `@register`/`@register_tool` add them, discovered by entry
point (§13).

**`core` (T1):** `Task`, `AgentResult`, `ToolInvocation`, `Goal` are governed value
objects; the executor returns governed results.

**Upward to `visualization` (T13):** an agent's note/recommendation is one source a
dashboard presents.

## 4. Package structure

| Group | Module(s) | Public symbols |
|---|---|---|
| The agent contract | `abstractions`, `memory` | `Agent`, `AgentContext`, `AgentMemory` |
| Tasks & goals | `task`, `goal`, `state`, `executor`, `persistence` | `Task`, `TaskStatus`, `TaskState`, `Goal`, `TaskExecutor`, `TaskRepository` |
| Tools | `tool` | `Tool`, `ToolInvocation`, `ToolMetadata` |
| Policy & approval | `policy`, `capability`, `approval` | `PolicyEngine`, `AgentPolicy`, `PolicyStatus`, `AgentCapabilitySet`, `Permission`, `ApprovalRequest`, `ApprovalStatus` |
| Workflow & communication | `workflow`, `communication`, `conversation` | `WorkflowEngine`, `AgentMessage`, `DelegationRequest`, `ConversationContext`, `ConversationTurn` |
| Results & audit | `result`, `audit` | `AgentResult`, `AgentAuditTrail`, `AgentAuditEntry` |
| Metadata, registry, discovery | `metadata`, `_registry`, `discovery` | `AgentCategory`, `AgentMetadata`, `REGISTRY`, `TOOLS`, `register`, `register_tool`, `by_category`, `by_scope` |
| Exceptions | `exceptions` | `AgentExecutionError`, `AgentValidationError`, `AgentVersionConflictError`, `TaskNotFoundError`, `PermissionDeniedError`, `PolicyConflictError` |

## 5. Public APIs

All 41 exports under the **coverage convention**:

**The spine — [deep]**
: `Agent`, `AgentContext`, `AgentMemory`, `Task`, `TaskStatus`, `TaskExecutor`,
  `Goal`, `Tool`, `ToolInvocation`, `AgentPolicy`, `PolicyEngine`, `Permission`,
  `ApprovalRequest`, `ApprovalStatus`, `WorkflowEngine`, `AgentResult`,
  `AgentAuditTrail`, `AgentMetadata`, `AgentCategory`, `REGISTRY`, `TOOLS`,
  `register`, `register_tool`, `by_category`, `by_scope`

**Everything else — [ref]** — see the table.

### Reference coverage

| Group | Symbols (`[ref]`) | What / when |
|---|---|---|
| Task & tool detail | `TaskState`, `TaskRepository`, `ToolMetadata`, `AgentAuditEntry` | Per-task state; task persistence; a tool's declared metadata; one audit record. |
| Capability & policy | `AgentCapabilitySet`, `PolicyStatus` | The set of capabilities an agent declares; a policy's lifecycle status. |
| Communication | `AgentMessage`, `DelegationRequest`, `ConversationContext`, `ConversationTurn` | Inter-agent messaging and delegation; multi-turn conversation context. |
| Exceptions | `AgentExecutionError`, `AgentValidationError`, `AgentVersionConflictError`, `TaskNotFoundError`, `PermissionDeniedError`, `PolicyConflictError` | Execution failure, invalid metadata, duplicate code, unknown task, a denied capability, conflicting policies. All derive from `core.MineProductivityError`. |

## 6. Conceptual model

Five ideas explain the package.

**A. Agents and tools are interface-only.** `Agent`, `Tool`, `AgentMemory` ship
**zero** implementations — the reasoning backend (LLM, rules, heuristic) is your
plugin. The package governs orchestration, not intelligence.

**B. A task is gated, acted, persisted, audited.** `TaskExecutor.execute` runs a
`Task` through policy checks, the agent's action, persistence, and an append-only
`AgentAuditTrail` — one accountable path.

**C. Authority is a policy.** A `PolicyEngine` with an `AgentPolicy` can route a
capability to `AwaitingApproval` (a supervisor approves, then `resume()` dispatches
it) or **deny** it outright (a hard stop, never a completed result).

**D. Tools compose the platform.** A `Tool` wraps a capability (run a simulation,
solve an optimization); an agent invokes tools, and each `ToolInvocation` is carried
on the result for audit.

**E. Workflows coordinate many agents.** A `WorkflowEngine` decomposes a multi-agent
`Goal` into ordered tasks (coordinator first), each audited — autonomous work that is
still fully reconstructable.

## 7. Real mining examples

The walkthroughs run a night-shift recovery: a single fleet-reallocation agent, an
approval-gated (and a denied) capability, a three-agent coordinated workflow, and a
planning agent composing simulation + optimization — plus a site-pack agent+tool
plugin (§13).

## 8. Step-by-step walkthroughs

### 8.1 A single governed task

A `Task` names its `Goal`, agent, and scope; `TaskExecutor` runs gate → act →
persist → audit; the `AgentResult` carries output and an explanation, and the
append-only `AgentAuditTrail` is queryable by scope. Running
[`01_single_agent_task.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/agents/01_single_agent_task.py):

```text
--- 1. A governed task names its goal, its agent, and its scope ---
task=TASK-HAUL-1 goal='GOAL.RecoverNightShiftHaulage' agent='FLEET.HaulReallocation'

--- 3. The audited result ---
output: {'goal': 'GOAL.RecoverNightShiftHaulage', 'recommended_extra_trucks': 3, 'target_tph': 1200.0}
explanation premises: ('target throughput 1200 t/h not met',)
task status COMPLETED: True

--- 4. The append-only audit trail recorded it, queryable by scope ---
audit entries for pit=north: 1 (agent FLEET.HaulReallocation)
```

### 8.2 Policy-gated approval, and a hard denial

A `PolicyEngine` gates one capability behind approval and denies another. An
approval-gated task routes to `AwaitingApproval` **unaudited**; a supervisor
approves and `resume()` dispatches it to Completed; a denying policy raises
`PermissionDeniedError` — never a completed result. Running
[`02_policy_gated_approval.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/agents/02_policy_gated_approval.py):

```text
--- 2. An approval-gated task routes to AwaitingApproval, unaudited ---
warning: AgentPolicy 'POLICY.FleetReallocationApproval' requires human approval for task 'TASK-APPROVE-1'
status: awaiting_approval; audit entries: 0

--- 3. A supervisor approves; resume() dispatches through to Completed ---
output: {'goal': 'GOAL.ReallocateNightFleet', 'adjusted': True}
status: completed; audit entries: 1

--- 4. A denying policy is a hard stop, never a completed result ---
PermissionDeniedError raised: AgentPolicy 'POLICY.PitShutdownDenied' denies task 'TASK-DENY-1' outright
```

This is the safety core: an autonomous agent can be *allowed*, *gated*, or
*forbidden* per capability — and the executor never resolves an approval itself (the
caller supplies a resolved `ApprovalRequest`).

### 8.3 Multi-agent workflow and tool composition

A `WorkflowEngine` decomposes a `Goal` naming several agents (coordinator first) into
one task each, records the delegation chain, runs them in order, and audits every
result. Separately, a planning agent composes simulation + optimization as tools.
Running
[`03_multi_agent_workflow.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/agents/03_multi_agent_workflow.py)
and
[`04_hypothesis_and_plan_search.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/agents/04_hypothesis_and_plan_search.py):

```text
--- 3. Run in decomposition order; every result is audited ---
  SHIFT_SUPERVISOR.NightShiftCoordinator -> Coordinates the recovery.
  FLEET.HaulReallocation -> Reallocates trucks around the outage.
  MAINTENANCE.BreakdownTriage -> Triages the failed unit.

--- (planning agent) composes simulation + optimization directly ---
hypothesis trials run: 6
best candidate plan (tonnes): 30.0
mean candidate plan (analytics-computed): 27.0
```

The planning agent is the whole Learning Suite composing: a tool runs a *simulation*
of a hypothesis, another runs an *optimization* search, *analytics* summarises — all
orchestrated by one audited agent task.

## 9. Repository example reuse

The five `agents` scripts were each executed (exit `0`), output above.

| Script | Public API it exercises | Walkthrough |
|---|---|---|
| [`01_single_agent_task.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/agents/01_single_agent_task.py) | `Task`, `Goal`, `TaskExecutor`, `TaskStatus`, `AgentResult`, `AgentAuditTrail` | §8.1 |
| [`02_policy_gated_approval.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/agents/02_policy_gated_approval.py) | `PolicyEngine`, `AgentPolicy`, `Permission`, `ApprovalRequest`, `ApprovalStatus`, `PermissionDeniedError` | §8.2 |
| [`03_multi_agent_workflow.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/agents/03_multi_agent_workflow.py) | `WorkflowEngine`, `AgentCategory`, `by_category` | §8.3 |
| [`04_hypothesis_and_plan_search.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/agents/04_hypothesis_and_plan_search.py) | `Tool`, `ToolInvocation`, composing `simulation`/`optimization` | §8.3 |
| [`05_plugin_agent_and_tool.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/agents/05_plugin_agent_and_tool.py) | `Agent`, `AgentMemory`, `AgentMetadata`, `ToolMetadata`, `register`, `register_tool`, `REGISTRY`, `TOOLS` | §13 |

## 10. Common mistakes

| Mistake | What happens | Do this instead |
|---|---|---|
| Importing an LLM SDK into the package | Violates model-independence | Wire the backend in a plugin `Agent` |
| Expecting the executor to resolve an approval | It never does | The caller supplies a resolved `ApprovalRequest`, then `resume()` |
| Treating a denied capability as retryable | It is a hard stop (`PermissionDeniedError`) | Deny means deny; only a policy change permits it |
| Running an action without a policy check | An autonomous system exceeds its authority | Always dispatch through `TaskExecutor`/`PolicyEngine` |
| Not auditing an agent action | Unreconstructable later | `AgentAuditTrail` records every actionable run |
| Putting domain computation in an agent | Duplicates the layers below | Compose them as tools; agents orchestrate |

## 11. Best practices

- **Keep agents/tools model-independent** — the backend belongs in a plugin.
- **Gate every capability with a policy**; approval-gate the risky ones, deny the forbidden.
- **Compose the lower layers as tools**; agents add orchestration, not new computation.
- **Audit every actionable run** — the same discipline as decision.
- **Carry `ToolInvocation`s on the result** so a run's tool calls are traceable.

## 12. Performance considerations

- **The executor is orchestration, not computation** — cost lives in the tools
  (a simulation, an optimization) it invokes, which parallelise on their own terms.
- **Agents are stateless across tasks** (memory is an explicit `AgentMemory`) — safe to share.
- **Workflow decomposition is O(agents)**; tasks run in dependency order.
- **Audit is append-only** — writes never block on a read.

## 13. Extension points — a plugin agent and tool

`agents` ships **zero** concrete agents or tools (interface-only). The extension
point is to implement `Agent` (and any `Tool`/`AgentMemory` it needs), declare
`AgentMetadata`/`ToolMetadata`, and register with `@register`/`@register_tool` —
usually as a plugin; the LLM or rules SDK lives *inside* your agent. The reused
[`05_plugin_agent_and_tool.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/agents/05_plugin_agent_and_tool.py)
discovers a site-pack agent and its tool through the real entry-point path:

```text
--- 1. agents ships zero concrete agents or tools (interface-only) ---
site-pack agents before: []
site-pack tools before:  []

--- 2. A site pack declares both via pyproject.toml entry-points ---
agents discover() is_ok: True loaded: ('sitepack',)
tools  discover() is_ok: True loaded: ('sitepack',)
registered agent: DISPATCH.SitePackReallocation; registered tool: TOOL.SitePackDispatchQuery

--- 3. The discovered agent dispatches like any built-in, consulting its tool ---
agent output: {'idle_trucks': 4}
tool invocations carried on the result: 1
task status COMPLETED: True
```

The **dual registries** are the shape to remember: agents register in `REGISTRY`,
tools in `TOOLS`, each with its own decorator — because an agent and the tools it
calls are independently versioned, discoverable capabilities.

!!! note "The platform bundles no intelligence — on purpose"
    Which reasoning backend suits a task (an LLM, a rules engine, a solver) depends on
    the task, the site, and cost/latency/governance constraints. Interface-only keeps
    that choice — and its heavy dependencies — in your plugin, and keeps the platform's
    *governance* (policy, audit, approval) independent of it.

## 14. Exercises

1. **Run a governed task.** Build a `Task` with a `Goal` and dispatch it through
   `TaskExecutor`; confirm the `AgentAuditTrail` recorded it and the result carries an
   explanation.
2. **Gate a capability.** Add an `AgentPolicy` requiring approval; show the task lands in
   `AwaitingApproval` unaudited, then `resume()` on a resolved `ApprovalRequest` completes it.
3. **Deny a capability.** Add a denying policy and confirm a `PermissionDeniedError` — not a
   completed result. Why is deny a hard stop rather than a warning?
4. **Compose tools.** Sketch a planning agent that calls a simulation tool then an
   optimization tool; why does the agent add no domain computation of its own?
5. **Implement an agent.** Outline a plugin `Agent` backed by a rules heuristic (no LLM);
   which methods do you implement, and why does the package ship none?

## 15. Reference solutions

??? success "Solution 1 — Run a governed task"
    Dispatch through `TaskExecutor.execute(task, ...)`; it runs gate → act → persist →
    audit and returns an `AgentResult` with an explanation. Query the `AgentAuditTrail`
    by scope to confirm the single recorded entry.

??? success "Solution 2 — Gate a capability"
    A `PolicyEngine` carrying an approval `AgentPolicy` routes the task to
    `AwaitingApproval` (audit count 0). The caller resolves an `ApprovalRequest`
    (`ApprovalStatus.APPROVED`) and calls `resume()`, which dispatches through to
    Completed (audit count 1).

??? success "Solution 3 — Deny a capability"
    A denying policy raises `PermissionDeniedError`; there is no completed result. Deny is
    a hard stop because an autonomous system must *never* perform a forbidden action —
    a warning could be ignored; an exception cannot be.

??? success "Solution 4 — Compose tools"
    The agent invokes a simulation `Tool` (seeded trials) then an optimization `Tool`
    (best plan) — each a governed capability from the layers below. The agent orchestrates
    and audits; it re-implements neither the world model nor the solver.

??? success "Solution 5 — Implement an agent"
    You implement the `Agent` contract's action method (and any `Tool`/`AgentMemory` it
    uses), wiring your heuristic. The package ships none because the reasoning backend is a
    per-site choice — interface-only keeps governance independent of intelligence.

## 16. Further reading

- **[`agents` package guide](../../packages/agents.md)** — the capability-tour view.
- **[`agents` API reference](../../api-reference/agents.md)** — every symbol, from source.
- **[AI Agents Design Specification](../../architecture/11_AI_Agents_Design_Specification.md)** · **[ADR-0011](../../adr/ADR-0011-AI-Agents.md)** — model-independence, the policy/approval/audit governance, the dual registries.
- **Package Tutorials [8 — Decision](08_decision.md) · [10 — Simulation](10_simulation.md) · [11 — Optimization](11_optimization.md).**

---

**Next package tutorial:** Visualization (deep) — presenting governed evidence to a
human, the final package. It closes the Learning Suite.
*(Not yet written — Tutorial 13 of 13.)*
