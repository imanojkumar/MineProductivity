"""A ``SIMULATION_PLAYBACK`` view (design spec §17, §26): one of the
four domain-specific visualization categories, presenting a sequence of
``simulation.SimulationResult`` frames as a played-back series.
``visualization`` reads the already-computed simulation outcomes; it
never runs a simulation itself (spec 12 §3.2) - the frames are handed
in on the ``VisualizationContext``.

The concrete visualization and renderer are example-local.

Run: python examples/visualization/04_simulation_playback.py
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from mineproductivity.simulation import SimulationResult, SimulationState
from mineproductivity.visualization import (
    REGISTRY,
    RENDERERS,
    PresentationModel,
    RenderedOutput,
    Renderer,
    RendererMetadata,
    RenderingPipeline,
    Visualization,
    VisualizationCategory,
    VisualizationContext,
    VisualizationMetadata,
    Widget,
    register,
    register_renderer,
)

START = datetime(2026, 7, 12, 6, 0, tzinfo=timezone.utc)


@register
class ThroughputPlayback(Visualization):
    """Presents simulation frames as a throughput timeline (example-local)."""

    meta = VisualizationMetadata(
        code="SIMULATION_PLAYBACK.Throughput",
        category=VisualizationCategory.SIMULATION_PLAYBACK,
        description="Plays back a simulation's throughput frames over time.",
    )

    def _render(self, widget: Widget, *, context: VisualizationContext) -> PresentationModel:
        frames: tuple[tuple[str, float], ...] = ()
        for result in context.simulation_results:
            if result.final_state is None:
                continue
            when = result.final_state.simulated_time.strftime("%H:%M")
            tph = float(result.final_state.attributes.get("tonnes_per_hour", 0.0))
            frames += ((when, tph),)
        if not frames:
            return PresentationModel(
                category=type(self).meta.category,
                title=widget.code,
                warnings=("no simulation frames in context",),
            )
        return PresentationModel(
            category=type(self).meta.category,
            title="Night-shift throughput playback",
            series={"frames": frames},
        )


@register_renderer
class TimelineTextRenderer(Renderer):
    meta = RendererMetadata(code="TEXT.Timeline", description="Renders frames as a text timeline.")

    def render(self, model: PresentationModel, *, context: VisualizationContext) -> RenderedOutput:
        frames = model.series.get("frames", ())
        body = " | ".join(f"{when} {tph:.0f}t/h" for when, tph in frames)
        return RenderedOutput(
            format="text", payload=f"{model.title}: {body}", warnings=model.warnings
        )


def main() -> None:
    print("--- 1. Simulation frames were already computed elsewhere ---")
    frames = [
        SimulationResult(
            final_state=SimulationState(
                attributes={"tonnes_per_hour": 4200.0 + step * 120.0},
                simulated_time=START + timedelta(hours=step),
            )
        )
        for step in range(6)
    ]
    print(f"{len(frames)} frames handed to the visualization context")

    print()
    print("--- 2. Render the playback view through the pipeline ---")
    pipeline = RenderingPipeline(registry=REGISTRY, renderers=RENDERERS)
    output = pipeline.render(
        Widget(code="playback", visualization_code="SIMULATION_PLAYBACK.Throughput"),
        context=VisualizationContext(simulation_results=frames),
        renderer_code="TEXT.Timeline",
    )
    print(output.payload)


if __name__ == "__main__":
    main()
