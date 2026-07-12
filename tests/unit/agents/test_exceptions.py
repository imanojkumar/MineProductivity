"""Tests for mineproductivity.agents.exceptions (design spec §6, §30)."""

from __future__ import annotations

from mineproductivity.agents.exceptions import (
    AgentExecutionError,
    AgentValidationError,
    AgentVersionConflictError,
    PermissionDeniedError,
    PolicyConflictError,
    TaskNotFoundError,
)
from mineproductivity.core import MineProductivityError, NotFoundError, ValidationError
from mineproductivity.registry import RegistrationError


class TestHierarchy:
    def test_validation_error_subclasses_core_validation_error(self) -> None:
        assert issubclass(AgentValidationError, ValidationError)

    def test_task_not_found_subclasses_core_not_found(self) -> None:
        assert issubclass(TaskNotFoundError, NotFoundError)

    def test_execution_error_subclasses_root(self) -> None:
        assert issubclass(AgentExecutionError, MineProductivityError)

    def test_version_conflict_subclasses_registration_error(self) -> None:
        assert issubclass(AgentVersionConflictError, RegistrationError)

    def test_policy_conflict_subclasses_registration_error(self) -> None:
        assert issubclass(PolicyConflictError, RegistrationError)

    def test_permission_denied_subclasses_root(self) -> None:
        """Design spec §30: the one hard-stop policy outcome."""
        assert issubclass(PermissionDeniedError, MineProductivityError)

    def test_all_are_catchable_as_the_platform_root(self) -> None:
        for exc_type in (
            AgentValidationError,
            TaskNotFoundError,
            AgentExecutionError,
            AgentVersionConflictError,
            PolicyConflictError,
            PermissionDeniedError,
        ):
            assert issubclass(exc_type, MineProductivityError)
