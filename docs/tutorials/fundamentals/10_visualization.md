# Lesson 10 - Visualization

## Objective

Present a governed fact to a human - and understand the two design choices that let one model render to a terminal, an SVG dashboard, or a PDF without the platform ever depending on a charting library.

This is the final Fundamentals lesson. It closes the chain.

## Prerequisites

- [Lesson 06 - KPIs](06_kpis.md) (the governed evidence being presented)
- Ideally all of 01–09; this lesson ties them together.

## Concepts covered

| Concept | Why it exists |
|---|---|
| `Visualization` (interface-only) | Produces a `PresentationModel` from a `Widget` + evidence. **Zero** ship. |
| `PresentationModel` | Structure, **not bytes**. No pixels, no colours, no fonts. |
| `Renderer` (interface-only) | Turns a model into a `RenderedOutput`. **Zero** ship. |
| `RenderingPipeline` | The one code path: visualization → model → renderer. |
| Qualify, don't coerce | Missing evidence → warning, never a fabricated `0.0`. |

## Complete runnable example

**[:material-file-code: `examples/fundamentals/10_visualization/visualization.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/fundamentals/10_visualization/visualization.py)**

```bash
python examples/fundamentals/10_visualization/visualization.py
```

Note the missing-evidence branch - it returns a *real model carrying a warning*, not an exception and not a zero:

```python
def _render(self, widget: Widget, *, context: VisualizationContext) -> PresentationModel:
    wanted = widget.binding.get("kpi_code", "")
    matched = [result for result in context.kpi_results if result.code == wanted]
    if not matched:
        return PresentationModel(
            category=type(self).meta.category,
            title=wanted or widget.code,
            warnings=(f"no KPIResult for {wanted!r} in context",),
        )
    result = matched[0]
    return PresentationModel(
        category=type(self).meta.category,
        title=wanted,
        series={"value": result.value, "unit": result.unit},
        evidence_refs=(wanted,),
    )
```

## Expected output

```text
--- 1. The evidence was governed by the layers below ---
context carries a PROD.TPH KPIResult of 1,150.0 t/h
(visualization did not compute it and could not -- it has no idea
 what a tonne or an operating hour is)

--- 2. A Widget binds a visualization type to the evidence it wants ---
widget 'tph_card' -> 'KPI_CARD.ShiftHandover' binding={'kpi_code': 'PROD.TPH'}

--- 3. One pipeline: visualization -> PresentationModel -> renderer ---
format : 'text'
payload: 'PROD.TPH: 1,150.0 t/h'

--- 4. The intermediate model carries structure, not pixels ---
category=kpi_card | title='PROD.TPH' | series={'value': 1150.0, 'unit': 't/h'} | evidence_refs=('PROD.TPH',)
(no bytes, no colours, no fonts. That is why the SAME model can go
 to a terminal, an SVG dashboard, or an exported PDF unchanged --
 two renderers above, one unchanged visualization.)

--- 5. Qualify, don't coerce: missing evidence is a warning ---
payload : 'PROD.TPH: UNAVAILABLE'
warnings: ("no KPIResult for 'PROD.TPH' in context",)
(a control room that silently shows 0.0 t/h when the feed dies is
 dangerous. The platform says UNAVAILABLE and tells you why.)

--- 6. Everything above was example-local, by design ---
visualization ships ZERO concrete Visualizations and ZERO Renderers.
Both classes in this file are yours. A charting/templating library
would be imported in a plugin -- the locked package imports none,
and a test enforces that (ADR-0012).

--- The chain, end to end ---
  events      -> the immutable facts        (lesson 04)
  ontology    -> what those facts are about (lesson 05)
  kpis        -> the governed measurement   (lesson 06)
  analytics   -> is it drifting?            (lesson 07)
  decision    -> what should we do, and why (lesson 08)
  digital_twin-> what is true right now     (lesson 09)
  visualization-> show a human              (this lesson)
Each layer consumed the one below and re-derived nothing. That
discipline is the whole architecture, and now you can read it.
```

## Explanation

### The package does no business computation - and cannot

`visualization` does not know what a tonne is. It cannot compute `PROD.TPH`; it has no access to the formula and no idea what an operating hour means. It takes evidence the lower layers already governed and arranges it for a human.

That sounds like a limitation. It is the reason the layer is safe: a dashboard can never disagree with the KPI engine, because a dashboard cannot do arithmetic.

### `PresentationModel` carries no bytes

Section 4 is the design choice worth internalising. The model says *"this is a KPI card titled PROD.TPH with value 1150 and unit t/h, sourced from evidence PROD.TPH"*. It does **not** say "here is a 400×200 PNG".

Because of that, the same model renders unchanged to a control-room terminal, an SVG dashboard, or an exported PDF - and the locked package never imports matplotlib, or Jinja, or a PDF library. The backend lives in a plugin. A test enforces that no charting/templating library string appears in the package at all (ADR-0012).

### Qualify, don't coerce - the safety rule

Section 5 is not a nicety. **A control room that silently shows `0.0 t/h` when the data feed dies is dangerous.** An operator sees zero and reasonably concludes the fleet has stopped. They may act on that.

So when evidence is missing, the visualization returns a *real model* carrying a `warning`, and the renderer prints `UNAVAILABLE`. Not an exception (which would blank the whole dashboard over one dead widget), and not a fabricated zero (which lies). This is the same philosophy as `EventValidator` scoring confidence in Lesson 04 rather than discarding suspect data.

### Everything in this lesson is yours

`ShiftKpiCard` and `ControlRoomTextRenderer` are **example-local**. The package ships zero concrete visualizations and zero renderers, exactly as `analytics` ships no forecaster (Lesson 07) and `decision` ships no root-cause engine (Lesson 08). The pattern is consistent: the platform defines contracts and refuses to make your modelling and backend decisions for you.

### The chain, end to end

That final block is the Fundamentals suite in seven lines. Each layer consumed the one below and **re-derived nothing**:

- Events are the immutable facts.
- Ontology says what the facts are about.
- KPIs measure, once, with one governed definition.
- Analytics characterises, without recomputing.
- Decision recommends, with an explanation and an audit trail.
- Digital Twin projects the present, from the log.
- Visualization shows a human, without computing anything.

That discipline *is* the architecture. You can now read it.

## Best practices

- **Never compute in a visualization.** If you find yourself dividing, you are in the wrong layer.
- **Return a warning-carrying model for missing evidence** - never `0.0`, never an exception.
- **Keep `PresentationModel` backend-free.** No colours, no dimensions, no bytes.
- **Import charting libraries only in a plugin renderer.**
- **Set `evidence_refs`** so a viewer can trace a card back to its governed source.

## Common mistakes

| Mistake | What happens | Do this instead |
|---|---|---|
| **Defaulting missing data to `0.0`** | The control room reads "fleet stopped". Genuinely dangerous. | Warning + `UNAVAILABLE` |
| Computing a KPI in a widget | The dashboard disagrees with the KPI engine, and both are "right" | Consume `context.kpi_results` |
| Putting colours/sizes in `PresentationModel` | Couples the model to one backend; the PDF path breaks | Keep it structural |
| Importing matplotlib in the package | Violates ADR-0012; a test fails | Import it in your plugin |
| Raising on missing evidence | One dead feed blanks the entire dashboard | Qualify, don't coerce |
| Omitting `evidence_refs` | A number on a screen with no provenance | Set them |

## Exercises

1. **Add a renderer.** Write an `SvgRenderer` producing `<svg><text>...</text></svg>` from the *same* `PresentationModel`. Note you did not touch the visualization - why is that the point?
2. **Kill the feed.** Render with an empty `VisualizationContext`. What does an operator see? Compare that to a dashboard that shows `0.0`. Which would you rather have at 3 a.m.?
3. **Present the trend.** Build a widget that shows Lesson 07's `TrendResult` - remembering to convert the slope to t/h per shift.
4. **Build a handover dashboard.** Use `DashboardBuilder` to combine a KPI card, a trend card, and an agent note ([`examples/visualization/02_multi_source_dashboard.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/visualization/02_multi_source_dashboard.py) shows the pattern).
5. **Reflect.** `analytics` ships no forecaster, `decision` no root-cause engine, `visualization` no renderer. Write down the single principle behind all three refusals.

## Suggested next lesson

**You have finished the Fundamentals milestone.** 🎉

You can now model a mine, measure it, characterise it, decide on it, project its live state, and present it - and you know which decisions the platform deliberately leaves to you.

Where to go next:

- **[Tutorials index](../index.md)** - the per-package walkthroughs go deeper on each layer, including `simulation`, `optimization`, and `agents`, which Fundamentals did not cover.
- **[Packages](../../packages/index.md)** - the full public API and extension guide for every package.
- **[Architecture Handbook](../../architecture/README.md)** - the twelve locked design specifications, and the ADRs explaining *why*.
- **Write a plugin.** Every refusal you met is an extension point waiting for you.

---

**See also:** [`visualization` API Reference](../../api-reference/visualization.md) · [`visualization` package guide](../../packages/visualization.md) · [Visualization design specification](../../architecture/12_Visualization_Design_Specification.md) · [ADR-0012](../../adr/ADR-0012-Visualization.md)
