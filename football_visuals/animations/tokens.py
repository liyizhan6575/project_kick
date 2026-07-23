"""The house tokens, translated once for manim.

`kick_tokens` is the single source of truth and imports nothing, so it is safe to read from here.
This module is the only place in `animations/` that converts those values into manim's conventions,
which differ from matplotlib's in three ways worth knowing:

* **Opacity is a separate argument.** `W(0.35)` returns `#FFFFFF59`; manim's `Text`/`Polygon` accept
  an 8-digit hex without complaint and then ignore the alpha. Use `W_pair` — it hands back
  `("#FFFFFF", 0.35)` for the colour/`*_opacity` pair manim actually wants.
* **Stroke width is in pixels, not points.** The still standard draws a pitch line at 1.2 pt on a 13"
  canvas. A manim scene unit is one typographic inch (it renders an em as `font_size/72` units), so
  the 14.2222-unit frame is 13.0 canvas inches wide → 1 canvas inch = 1.0940 units, and at
  1920 px / 14.2222 u = 135 px/u a 1.2 pt line is `1.2/72 * 1.0940 * 135` ≈ 2.2 px. Same line,
  same apparent weight, in both media.
* **Colour ramps are sampled, not passed.** matplotlib takes a Colormap object; manim wants a colour
  per mobject. `kick_ramp(KICK_SEQ_STOPS, t)` returns the same colour the Colormap would, to 1/255.

The conversions live here as named constants so a scene never re-derives them, exactly as
`KICK_LAYOUT` stops a chart re-deriving its margin.
"""
try:                                                   # normal: football_visuals.animations.tokens
    from ..kick_tokens import (
        KICK, KICK_CAT, KICK_STATUS, W_pair, kick_ramp,
        KICK_SEQ_STOPS, KICK_SEQ_WARM_STOPS, KICK_DIV_STOPS, KICK_LAYOUT, KICK_MARGIN_IN,
    )
except ImportError:                                    # manim loads a scene file as a loose script
    import sys as _sys, pathlib as _pathlib
    _sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
    from kick_tokens import (                          # noqa: F401
        KICK, KICK_CAT, KICK_STATUS, W_pair, kick_ramp,
        KICK_SEQ_STOPS, KICK_SEQ_WARM_STOPS, KICK_DIV_STOPS, KICK_LAYOUT, KICK_MARGIN_IN,
    )

__all__ = [
    "KICK", "KICK_CAT", "KICK_STATUS", "W_pair", "kick_ramp",
    "KICK_SEQ_STOPS", "KICK_SEQ_WARM_STOPS", "KICK_DIV_STOPS", "KICK_LAYOUT",
    "FRAME_W", "PX_PER_UNIT", "U_PER_CANVAS_IN", "pt_to_px", "MARGIN_U", "LINE_WIDTH", "seq",
    "MEDALS", "FONT", "FONT_BOLD", "FONT_VALUE", "W",
]

# ── the scene FACE — Inter (a per-format CRAFT choice, like the motion ground; NOT the still identity) ──
# The still house face is Chakra Petch — a monospace-inspired display face that reads as a mark at title
# size. But a MOTION board leans on small numbers/captions (the axis ticks, the qualifier, the count-up
# values, the row names), and there Chakra Petch is wide, grid-like and barely-kerned: digits read as
# gaps ('9 0', '60 0'), and its own near-absent kerning means letter_spacing can't fix it (Pango drops
# kerning the moment spacing is set → uneven). Inter is a superbly-kerned grotesque with tight, even
# figures at every size, so the video moves to it. This lives here with the video law and leaves the
# still identity (kick_style / kick_tokens) untouched. Pango resolves it by family name; weight is a
# Text() argument, so one family covers Regular + Bold.
FONT = "Inter"
FONT_BOLD = "Inter"
# The big RANKING NUMBERS keep the house display face — Chakra Petch's techy figures ARE the identity at
# hero size, and its small-size gappiness is a non-issue that large. Everything else (title, qualifier,
# axis ticks, names/tags, chrome) stays Inter, which kerns tight and even. A deliberate display+text pair.
FONT_VALUE = "Chakra Petch"


def W(a):
    """White at opacity `a`, as an #RRGGBBAA string (mirrors kick_tokens.W). manim's Text ignores the
    alpha byte — pass fill_opacity separately, or use W_pair — but VMobject strokes/fills honour it."""
    return "#FFFFFF%02X" % round(a * 255)


# ── ranking MEDAL tones — top-3 vs the field, retoned to the house palette ───
# Gold is the house accent (separable from home orange); silver/bronze keep the podium metaphor at
# tones that read on the dark stage. The rest of the field is a muted grey.
MEDALS = [KICK["accent"], "#CDD3DA", "#CF8A4B"]

# ── the still canvas ↔ scene frame conversion ────────────────────────────────
FRAME_W = 14.2222                       # manim's default frame width in scene units (16:9 at height 8)
PX_PER_UNIT = 1920.0 / FRAME_W          # 135.0 at 1080p
U_PER_CANVAS_IN = FRAME_W / KICK_LAYOUT["width_in"]     # 1.0940 — one 13" canvas inch, in scene units


def pt_to_px(pt):
    """A still-figure size in POINTS → a manim stroke width in pixels, at matched apparent weight."""
    return pt / 72.0 * U_PER_CANVAS_IN * PX_PER_UNIT


MARGIN_U = KICK_MARGIN_IN * U_PER_CANVAS_IN   # 0.3938 u — the golden rule's 0.36", i.e. the same
#                                               2.77% of frame width the still figure reserves
LINE_WIDTH = pt_to_px(1.2)                    # ≈2.2 px — the house pitch line


def seq(t, ramp=None):
    """Sample the house sequential ramp (ice by default) at `t` ∈ [0,1]. Use the ICE ramp for a
    continuous SURFACE — its dark end IS the panel tone, so low values melt into the pitch and
    magnitude glows out of it — and `KICK_SEQ_WARM_STOPS` for sparse DISCRETE marks, which would
    otherwise vanish at the low end (and collide with the white away team at the high end)."""
    return kick_ramp(ramp or KICK_SEQ_STOPS, t)
