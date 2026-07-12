"""``mineproductivity.agents`` -- the AI-agent orchestration layer
(design spec 11): a model-independent orchestration layer for
autonomous and semi-autonomous work, built directly above
``optimization``. Defines *how* agent work is governed, gated,
executed, delegated, and audited -- ``Agent``/``Tool``/``AgentMemory``
are interface-only extension points; choosing a reasoning backend is
exactly the implementation decision this package excludes (§3.1, §4).

Public API (design spec §7) -- every name stable once implementation
begins.
"""

from __future__ import annotations

from mineproductivity.agents._registry import REGISTRY, TOOLS, register, register_tool
from mineproductivity.agents.abstractions import Agent, AgentContext
from mineproductivity.agents.approval import ApprovalRequest, ApprovalStatus
from mineproductivity.agents.audit import AgentAuditEntry, AgentAuditTrail
from mineproductivity.agents.capability import AgentCapabilitySet, Permission
from mineproductivity.agents.communication import AgentMessage, DelegationRequest
from mineproductivity.agents.conversation import ConversationContext, ConversationTurn
from mineproductivity.agents.discovery import by_category, by_scope
from mineproductivity.agents.exceptions import (
    AgentExecutionError,
    AgentValidationError,
    AgentVersionConflictError,
    PermissionDeniedError,
    PolicyConflictError,
    TaskNotFoundError,
)
from mineproductivity.agents.executor import TaskExecutor
from mineproductivity.agents.goal import Goal
from mineproductivity.agents.memory import AgentMemory
from mineproductivity.agents.metadata import AgentCategory, AgentMetadata
from mineproductivity.agents.persistence import TaskRepository
from mineproductivity.agents.policy import AgentPolicy, PolicyEngine, PolicyStatus
from mineproductivity.agents.result import AgentResult
from mineproductivity.agents.state import TaskState
from mineproductivity.agents.task import Task, TaskStatus
from mineproductivity.agents.tool import Tool, ToolInvocation, ToolMetadata
from mineproductivity.agents.workflow import WorkflowEngine

__all__ = [
    "Agent",
    "AgentAuditEntry",
    "AgentAuditTrail",
    "AgentCapabilitySet",
    "AgentCategory",
    "AgentContext",
    "AgentExecutionError",
    "AgentMemory",
    "AgentMessage",
    "AgentMetadata",
    "AgentPolicy",
    "AgentResult",
    "AgentValidationError",
    "AgentVersionConflictError",
    "ApprovalRequest",
    "ApprovalStatus",
    "ConversationContext",
    "ConversationTurn",
    "DelegationRequest",
    "Goal",
    "Permission",
    "PermissionDeniedError",
    "PolicyConflictError",
    "PolicyEngine",
    "PolicyStatus",
    "REGISTRY",
    "TOOLS",
    "Task",
    "TaskExecutor",
    "TaskNotFoundError",
    "TaskRepository",
    "TaskState",
    "TaskStatus",
    "Tool",
    "ToolInvocation",
    "ToolMetadata",
    "WorkflowEngine",
    "by_category",
    "by_scope",
    "register",
    "register_tool",
]
