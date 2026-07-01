"""Tests for mineproductivity.core.configuration."""

from __future__ import annotations

import dataclasses

import pytest

from mineproductivity.core.configuration import BaseConfiguration
from mineproductivity.core.exceptions import ConfigurationError


@dataclasses.dataclass(frozen=True, slots=True)
class RetrySettings(BaseConfiguration):
    max_attempts: int = 3
    backoff_seconds: float = 1.0


class TestFromMapping:
    def test_builds_instance_from_full_mapping(self) -> None:
        config = RetrySettings.from_mapping({"max_attempts": 5, "backoff_seconds": 2.0})
        assert config.max_attempts == 5
        assert config.backoff_seconds == 2.0

    def test_builds_instance_from_partial_mapping_using_defaults(self) -> None:
        config = RetrySettings.from_mapping({"max_attempts": 5})
        assert config.max_attempts == 5
        assert config.backoff_seconds == 1.0

    def test_empty_mapping_uses_all_defaults(self) -> None:
        config = RetrySettings.from_mapping({})
        assert config == RetrySettings()

    def test_unknown_field_raises_configuration_error(self) -> None:
        with pytest.raises(ConfigurationError):
            RetrySettings.from_mapping({"bogus_field": 1})


class TestToMapping:
    def test_round_trips_via_mapping(self) -> None:
        config = RetrySettings(max_attempts=7, backoff_seconds=0.5)
        mapping = config.to_mapping()
        assert mapping == {"max_attempts": 7, "backoff_seconds": 0.5}
        assert RetrySettings.from_mapping(mapping) == config


class TestImmutability:
    def test_configuration_is_frozen(self) -> None:
        config = RetrySettings()
        with pytest.raises(dataclasses.FrozenInstanceError):
            config.max_attempts = 10  # type: ignore[misc]
