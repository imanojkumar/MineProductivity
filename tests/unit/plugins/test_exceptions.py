"""Tests for mineproductivity.plugins.exceptions."""

from __future__ import annotations

import pytest

from mineproductivity.core import MineProductivityError
from mineproductivity.plugins.exceptions import PluginActivationError, PluginDependencyError


class TestExceptionHierarchy:
    def test_plugin_activation_error_is_a_mineproductivity_error(self) -> None:
        assert issubclass(PluginActivationError, MineProductivityError)

    def test_plugin_dependency_error_is_a_plugin_activation_error(self) -> None:
        assert issubclass(PluginDependencyError, PluginActivationError)

    @pytest.mark.parametrize("exc_type", [PluginActivationError, PluginDependencyError])
    def test_catchable_as_root(self, exc_type: type[MineProductivityError]) -> None:
        with pytest.raises(MineProductivityError):
            raise exc_type("boom")

    @pytest.mark.parametrize("exc_type", [PluginActivationError, PluginDependencyError])
    def test_carries_message(self, exc_type: type[MineProductivityError]) -> None:
        err = exc_type("boom")
        assert err.message == "boom"
