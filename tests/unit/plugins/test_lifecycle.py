"""Tests for mineproductivity.plugins.lifecycle."""

from __future__ import annotations

from collections.abc import Sequence

import pytest

from mineproductivity.core import NotFoundError, Result
from mineproductivity.plugins.exceptions import PluginActivationError, PluginDependencyError
from mineproductivity.plugins.lifecycle import PluginLifecycle, PluginState, _DefaultPluginLifecycle
from mineproductivity.plugins.loader import PluginLoader
from mineproductivity.plugins.manifest import PluginDependency, PluginManifest
from mineproductivity.registry import EntryPointDiscovery, EntryPointSpec, VersionRange

_COMPATIBLE_RANGE = VersionRange(min_version="0.0.0", max_version_exclusive="99.0.0")
_INCOMPATIBLE_RANGE = VersionRange(min_version="10.0.0", max_version_exclusive="11.0.0")


class _StubDiscovery(EntryPointDiscovery):
    def __init__(self, ok: bool = True) -> None:
        self._ok = ok

    def discover(self, spec: EntryPointSpec) -> Result[Sequence[str]]:
        if self._ok:
            return Result.ok(("dummy",))
        return Result.err("boom")


def make_manifest(
    name: str,
    *,
    core_range: VersionRange = _COMPATIBLE_RANGE,
    depends_on: tuple[PluginDependency, ...] = (),
) -> PluginManifest:
    return PluginManifest(
        plugin_name=name,
        plugin_version="1.0.0",
        core_version_range=core_range,
        provides=(EntryPointSpec(group="g", target_registry="t"),),
        depends_on=depends_on,
    )


class TestPluginState:
    def test_has_five_states(self) -> None:
        assert len(list(PluginState)) == 5

    def test_values(self) -> None:
        assert PluginState.DISCOVERED.value == "discovered"
        assert PluginState.VALIDATED.value == "validated"
        assert PluginState.ACTIVE.value == "active"
        assert PluginState.FAILED.value == "failed"
        assert PluginState.DEACTIVATED.value == "deactivated"


class TestPluginLifecycleAbstractContract:
    def test_cannot_instantiate_abstract_base(self) -> None:
        with pytest.raises(TypeError):
            PluginLifecycle()  # type: ignore[abstract]


class TestDefaultPluginLifecycleActivate:
    def test_successful_activation_reaches_active(self) -> None:
        lifecycle = _DefaultPluginLifecycle(
            core_version="0.5.0", loader=PluginLoader(discovery=_StubDiscovery())
        )
        result = lifecycle.activate(make_manifest("p1"))
        assert result.is_ok
        assert lifecycle.state_of("p1") is PluginState.ACTIVE

    def test_version_incompatible_reaches_failed(self) -> None:
        lifecycle = _DefaultPluginLifecycle(
            core_version="0.5.0", loader=PluginLoader(discovery=_StubDiscovery())
        )
        result = lifecycle.activate(make_manifest("p1", core_range=_INCOMPATIBLE_RANGE))
        assert result.is_err
        assert lifecycle.state_of("p1") is PluginState.FAILED

    def test_load_failure_reaches_failed(self) -> None:
        lifecycle = _DefaultPluginLifecycle(
            core_version="0.5.0", loader=PluginLoader(discovery=_StubDiscovery(ok=False))
        )
        result = lifecycle.activate(make_manifest("p1"))
        assert result.is_err
        assert isinstance(result.error, PluginActivationError)
        assert lifecycle.state_of("p1") is PluginState.FAILED

    def test_unmet_dependency_reaches_failed(self) -> None:
        lifecycle = _DefaultPluginLifecycle(
            core_version="0.5.0", loader=PluginLoader(discovery=_StubDiscovery())
        )
        dep = PluginDependency(plugin_name="missing-base", version_range=_COMPATIBLE_RANGE)
        result = lifecycle.activate(make_manifest("dependent", depends_on=(dep,)))
        assert result.is_err
        assert isinstance(result.error, PluginDependencyError)
        assert lifecycle.state_of("dependent") is PluginState.FAILED

    def test_dependency_active_first_allows_dependent_to_activate(self) -> None:
        lifecycle = _DefaultPluginLifecycle(
            core_version="0.5.0", loader=PluginLoader(discovery=_StubDiscovery())
        )
        lifecycle.activate(make_manifest("base"))
        dep = PluginDependency(plugin_name="base", version_range=_COMPATIBLE_RANGE)
        result = lifecycle.activate(make_manifest("dependent", depends_on=(dep,)))
        assert result.is_ok
        assert lifecycle.state_of("dependent") is PluginState.ACTIVE


class TestDefaultPluginLifecycleDeactivate:
    def test_deactivate_active_plugin(self) -> None:
        lifecycle = _DefaultPluginLifecycle(
            core_version="0.5.0", loader=PluginLoader(discovery=_StubDiscovery())
        )
        lifecycle.activate(make_manifest("p1"))
        result = lifecycle.deactivate("p1")
        assert result.is_ok
        assert lifecycle.state_of("p1") is PluginState.DEACTIVATED

    def test_deactivate_unknown_plugin_errs(self) -> None:
        lifecycle = _DefaultPluginLifecycle(core_version="0.5.0")
        result = lifecycle.deactivate("never-activated")
        assert result.is_err
        assert isinstance(result.error, PluginActivationError)


class TestDefaultPluginLifecycleStateOf:
    def test_state_of_unknown_plugin_raises(self) -> None:
        lifecycle = _DefaultPluginLifecycle(core_version="0.5.0")
        with pytest.raises(NotFoundError):
            lifecycle.state_of("never-seen")


class TestIsolation:
    def test_one_failing_plugin_does_not_block_another(self) -> None:
        """The isolation rule (design spec §11, §26): a plugin reaching
        Failed must never prevent another plugin from reaching Active."""
        lifecycle = _DefaultPluginLifecycle(
            core_version="0.5.0", loader=PluginLoader(discovery=_StubDiscovery())
        )

        broken_result = lifecycle.activate(make_manifest("broken", core_range=_INCOMPATIBLE_RANGE))
        healthy_result = lifecycle.activate(make_manifest("healthy"))

        assert broken_result.is_err
        assert healthy_result.is_ok
        assert lifecycle.state_of("broken") is PluginState.FAILED
        assert lifecycle.state_of("healthy") is PluginState.ACTIVE

    def test_activation_order_does_not_matter_for_isolation(self) -> None:
        lifecycle = _DefaultPluginLifecycle(
            core_version="0.5.0", loader=PluginLoader(discovery=_StubDiscovery())
        )

        lifecycle.activate(make_manifest("healthy"))
        lifecycle.activate(make_manifest("broken", core_range=_INCOMPATIBLE_RANGE))

        assert lifecycle.state_of("healthy") is PluginState.ACTIVE
        assert lifecycle.state_of("broken") is PluginState.FAILED
