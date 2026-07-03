"""Tests for mineproductivity.registry.version_compat."""

from __future__ import annotations

import pytest

from mineproductivity.core import ValidationError
from mineproductivity.registry.exceptions import VersionIncompatibleError
from mineproductivity.registry.version_compat import VersionCompatibility, VersionRange


class TestVersionRange:
    def test_valid_construction(self) -> None:
        vr = VersionRange(min_version="1.0.0", max_version_exclusive="2.0.0")
        assert vr.min_version == "1.0.0"
        assert vr.max_version_exclusive == "2.0.0"

    def test_empty_min_version_rejected(self) -> None:
        with pytest.raises(ValidationError):
            VersionRange(min_version="", max_version_exclusive="2.0.0")

    def test_empty_max_version_rejected(self) -> None:
        with pytest.raises(ValidationError):
            VersionRange(min_version="1.0.0", max_version_exclusive="")

    def test_inverted_range_rejected(self) -> None:
        with pytest.raises(ValidationError):
            VersionRange(min_version="2.0.0", max_version_exclusive="1.0.0")

    def test_equal_bounds_rejected(self) -> None:
        with pytest.raises(ValidationError):
            VersionRange(min_version="1.0.0", max_version_exclusive="1.0.0")


class TestIsCompatible:
    @pytest.mark.parametrize(
        ("core_version", "expected"),
        [
            ("0.9.0", False),
            ("1.0.0", True),  # inclusive lower bound
            ("1.5.0", True),
            ("1.9.9", True),
            ("2.0.0", False),  # exclusive upper bound
            ("2.1.0", False),
        ],
    )
    def test_boundary_cases(self, core_version: str, expected: bool) -> None:
        vr = VersionRange(min_version="1.0.0", max_version_exclusive="2.0.0")
        assert VersionCompatibility.is_compatible(vr, core_version) is expected

    def test_minor_version_precision(self) -> None:
        vr = VersionRange(min_version="1.2.0", max_version_exclusive="1.3.0")
        assert VersionCompatibility.is_compatible(vr, "1.2.5") is True
        assert VersionCompatibility.is_compatible(vr, "1.3.0") is False

    def test_pre_release_suffix_is_ignored(self) -> None:
        vr = VersionRange(min_version="1.0.0", max_version_exclusive="2.0.0")
        assert VersionCompatibility.is_compatible(vr, "1.0.0rc1") is True


class TestCheckOrRaise:
    def test_compatible_does_not_raise(self) -> None:
        vr = VersionRange(min_version="1.0.0", max_version_exclusive="2.0.0")
        VersionCompatibility.check_or_raise(vr, "1.5.0")

    def test_incompatible_raises(self) -> None:
        vr = VersionRange(min_version="1.0.0", max_version_exclusive="2.0.0")
        with pytest.raises(VersionIncompatibleError):
            VersionCompatibility.check_or_raise(vr, "3.0.0")
