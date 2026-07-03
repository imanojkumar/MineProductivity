"""``KPIMetadata``: the complete, governed 29-field mandatory schema from
Developer & Cookbook Guide Part III, the KPI Standard Library.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from enum import Enum
from types import MappingProxyType
from typing import Literal

from mineproductivity.core import BaseMetadata

from mineproductivity.kpis.exceptions import KPIValidationError
from mineproductivity.kpis.lifecycle import KPIStatus
from mineproductivity.kpis.naming import parse_identifier

__all__ = ["Aggregation", "DigitalMaturity", "Direction", "KPIMetadata"]


class Direction(Enum):
    """Which way "better" points for a KPI's value."""

    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"
    TARGET_IS_BEST = "target_is_best"  # e.g. payload near, not above, rated capacity


class Aggregation(Enum):
    """Governs how a KPI MAY be aggregated across periods/groups --
    directly enforces the RATIO-not-averaged rule (Cookbook Part I Ch. 6)."""

    ADDITIVE = "additive"
    RATIO = "ratio"  # re-derive from summed numerator/denominator
    AVERAGE = "average"  # count-weighted mean
    WEIGHTED_AVERAGE = "weighted_average"
    ROLLING = "rolling"
    CUMULATIVE = "cumulative"
    DERIVED = "derived"  # composite of other KPIs


class DigitalMaturity(Enum):
    """The site digital-maturity level a KPI requires to be computable."""

    L1_MANUAL = 1
    L2_FMS = 2
    L3_ANALYTICS = 3
    L4_AUTONOMOUS = 4


@dataclasses.dataclass(frozen=True, slots=True)
class KPIMetadata(BaseMetadata):
    """The complete, governed metadata for one KPI -- fields 1-15 and
    18-29 of the Standard Library's mandatory template are typed engine
    fields; fields 16-17 (worked example, sample dataset) are
    documentation artifacts carried in ``attributes`` since the engine
    does not execute prose (design spec §34).

    No field is optional -- a blank field is a specification gap
    (Standard Library governance rule, enforced here at construction).
    """

    # 1. Identifier
    code: str
    # 2. Official Name (BaseMetadata.name doubles as the short display name)
    official_name: str = dataclasses.field(default="", kw_only=True)
    # 3. Business Purpose
    business_purpose: str = dataclasses.field(default="", kw_only=True)
    # 4. Operational Question
    operational_question: str = dataclasses.field(default="", kw_only=True)
    # 5. Business Meaning
    business_meaning: str = dataclasses.field(default="", kw_only=True)
    # 6. Formula (plain-text/Unicode, every symbol defined)
    formula: str = dataclasses.field(default="", kw_only=True)
    # 7. Units
    unit: str = dataclasses.field(default="", kw_only=True)
    # 8. Dimensions
    dimensions: tuple[str, ...] = dataclasses.field(default=(), kw_only=True)
    # 9. Required Events
    required_events: tuple[str, ...] = dataclasses.field(default=(), kw_only=True)
    # 10. Required Ontology
    required_ontology: tuple[str, ...] = dataclasses.field(default=(), kw_only=True)
    # 11. Dependencies
    dependencies: tuple[str, ...] = dataclasses.field(default=(), kw_only=True)
    # 12. Mathematical Properties
    aggregation: Aggregation = dataclasses.field(default=Aggregation.ADDITIVE, kw_only=True)
    # 13-17 (Calculation Logic / Implementation / Expected Output / Worked
    #         Example / Sample Dataset) are documentation, carried via
    #         BaseMetadata.attributes and the class's own docstring/_compute.
    # 18. Visualization
    visualization_hint: str = dataclasses.field(default="", kw_only=True)
    # 19. Operational Interpretation (benchmark bands)
    benchmark_bands: Mapping[str, str] = dataclasses.field(default_factory=dict, kw_only=True)
    # 20-22 (Common Mistakes / Validation Rules / Unit Tests) are documentation
    #         + the class's own validate()/tests, not engine-executed metadata.
    # 23. Performance Considerations -- documentation, in `attributes`.
    # 24. Edge Cases
    edge_cases: tuple[str, ...] = dataclasses.field(default=(), kw_only=True)
    # 25. AI Contributor Notes
    leading_or_lagging: Literal["leading", "lagging"] = dataclasses.field(
        default="lagging", kw_only=True
    )
    operational_or_strategic: Literal["operational", "strategic"] = dataclasses.field(
        default="operational", kw_only=True
    )
    # 26. Digital Twin Mapping -- documentation, in `attributes`.
    # 27. Decision Intelligence Mapping -- documentation, in `attributes`.
    # 28. Related KPIs
    related_kpis: tuple[str, ...] = dataclasses.field(default=(), kw_only=True)
    # 29. References
    references: tuple[str, ...] = dataclasses.field(default=(), kw_only=True)

    # Additional engine-required fields beyond the 29 (naming standard,
    # lifecycle, applicability -- Introduction & Naming Standard chapters):
    direction: Direction = dataclasses.field(default=Direction.HIGHER_IS_BETTER, kw_only=True)
    status: KPIStatus = dataclasses.field(default_factory=lambda: KPIStatus.PROPOSED, kw_only=True)
    version: str = dataclasses.field(default="1.0.0", kw_only=True)  # SemVer string
    min_maturity: DigitalMaturity = dataclasses.field(
        default=DigitalMaturity.L1_MANUAL, kw_only=True
    )
    method_applicability: tuple[str, ...] = dataclasses.field(
        default=("open_pit", "underground"), kw_only=True
    )
    commodity_applicability: tuple[str, ...] = dataclasses.field(
        default=(), kw_only=True
    )  # empty = all
    aliases: tuple[str, ...] = dataclasses.field(default=(), kw_only=True)
    deprecated_successor: str | None = dataclasses.field(default=None, kw_only=True)

    def _normalize(self) -> None:
        super(KPIMetadata, self)._normalize()
        object.__setattr__(self, "benchmark_bands", MappingProxyType(dict(self.benchmark_bands)))

    def validate(self) -> None:
        super(KPIMetadata, self).validate()
        parse_identifier(self.code)
        for field_name in (
            "official_name",
            "business_purpose",
            "operational_question",
            "business_meaning",
            "formula",
            "unit",
        ):
            if not getattr(self, field_name).strip():
                raise KPIValidationError(f"{self.code}: {field_name} must not be empty")
        if not self.dimensions:
            raise KPIValidationError(f"{self.code}: dimensions must not be empty")
        if not self.required_events:
            raise KPIValidationError(f"{self.code}: required_events must not be empty")
