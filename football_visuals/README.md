# football_visuals

The project's shared visual language — one design system across **still** figures and **motion**.

Where [`football_metrics`](../football_metrics) measures and [`football_forecasts`](../football_forecasts)
predicts, this module decides how any of it *looks*.

| Piece | What |
|---|---|
| [`kick_style.py`](./kick_style.py) | The house **matplotlib** design system: palette by job, Inter/Chakra type scale, dark pitch treatment, layout + legend + colourbar helpers. Imported by every metric notebook so no figure drifts from the standard. |
| [`style_guide.ipynb`](./style_guide.ipynb) | Renders one example of each chart family — the visual contract in runnable form. |
| [`animations/`](./animations) | [Manim](https://www.manim.community/) scene utilities (see below). |
| [`assets/`](./assets) | Brand mark used by the chart header. Resolved relative to `kick_style.py`, so it loads from any working directory. |

## Using the style

```python
import sys; sys.path.insert(0, "<repo root>")
from football_visuals.kick_style import *
apply_kick_style()
```

## Animations

```
animations/
├── geometry.py        pure-numpy Voronoi + half-space clipping — imports NO manim
├── pitch.py           StandardPitch: FIFA-dimension pitch as a manim VGroup + coordinate frames
├── voronoi.py         VoronoiManager: deploy players, tessellate, play back tracking frames
├── metric_surface.py  MetricSurface: a gridded metric as 2.5D relief over the pitch
└── example_scene.py   minimal runnable scene
```

Render the example from the repository root:

```bash
manim -pqh football_visuals/animations/example_scene.py VoronoiFrameScene
```

## Two deliberate decoupling choices

**`football_visuals` has no `__init__.py`** (a PEP 420 namespace package). Importing
`football_visuals.kick_style` therefore never reaches `animations/`, so the metric notebooks pull in
matplotlib only — never manim's rendering stack.

**`geometry.py` imports no manim.** The tessellation maths used to live inside the `StandardPitch`
mobject, which meant pitch-control geometry could not be computed or unit-tested without building a
scene graph. It is now plain numpy, and `StandardPitch.get_voronoi_cells()` simply delegates to it.
