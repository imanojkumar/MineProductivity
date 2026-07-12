"""Tests for mineproductivity.visualization.report (design spec §13)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from mineproductivity.core import BaseEntity, BaseValueObject
from mineproductivity.core.serialization import to_dict
from mineproductivity.visualization.renderer import RenderedOutput
from mineproductivity.visualization.report import Report

_WHEN = datetime(2026, 7, 6, tzinfo=timezone.utc)


class TestReport:
    def test_defaults(self) -> None:
        report = Report(report_code="SHIFT.Handover.2026-07-06", generated_at=_WHEN)
        assert report.sections == ()
        assert report.warnings == ()

    def test_sections_are_fully_rendered_outputs(self) -> None:
        """Design spec §13: a Report is the finished document, never
        raw PresentationModels."""
        section = RenderedOutput(format="text", payload="1212.1 t/h")
        report = Report(report_code="SHIFT.Handover", generated_at=_WHEN, sections=(section,))
        assert report.sections[0].format == "text"

    def test_is_a_value_object_not_an_entity(self) -> None:
        """Design spec §13: a produced-once artifact, exactly like
        OptimizationResult/AgentResult."""
        assert issubclass(Report, BaseValueObject)
        assert not issubclass(Report, BaseEntity)

    def test_no_report_repository_exists(self) -> None:
        """Design spec §13, §22: never independently persisted."""
        import mineproductivity.visualization as visualization

        package_dir = Path(visualization.__file__).parent
        source = (package_dir / "persistence.py").read_text(encoding="utf-8")
        assert "ReportRepository" not in source
        assert not hasattr(visualization, "ReportRepository")

    def test_serializes_via_core_serialization(self) -> None:
        serialized = to_dict(Report(report_code="R", generated_at=_WHEN))
        assert serialized["report_code"] == "R"
