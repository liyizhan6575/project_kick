"""The house MOTION stage — a halftone pitch-ratio canvas with edge chrome.

Every board plays on this surface. A 105:68 rectangle (the same ratio as a pitch) is centred on the
16:9 frame; the letterbox margins it leaves are the chrome zone — vertical labels run up the left
touchline and down the right, section ticks stack bottom-left, the brand badge sits top-right.

Ported from the private film canvas and retoned to the KICK identity: the stage is filled with the
house `panel` tone, bordered in `pitch_line`, textured with a quiet `ink` halftone; the accent is the
house gold. No series branding, no data — the labels are plain parameters.

    apply_motion_config()                        # 1920x1080 / 30fps, house background
    cv = make_canvas(title="INDIVIDUALS", eyebrow="EVALUATION OF",
                     context="WORLD CUP 2026", context_sub="GROUP STAGE",
                     section=0, n_sections=4)
    self.add(*cv.values())                        # the stage + chrome, ready to draw a board into

`STAGE_W` / `STAGE_H` are the stage extents in scene units; a board positions itself against them.
"""
from pathlib import Path

import numpy as np
from PIL import Image
from manim import *

from . import tokens as T

HERE = Path(__file__).resolve().parent
LOGO = HERE.parent / "assets" / "logo_wordmark.png"

# ── geometry (scene units) ───────────────────────────────────────────────────
PITCH_SCALE = 0.098                     # metres → scene units; the stage fills ~83% of the 8.0 frame height
STAGE_W = 105 * PITCH_SCALE             # 10.29 — pitch-ratio stage width
STAGE_H = 68 * PITCH_SCALE              # 6.664 — stage height
FRAME_W, FRAME_H, FPS = 14.2222, 8.0, 30

# ── MOTION SURFACE tones — a per-format CRAFT choice, NOT a change to the shared identity ─────
# A video is watched on a lit screen, where a truer near-black reads better than the notebook's
# slightly-cool figure #0E1116 / panel #161A20 — and the film language wants content on a flat dark
# GROUND, not a lifted blue panel. So the motion ground is darker and neutral, like the film deck.
# Every BRAND HUE (home/accent/teal/purple + the medal tones + pitch_line) is unchanged — those are
# identity, from kick_tokens; only the ground tone is craft, and it lives here with the video law.
MOTION_BG = "#0A0A0B"                   # near-black, essentially neutral
MOTION_STAGE = "#141518"               # the stage: a whisper lifted from the ground, still neutral


def apply_motion_config(output_file="motion", w=1920, h=1080, fps=FPS, ss=1):
    """The one place the 1920x1080 / 16:9 / 30fps frame + motion ground are set. `ss` is the SUPERSAMPLE
    factor: the frame is rendered at `ss`× the target pixel size, then render.py downscales it back to
    (w, h) with a Lanczos filter — SSAA that crisps up thin strokes and small text. Stroke widths are
    resolution-relative in manim (verified), so they need no compensation; only the pixel grid changes."""
    config.pixel_width, config.pixel_height = w * ss, h * ss
    config.frame_width, config.frame_height = FRAME_W, FRAME_H
    config.frame_rate = fps
    config.background_color = MOTION_BG
    config.output_file = output_file


def halftone(width=STAGE_W, height=STAGE_H, spacing=None, dot_r=0.020, alpha=0.08):
    """The quiet dot texture — a hex-offset lattice filling only the STAGE. The grain is what DEFINES the
    content area: a textured stage against clean margins, so the eye reads the stage as the surface and
    the margins as quiet chrome.

    The lattice is CENTRED in the rectangle, so the inset is symmetric — the top row's gap to the top
    edge equals the bottom row's gap to the bottom edge, and likewise left/right. Every row is centred
    horizontally (even and offset rows alike), so the hex offset never breaks the left/right symmetry."""
    if spacing is None:
        spacing = 3.0 * PITCH_SCALE
    n_rows = max(1, int((height - spacing) / spacing) + 1)      # rows that fit with ~spacing/2 inset…
    n_cols = max(1, int((width - spacing) / spacing) + 1)       # …then centre them (below) → symmetric
    y0 = -(n_rows - 1) * spacing / 2.0
    x0 = -(n_cols - 1) * spacing / 2.0
    dots = VGroup()
    for j in range(n_rows):
        y = y0 + j * spacing
        if j % 2 == 0:                                          # full row, centred
            xs = [x0 + i * spacing for i in range(n_cols)]
        else:                                                   # offset row: one fewer dot, still centred
            xs = [x0 + spacing / 2.0 + i * spacing for i in range(n_cols - 1)]
        for x in xs:
            dots.add(Dot([x, y, 0], radius=dot_r, color=T.KICK["ink"], fill_opacity=alpha, stroke_width=0))
    return dots


def _icon_logo(target_h, alpha=0.55):
    """The KK icon (the wordmark cropped to its mark), as an ImageMobject — the badge. Crops the
    transparent padding, then cuts at the first wide internal gap (the icon↔wordmark separator), the
    same rule kick_style uses. Bakes the alpha into the pixel channel (set_opacity would dark-box the
    transparent corners). Returns None if the asset is missing, so a scene never hard-crashes on it."""
    try:
        img = Image.open(LOGO).convert("RGBA")
    except Exception:
        return None
    a = np.asarray(img)[:, :, 3]
    ys, xs = np.where(a > 13)
    if not len(xs):
        return None
    img = img.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))
    col_ink = (np.asarray(img)[:, :, 3] > 13).any(axis=0)
    run = 0; cut = None
    for i, on in enumerate(col_ink):                        # first internal gap ≥ 18 px = icon↔text boundary
        if not on:
            run += 1
            if run >= 18 and (i - run) > 0:
                cut = i - run; break
        else:
            run = 0
    if cut:
        img = img.crop((0, 0, cut, img.height))
        c = np.where((np.asarray(img)[:, :, 3] > 13).any(axis=0))[0]
        img = img.crop((int(c.min()), 0, int(c.max()) + 1, img.height))
    arr = np.asarray(img).copy()
    arr[:, :, 3] = (arr[:, :, 3] * alpha).astype(np.uint8)
    return ImageMobject(arr).scale_to_fit_height(target_h).set_z_index(30)


def _tracked(text, size, color, bold=False, opacity=1.0, tracking=450):
    """A chrome label with letter tracking — the display treatment (uppercase reads as a mark, not a
    word). Pango `letter_spacing` adds space between glyphs; manim's plain Text has no tracking, so this
    routes through MarkupText. `color` is a solid hex; opacity is applied separately (an 8-digit hex
    would be dropped). Tracking is measured, not eyeballed — 450 at the 24pt title reads as a cohesive
    mark; small caps take a touch more (see the eyebrow/sub call sites) but nowhere near the original
    1150/2200, which gapped the glyphs so wide the word fell apart."""
    fw = "bold" if bold else "normal"
    m = MarkupText(f'<span letter_spacing="{tracking}" font_weight="{fw}">{text}</span>',
                   font=T.FONT, font_size=size, color=color)
    if opacity != 1.0:
        m.set_opacity(opacity)
    return m


def crisp_text(text, font_size, base=64, **kw):
    """Latin text at a small `font_size` MIS-KERNS in manim/Pango ('9 0', '≥60 0', 'S hot s Faced') — a
    LAYOUT bug (wrong glyph positions), not rasterisation, so supersampling can't touch it. Render at a
    large `base` size where the kerning is correct, then uniformly scale down: crisp and layout-preserving.
    This is the private film's `board_common.crisp_text` trick — and the reason the scale_to_fit_height
    row text (names/values, built at the default 48 then shrunk) always looked right while the small
    explicit-`font_size` labels (title/qualifier/ticks/footnote) gapped. Use this for those."""
    return Text(text, font_size=base, **kw).scale(font_size / base)


def make_canvas(title="INDIVIDUALS", eyebrow="EVALUATION OF",
                context="WORLD CUP 2026", context_sub="GROUP STAGE",
                section=0, n_sections=4, watermark=True, emblem=None):
    """Build the stage + chrome and return them as a dict of positioned mobjects (add them, then draw
    a board into the stage). Text is vertical along the touchlines — the signature look.

    Two brand marks, film-canvas style: the KK mark is a faint CENTRE watermark on the stage (an
    ownership undertone the content sits over), and `emblem` — a mobject the CALLER supplies, e.g. an
    ImageMobject of the tournament / event logo — rides the TOP-RIGHT. The repo ships no tournament
    marks (they are trademarked), so that slot is a parameter: pass your own, or leave it empty."""
    W2, H2 = STAGE_W / 2, STAGE_H / 2
    # Stage = a neutral fill (behind), a full-frame halftone (a background grain over everything), and a
    # pitch_line border (in front). Splitting fill from border lets the grain sit BETWEEN them, so the
    # texture reads over the stage and the margins alike.
    stage = Rectangle(width=STAGE_W, height=STAGE_H, fill_color=MOTION_STAGE, fill_opacity=1.0,
                      stroke_width=0).set_z_index(-10)
    dots = halftone().set_z_index(-5)
    border = Rectangle(width=STAGE_W, height=STAGE_H, stroke_color=T.KICK["pitch_line"],
                       stroke_width=1.8, fill_opacity=0.0).set_stroke(opacity=0.65).set_z_index(1)
    out = {"stage": stage, "canvas": dots, "frame": border}

    # CHROME is framing, not message: it sits a clear tier BELOW whatever content the stage holds. It is
    # small (24) and QUIET (~38% white), with WIDE LETTER TRACKING (the display treatment — an uppercase
    # label reads as a mark, not a word). The accent eyebrow is the one small pop, itself held back.
    # LEFT (vertical, reads bottom→top): eyebrow (accent) above the title, top-aligned
    tm = _tracked(title, 24, "#FFFFFF", bold=True, opacity=0.40).rotate(PI / 2)
    max_h = STAGE_H - 1.4
    if tm.height > max_h:
        tm.scale(max_h / tm.height)
    es = _tracked(eyebrow, 13, T.KICK["accent"], opacity=0.65, tracking=750).rotate(PI / 2)
    left = VGroup(tm, es).arrange(LEFT, aligned_edge=UP, buff=0.16).set_z_index(20)
    left.move_to([-W2 - 0.22 - left.width / 2, H2 - left.height / 2, 0])
    out["title"] = left

    # RIGHT (vertical, reads top→bottom): context + sub, bottom-aligned
    cm = _tracked(context, 24, "#FFFFFF", bold=True, opacity=0.38).rotate(-PI / 2)
    cs = _tracked(context_sub, 13, "#FFFFFF", opacity=0.28, tracking=750).rotate(-PI / 2)
    right = VGroup(cm, cs).arrange(RIGHT, aligned_edge=DOWN, buff=0.16).set_z_index(20)
    right.move_to([W2 + 0.22 + right.width / 2, -H2 + right.height / 2, 0])
    out["context"] = right

    # BOTTOM-LEFT section ticks — the current one reads, the rest are near-ghost framing
    tw = left.width
    ticks = VGroup(*[Rectangle(width=tw, height=0.18, fill_color=T.W(0.55), fill_opacity=1.0,
                               stroke_width=0) for _ in range(n_sections)]).arrange(DOWN, buff=0.12)
    ticks.set_z_index(20).move_to([left.get_center()[0], -H2 + ticks.height / 2, 0])
    for i, s in enumerate(ticks):
        if i != section:
            s.set_opacity(0.20)
    out["ticks"] = ticks

    # CENTRE watermark — the KK mark, large and faint, an ownership undertone the content draws over
    # (z=0: above the stage fill + grain, below the axis/bars/values). The film canvas puts the brand
    # here so the corner stays free for the event's own logo.
    if watermark:
        wm = _icon_logo(1.35, alpha=0.08)
        if wm is not None:
            wm.move_to(ORIGIN).set_z_index(0)
            out["watermark"] = wm

    # TOP-RIGHT emblem — the tournament / event logo the caller supplies. Scaled to the context text
    # block's WIDTH so BOTH its edges align with that text (left→left, right→right) whatever the logo's
    # aspect — a wide mark and a tall one both sit in the same column — and top-aligned to the top
    # touchline. (The PNGs are tight-trimmed, so the box matches the visible ink.) The repo ships none.
    if emblem is not None:
        emblem.scale_to_fit_width(right.width)
        left_x = right.get_left()[0]                      # the context block's left edge
        emblem.move_to([left_x + emblem.width / 2, H2 - emblem.height / 2, 0]).set_z_index(30)
        out["emblem"] = emblem
    return out


# ── JSON bridge: a `canvas` spec block → the positioned stage+chrome dict ─────────────────────────
def load_emblem(path, root=None):
    """Load a PRE-PROCESSED emblem PNG (already white-on-transparent and tight-trimmed — see
    assets/emblems/README.md) as an ImageMobject for the top-right slot. `path` is absolute, or relative
    to the football_visuals package root. The PNG carries its own per-pixel alpha, so ImageMobject shows
    it cleanly — no `set_opacity` dark-box. Returns None if the asset is missing or unreadable, so a spec
    that names a wrong path degrades to an empty slot (exactly what `emblem=None` does) instead of
    crashing the render."""
    if not path:
        return None
    p = Path(path)
    if not p.is_absolute():
        p = (Path(root) if root else HERE.parent) / p
    try:
        img = Image.open(p).convert("RGBA")
    except Exception:
        return None
    return ImageMobject(np.asarray(img))


_CANVAS_KEYS = ("title", "eyebrow", "context", "context_sub", "section", "n_sections", "watermark")


def build_canvas(spec, root=None):
    """Turn a JSON `canvas` block into the stage+chrome dict. The only field needing resolution is
    `emblem`, a PATH here vs a mobject in `make_canvas` — load it, then delegate. Unknown keys are ignored
    so a spec may carry extra annotation without breaking the render."""
    spec = dict(spec or {})
    emb = spec.pop("emblem", None)
    kw = {k: spec[k] for k in _CANVAS_KEYS if k in spec}
    kw["emblem"] = load_emblem(emb, root=root) if emb else None
    return make_canvas(**kw)
