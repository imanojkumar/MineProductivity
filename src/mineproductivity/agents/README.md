# mineproductivity.agents

## Purpose

The AI-agent orchestration layer (design spec 11) — a model-independent orchestration layer for autonomous and semi-autonomous work, built directly above `optimization`. It defines *how* agent work is governed (`AgentPolicy`/`PolicyEngine`/`AgentCapabilitySet`), gated (`ApprovalRequest`), executed (`Task`/`TaskExecutor`), decomposed and delegated (`Goal`/`WorkflowEngine`/`AgentMessage`/`DelegationRequest`), and audited (`AgentAuditTrail`) — while `Agent`, `Tool`, and `AgentMemory` remain interface-only extension points: choosing a reasoning backend is exactly the implementation decision this package excludes.

## Governing documents

- [`docs/architecture/11_AI_Agents_Design_Specification.md`](../../../docs/architecture/11_AI_Agents_Design_Specification.md)
- [`docs/design/11_AI_Agents_Implementation_Checklist.md`](../../../docs/design/11_AI_Agents_Implementation_Checklist.md)
- [`docs/adr/ADR-0011-AI-Agents.md`](../../../docs/adr/ADR-0011-AI-Agents.md)

## Scope

**What belongs here:** agent/task/policy/approval/workflow/audit orchestration contracts and their reference execution path.

**What must never belong here:** a concrete `Agent`, `Tool`, or `AgentMemory` implementation; any LLM-provider SDK coupling; any recomputation of a KPI, statistical, decision, twin-state, simulation, or optimization fact a lower package already owns.

## Dependencies

**Depends on:** `core`, `events` (transport for `AgentMessage`, composed by callers), `registry`, `connectors` (`RetryPolicy` as the retry-configuration shape, per spec 11 §12), `kpis`, `analytics`, `decision` (`Explanation` reused directly), `digital_twin`, `simulation`, `optimization`.

**Depended on by:** `visualization` (future). No lower package imports `agents`.

## Extension points

Register a concrete `Agent` with `@register` (entry-point group `mineproductivity.agents`) and a concrete `Tool` with `@register_tool` (group `mineproductivity.agents.tools`); implement a `TaskRepository` backend as a `core.BaseRepository[Task, str]`; subclass `AgentMemory` for a memory backend (wired per-agent, not globally discovered).
