"""Tests for mineproductivity.digital_twin.lifecycle.

The transition behavior itself (Provisioned -> Synchronized on first
successful sync, Degraded on repeated ``_apply`` failures, recovery,
and ``Retired``'s terminality) is proven in
``test_synchronization.py``'s lifecycle-transition tests, where the one
component that drives transitions lives.
"""

from __future__ import annotations

from mineproductivity.digital_twin.lifecycle import TwinStatus


class TestTwinStatus:
    def test_exactly_the_five_members_of_design_spec_10(self) -> None:
        assert {member.value for member in TwinStatus} == {
            "provisioned",
            "synchronized",
            "stale",
            "degraded",
            "retired",
        }

    def test_members_are_distinct(self) -> None:
        assert len(TwinStatus) == 5
