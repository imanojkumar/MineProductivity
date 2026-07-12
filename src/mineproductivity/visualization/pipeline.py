"""``RenderingPipeline``: orchestrates one rendering request (design
spec §11) -- the one place in this package where the dispatch decision
is made, exactly once per call, by reading
``widget.visualization_code`` and the caller-supplied
``renderer_code`` directly, never by branching on a concrete Python
type. There is exactly one rendering code path in this package --
live dashboard rendering and export (§18) both flow through
:meth:`RenderingPipeline.render`, never two independently-maintained
paths.
"""

from __future__ import annotations

from mineproductivity.registry import Registry, UnregisteredLookupError

from mineproductivity.visualization.abstractions import Visualization, VisualizationContext
from mineproductivity.visualization.exceptions import DashboardNotFoundError, RenderingError
from mineproductivity.visualization.renderer import RenderedOutput, Renderer
from mineproductivity.visualization.widget import Widget

__all__ = ["RenderingPipeline"]


class RenderingPipeline:
    """Resolves ``widget.visualization_code`` against the composed
    visualization registry, dispatches to the registered
    ``Visualization``'s ``_render``, then resolves ``renderer_code``
    against the composed renderer registry and hands the resulting
    ``PresentationModel`` to that ``Renderer``'s ``render`` (design
    spec §11's sequence diagram). Composes the two registries (§20)
    directly -- no bespoke lookup mechanism of its own. Carries no
    shared mutable state across calls: independent widget renders
    execute fully in parallel (§29)."""

    def __init__(
        self,
        *,
        registry: Registry[str, type[Visualization]],
        renderers: Registry[str, type[Renderer]],
    ) -> None:
        self._registry = registry
        self._renderers = renderers

    def __repr__(self) -> str:
        return f"{type(self).__name__}(registry={self._registry!r}, renderers={self._renderers!r})"

    def render(
        self, widget: Widget, *, context: VisualizationContext, renderer_code: str
    ) -> RenderedOutput:
        """Render ``widget`` end to end. A widget bound to incomplete
        or not-yet-computed evidence flows through as a
        warning-carrying model/output, never a raise (design spec
        §30).

        Raises
        ------
        DashboardNotFoundError
            If no ``Visualization`` is registered for
            ``widget.visualization_code``, or no ``Renderer`` for
            ``renderer_code``.
        RenderingError
            If the dispatched ``_render``/``render`` raised for a
            structurally valid input (design spec §30).
        """
        try:
            visualization_cls = self._registry.get(widget.visualization_code)
        except UnregisteredLookupError as exc:
            raise DashboardNotFoundError(
                f"No Visualization is registered for code {widget.visualization_code!r}"
            ) from exc
        try:
            renderer_cls = self._renderers.get(renderer_code)
        except UnregisteredLookupError as exc:
            raise DashboardNotFoundError(
                f"No Renderer is registered for code {renderer_code!r}"
            ) from exc

        visualization = visualization_cls()
        renderer = renderer_cls()
        try:
            model = visualization._render(widget, context=context)
            return renderer.render(model, context=context)
        except Exception as exc:
            raise RenderingError(
                f"Rendering widget {widget.code!r} via "
                f"{widget.visualization_code!r}/{renderer_code!r} raised for a "
                f"structurally valid input: {exc}"
            ) from exc
