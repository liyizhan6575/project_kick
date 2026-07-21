"""The house design VALUES — and nothing else.

This module **imports nothing**. Not matplotlib, not manim, not numpy. That is its entire job and the
one rule to keep: it is the single source of truth for the palette, the ramps, the type scale and the
layout manifest, so *every* renderer can read the same numbers.

Why it exists: the tokens used to live inside `kick_style.py`, which imports matplotlib and mplsoccer
at module top. Anything that could not afford those imports — the manim scenes in `animations/`, a
future video path, a web export — therefore could not read the house palette at all, and drifted to
its own colours. A module with no imports is safe for all of them.

    from kick_tokens import KICK, W, KICK_LAYOUT          # any renderer, any stack
    from football_visuals.kick_style import *             # unchanged for notebooks

`kick_style` re-exports every name here, so `from kick_style import *` keeps working exactly as
before. New code that only needs values should import from here instead.

Colour ramps are exported as **stop lists**, not as built colormap objects — building a
`LinearSegmentedColormap` needs matplotlib. `kick_style` builds the objects; a non-matplotlib renderer
uses `kick_ramp()` below. The stops are the shared truth either way.

The doctrine comments live WITH the values on purpose. A hex without its reason is a hex someone will
"tidy up" — the comment explaining that KICK_SEQ's dark end *is* the panel tone is the only thing
standing between the ramp and a well-meant swap to viridis.
"""

# ── palette ──────────────────────────────────────────────────────────────────
KICK = {
    "figure":     "#0E1116",   # page / figure face
    "panel":      "#161A20",   # pitch & axes face (touchline interior)
    "ink":        "#F2F4F7",
    "ink_soft":   "#AEB6C0",
    "muted":      "#6B7480",
    "grid":       "#232833",
    "pitch_line": "#46505E",
    # ── TEAM COLOURS: a swappable DEFAULT, NOT part of the hard-locked golden rule (people may prefer
    #    others). Home is orange, away is white — white/orange reads best for dots and is grayscale-safe.
    "home":       "#DB6A12",   # orange
    "away":       "#ECEEF1",   # white (a light neutral; the checker bevel adapts for it — see _bevel)
    "danger":     "#E5484D",   # reserved status red (was the old home) — loss / risk, never a team
    "accent":     "#F2C13C",   # single-highlight (e.g. passnet hub) — bright gold, pops against orange
    "green":      "#1F9E5A",
    "teal":       "#0EA5A0",   # categorical group-3
    "purple":     "#7E5CE0",   # categorical group-4
    "ball":       "#F2E23A",   # hi-vis yellow — distinct from orange home AND white away (was neutral white)
}

# ── colour ramps, as STOPS (kick_style builds the Colormap objects from these) ──
# sequential (magnitude): threat / xT / activity. Its DARK end IS the pitch tone (#161A20) so low values
# melt into the pitch and magnitude GLOWS out of it (cool ice-white → white-hot core). Swappable default.
KICK_SEQ_STOPS = ["#161A20", "#26323E", "#5A7488", "#AEC4D4", "#FFFFFF"]
# warm sequential ramp for DISCRETE marks that must stay legible on the dark pitch (passing-network node
# xT, any per-mark magnitude): dark ember → home orange → gold. Counterpart to KICK_SEQ — the ice ramp's
# dark end is the PITCH tone so it melts into a continuous SURFACE, which would make a low-value discrete
# node vanish (and its white top would collide with the away-team white); this stays warm and visible.
KICK_SEQ_WARM_STOPS = ["#6B3D10", KICK["home"], KICK["accent"]]
# diverging (polarity): away ↔ panel-neutral ↔ home — white zones vs orange zones, reading cleanly on dark.
KICK_DIV_STOPS = [KICK["away"], KICK["panel"], KICK["home"]]

KICK_STATUS = {"gain": KICK["green"], "noise": KICK["muted"], "loss": KICK["danger"]}
# categorical grouping order — assign, never cycle. Teams lead (orange/white); teal/purple are extra groups.
KICK_CAT = [KICK["home"], KICK["away"], KICK["teal"], KICK["purple"]]


def W(a):
    """White text at opacity `a`, as an #RRGGBBAA string — the house brightness tier."""
    return "#FFFFFF%02X" % round(a * 255)


def W_pair(a):
    """`W(a)` split into ("#FFFFFF", alpha) — for renderers whose colour and alpha are separate
    arguments (manim's Text takes fill_opacity; an 8-digit hex is silently ignored there)."""
    return "#FFFFFF", float(a)


# ── colour maths (pure python, no numpy — a renderer-agnostic minimum) ────────
def hex_to_rgb(h):
    """'#RRGGBB' or '#RRGGBBAA' → (r, g, b) floats in 0..1. Alpha, if present, is dropped."""
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def rgb_to_hex(rgb):
    """(r, g, b) floats in 0..1 → '#RRGGBB'."""
    return "#%02X%02X%02X" % tuple(max(0, min(255, round(c * 255))) for c in rgb[:3])


def kick_ramp(stops, t):
    """Sample a stop list at `t` ∈ [0,1] by piecewise-linear RGB interpolation → '#RRGGBB'.

    The matplotlib-free equivalent of calling a LinearSegmentedColormap. `kick_style` still builds real
    Colormap objects for matplotlib's sake; this is what every other renderer uses, so a surface drawn
    in a notebook and the same surface drawn in a scene sample the identical ramp."""
    if not stops:
        raise ValueError("kick_ramp: empty stop list")
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else float(t))
    if len(stops) == 1:
        return stops[0]
    pos = t * (len(stops) - 1)
    i = min(int(pos), len(stops) - 2)
    f = pos - i
    a, b = hex_to_rgb(stops[i]), hex_to_rgb(stops[i + 1])
    return rgb_to_hex(tuple(a[k] + (b[k] - a[k]) * f for k in range(3)))


# ── layout constants (inches / points — deliberately medium-independent) ─────
KICK_MARGIN_IN = 0.36    # house outer inset (inches): image edge → pitch touchline / label / logo, everywhere
LOGO_ALPHA = 0.55        # brand-mark opacity, hard-locked (subtler than the data)
LOGO_SCALE = 0.70        # brand-mark height as a fraction of the header block (a small top-right badge)
NODE_ICON_R = 1.05       # node-attached event icon radius (pitch-data units) — FIXED, the same on every node
NODE_ICON_EDGE = 0.62    # its inner edge sits at this fraction of a node's radius (the centre-colour boundary)

# ── typography ───────────────────────────────────────────────────────────────
# The preference ORDER only. Which of these actually resolves depends on what is installed, so the
# concrete font list stays in kick_style (it probes and registers Chakra Petch); this is the intent.
KICK_FONT_STACK = ["Chakra Petch", "Inter", "DejaVu Sans"]


# ── GOLDEN RULE — hard-locked layout manifest (every chart obeys; no chart re-derives these) ──
# Enforced through ONE header path per chart family (kick_title · kick_grid_title · kick_grid_header) and
# checked by kick_verify_margins. Sizes/colours also live in apply_kick_style rcParams (kept in sync here).
#
# Every quantity here is in INCHES or POINTS against a declared 13" canvas — never in pixels. That is
# what makes the rule portable: a renderer with a different canvas converts once and inherits the whole
# manifest, instead of re-tuning offsets by eye.
KICK_LAYOUT = {
    "width_in":       13.0,        # canvas width (portrait pitch matched to 13" so type is pixel-identical)
    "margin_in":      KICK_MARGIN_IN,   # 0.36" uniform outer inset, every edge → nearest ink, everywhere
    "logo_alpha":     LOGO_ALPHA,       # 0.55 brand-mark opacity (less prominent)
    "logo_scale":     LOGO_SCALE,       # 0.70 of the header block — a small corner badge
    "logo_pos":       "top-right",      # top & right edges on the margin (frees the top-left; legends go inside)
    "logo":           "icon-only",      # the KK mark, not the full wordmark
    "header_align":   "center",         # title + subtitle centred over the plot area
    "legend":         "inside",         # ALL legends sit inside the plot (no header legend)
    "title_pt":       20, "title_weight": "bold", "title_opacity": 1.00,
    "sub_pt":         18, "sub_weight":  "normal", "sub_opacity":  0.60,
    "axis_label_pt":  14, "axis_label_opacity": 0.75,
    "axis_unit_opacity": 0.40,     # a trailing "(m/s)" recedes: the eye reads the quantity, then the unit
    "panel_title_pad_pt": 13,      # panel title ↔ its panel: ONE fixed gap, for subplot grids
    #   (ax.set_title(pad=…)) AND pitch grids (kick_panel_label) — never centred in leftover space
    "bar_label_pt":   5,           # value label ↔ bar end: a typographic gap, so it holds at any data range
    "bar_label_headroom": 0.10,    # …and the value axis grows 10% so the label never touches the plot edge
    "tick_pt":        12, "tick_opacity": 0.45,
    # node-attached event icons (subs/goals/assists/…): FIXED size, same on every node, placed TOP-RIGHT
    # with the inner edge on the centre-colour boundary so they never cover the jersey number.
    "node_icon_r":    NODE_ICON_R, "node_icon_edge": NODE_ICON_EDGE, "node_icon_pos": "top-right",
}
