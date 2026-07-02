"""Tests for mineproductivity.events.versioning."""

from __future__ import annotations

from mineproductivity.events.versioning import EventVersion


class TestEventVersion:
    def test_default_version_is_one(self) -> None:
        assert EventVersion().version == 1

    def test_next_version_increments(self) -> None:
        assert EventVersion().next_version().version == 2

    def test_next_version_does_not_mutate_original(self) -> None:
        original = EventVersion()
        original.next_version()
        assert original.version == 1

    def test_equal_versions_are_equal(self) -> None:
        assert EventVersion(version=2) == EventVersion(version=2)

    def test_different_versions_are_not_equal(self) -> None:
        assert EventVersion(version=1) != EventVersion(version=2)
