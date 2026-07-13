# Examples - mineproductivity.agents

## Purpose

Runnable, minimal, self-contained scripts demonstrating the AI Agents package: a single governed agent task, human-in-the-loop policy-gated approval, a multi-agent workflow, a planning agent composing `simulation` and `optimization` directly, and a third-party agent+tool plugin. Every concrete agent and tool in these scripts is example-local — the package ships zero concrete agents, tools, or memory backends by design (`Agent`/`Tool`/`AgentMemory` are interface-only extension points, design spec §3.1, §4, ADR-0011).

## Scope

Example scripts and their direct output. No test assertions live here (see `tests/unit/agents/` for that); each script is meant to be read and run by a human evaluating the package.

## Responsibilities

- Show idiomatic usage of the AI Agents public API.
- Serve as executable documentation that stays correct because it is actually run.
- Demonstrate the platform disciplines end-to-end: the policy gate → dispatch → persist → audit sequence, human approval via a caller-supplied `ApprovalRequest`, delegation recorded in open state attributes, and cross-layer composition (`simulation.ExperimentRunner`, `optimization.OptimizationExecutor`/`PlanComparator`) living in the concrete agent — never in the orchestrator.

## Contents

- `01_single_agent_task.py` - a governed `Task` dispatched through `TaskExecutor`, producing an audited `AgentResult` with a `decision.Explanation`.
- `02_policy_gated_approval.py` - a capability gated behind approval (routes to `AwaitingApproval`, resumed by a caller-supplied approved `ApprovalRequest`), plus a denying policy's hard-stop `PermissionDeniedError`.
- `03_multi_agent_workflow.py` - the design spec §19 worked example: a `ShiftSupervisor` agent coordinating a `Fleet` and a `Maintenance` agent via `WorkflowEngine.decompose`/`run`, with the delegation chain carried in state attributes.
- `04_hypothesis_and_plan_search.py` - a `PLANNING` agent composing `simulation.ExperimentRunner` (hypothesis exploration) and `optimization.OptimizationExecutor`/`PlanComparator` (candidate-plan search) directly (design spec §13).
- `05_plugin_agent_and_tool.py` - a third-party-style `Agent` and `Tool` registered via entry points into the two orthogonal registries (`REGISTRY` for agent types, `TOOLS` for tool types, design spec §22, §31), mirroring `examples/registry/01_register_and_discover.py`'s real-discovery pattern.

## Dependencies

`mineproductivity[analytics]` (for `analytics`' statistical primitives, used transitively by the `optimization` composition in example 04). No network access; every task, policy, and scenario is constructed in-script.

## Running the Examples

```bash
pip install -e ".[analytics]"
python examples/agents/01_single_agent_task.py
python examples/agents/02_policy_gated_approval.py
python examples/agents/03_multi_agent_workflow.py
python examples/agents/04_hypothesis_and_plan_search.py
python examples/agents/05_plugin_agent_and_tool.py
```

Each script exits `0` and prints its own output; there is nothing to configure.

## Future Work

Add a conversation/memory walkthrough once first-party or third-party `AgentMemory` backends exist (deliberately never shipped inside `agents` itself, design spec §4).

## References

- [`docs/architecture/11_AI_Agents_Design_Specification.md`](../../docs/architecture/11_AI_Agents_Design_Specification.md) §10, §12, §13, §16–§17, §19, §22, §31
- [`src/mineproductivity/agents/README.md`](../../src/mineproductivity/agents/README.md)
- [`docs/adr/ADR-0011-AI-Agents.md`](../../docs/adr/ADR-0011-AI-Agents.md)
