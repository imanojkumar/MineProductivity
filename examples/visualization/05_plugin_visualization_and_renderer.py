"""A third-party-style ``Visualization`` and ``Renderer`` registered
via entry points into the package's two orthogonal registries (spec 12
§22, §31):

    [project.entry-points."mineproductivity.visualization"]
    sitepack = "mineproductivity_sitepack.visualization"
    [project.entry-points."mineproductivity.visualization.renderers"]
    sitepack = "mineproductivity_sitepack.renderers"

``REGISTRY`` holds visualization *types*; ``RENDERERS`` holds renderer
*types* — never merged. A charting library, templating engine, or
document-generation library lives only in the plugin's renderer, never
in this repository (mechanically enforced).

Run: python examples/visualization/05_plugin_visualization_and_renderer.py
"""

from __future__ import annotations

import importlib.metadata
import sys
import tempfile
from pathlib import Path

from mineproductivity.kpis import KPIResult
from mineproductivity.registry import EntryPointDiscovery, EntryPointSpec
from mineproductivity.visualization import (
    REGISTRY,
    RENDERERS,
    RendererMetadata,
    RenderingPipeline,
    VisualizationContext,
    VisualizationMetadata,
    Widget,
)

_PLUGIN_SOURCE = '''\
"""A site pack's own visualization and renderer -- importing this
module registers both, exactly as a pip-installed plugin's entry-point
scan would."""

from mineproductivity.visualization import (
    PresentationModel,
    RenderedOutput,
    Renderer,
    RendererMetadata,
    Visualization,
    VisualizationCategory,
    VisualizationContext,
    VisualizationMetadata,
    Widget,
    register,
    register_renderer,
)


@register
class SitePackGaugeCard(Visualization):
    """A site pack's gauge-style KPI card."""

    meta = VisualizationMetadata(
        code="KPI_CARD.SitePackGauge",
        category=VisualizationCategory.KPI_CARD,
        description="A site pack's gauge-style KPI card.",
    )

    def _render(self, widget, *, context):
        wanted = widget.binding.get("kpi_code", "")
        matched = [r for r in context.kpi_results if r.code == wanted]
        if not matched:
            return PresentationModel(
                category=type(self).meta.category, title=wanted, warnings=("no evidence",)
            )
        return PresentationModel(
            category=type(self).meta.category,
            title=wanted,
            series={"value": matched[0].value},
            evidence_refs=(wanted,),
        )


@register_renderer
class SitePackSvgRenderer(Renderer):
    """A site pack's SVG renderer -- a real one would import a charting
    library here; this one emits a tiny inline SVG string."""

    meta = RendererMetadata(code="SVG.SitePack", description="Renders a model to inline SVG.")

    def render(self, model, *, context):
        value = model.series.get("value", 0.0)
        return RenderedOutput(
            format="svg",
            payload=f"<svg><text>{model.title}: {value}</text></svg>",
            warnings=model.warnings,
        )
'''


def main() -> None:
    print("--- 1. visualization ships zero concrete views or renderers ---")
    print(f"site-pack views before:     {sorted(c for c in REGISTRY if 'SitePack' in c)}")
    print(f"site-pack renderers before: {sorted(c for c in RENDERERS if 'SitePack' in c)}")

    print()
    print("--- 2. A site pack declares both via pyproject.toml entry-points ---")
    with tempfile.TemporaryDirectory() as tmp_dir:
        plugin_path = Path(tmp_dir) / "_example_sitepack_visualization.py"
        plugin_path.write_text(_PLUGIN_SOURCE, encoding="utf-8")
        sys.path.insert(0, tmp_dir)
        try:
            real_entry_points = importlib.metadata.entry_points

            def _fake_entry_points(*, group: str):  # type: ignore[no-untyped-def]
                if group in (
                    "mineproductivity.visualization",
                    "mineproductivity.visualization.renderers",
                ):
                    return (
                        importlib.metadata.EntryPoint(
                            name="sitepack", value="_example_sitepack_visualization", group=group
                        ),
                    )
                return real_entry_points(group=group)

            importlib.metadata.entry_points = _fake_entry_points  # type: ignore[assignment]
            try:
                discovery = EntryPointDiscovery()
                views = discovery.discover(
                    EntryPointSpec(
                        group="mineproductivity.visualization", target_registry="visualization"
                    )
                )
                renderers = discovery.discover(
                    EntryPointSpec(
                        group="mineproductivity.visualization.renderers",
                        target_registry="visualization.renderers",
                    )
                )
            finally:
                importlib.metadata.entry_points = real_entry_points
        finally:
            sys.path.remove(tmp_dir)
            sys.modules.pop("_example_sitepack_visualization", None)

    print(f"views     discover() is_ok: {views.is_ok} loaded: {views.value}")
    print(f"renderers discover() is_ok: {renderers.is_ok} loaded: {renderers.value}")
    view_meta = REGISTRY.metadata_for("KPI_CARD.SitePackGauge").unwrap()
    renderer_meta = RENDERERS.metadata_for("SVG.SitePack").unwrap()
    assert isinstance(view_meta, VisualizationMetadata)
    assert isinstance(renderer_meta, RendererMetadata)
    print(f"registered view: {view_meta.code}; registered renderer: {renderer_meta.code}")

    print()
    print("--- 3. The discovered plugin renders like any built-in would ---")
    pipeline = RenderingPipeline(registry=REGISTRY, renderers=RENDERERS)
    output = pipeline.render(
        Widget(
            code="gauge",
            visualization_code="KPI_CARD.SitePackGauge",
            binding={"kpi_code": "PROD.TPH"},
        ),
        context=VisualizationContext(
            kpi_results=(KPIResult(code="PROD.TPH", value=1212.1, unit="t/h"),)
        ),
        renderer_code="SVG.SitePack",
    )
    print(f"format={output.format!r} payload={output.payload!r}")


if __name__ == "__main__":
    main()
