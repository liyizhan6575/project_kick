"""project_kick visualization style — the house design system.

Import in a notebook with:  from kick_style import *  ; then call apply_kick_style().
Colour by job (categorical teams / sequential magma / diverging team-poles), Inter type scale
(20/18/16/14, white-opacity tiers), dark pitch with a lighter touchline interior, logo header.
"""
import os, glob, re
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patheffects as pe
import matplotlib.font_manager as fm
import matplotlib.transforms as mtransforms
from matplotlib.colors import LinearSegmentedColormap, to_rgb, to_rgba
from matplotlib.patches import Rectangle, Circle, Wedge, PathPatch, Patch
from matplotlib.textpath import TextPath
from matplotlib.ticker import FuncFormatter
from mplsoccer import Pitch, VerticalPitch

# A star-import must not re-export the modules above: without this list it replaces a notebook's
# `from glob import glob` with the `glob` *module*.
__all__ = [
    # palette & layout constants
    "KICK", "KICK_CAT", "KICK_DIV", "KICK_SEQ", "KICK_SEQ_WARM", "KICK_STATUS",
    "KICK_FONT", "KICK_ICONS", "KICK_LAYOUT", "KICK_LOGO", "KICK_MARGIN_IN",
    "LOGO_ALPHA", "LOGO_SCALE", "NODE_ICON_EDGE", "NODE_ICON_R", "W",
    # house helpers
    "apply_kick_style", "draw_kick_pitch", "kick_caption", "kick_cbar", "kick_checker",
    "kick_contour", "kick_flat_legend", "kick_grid", "kick_grid_cbar", "kick_grid_header",
    "kick_grid_title", "kick_header_legend", "kick_heatmap", "kick_hide_origin_zero",
    "kick_inside_legend", "kick_legend", "kick_node_icon", "kick_panel_label", "kick_pitch",
    "kick_reserve_legend", "kick_smart_labels", "kick_swatch", "kick_tiered_title",
    "kick_bar_labels", "kick_clip", "kick_tilt_big_ticks", "kick_title", "kick_verify_margins",
    # matplotlib / mplsoccer names the notebooks build their figures with
    "Circle", "FuncFormatter", "LinearSegmentedColormap", "Patch", "PathPatch", "Pitch",
    "Rectangle", "TextPath", "VerticalPitch", "Wedge", "to_rgb", "to_rgba",
]

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
# sequential (magnitude): threat / xT / activity. Its DARK end IS the pitch tone (#161A20) so low values
# melt into the pitch and magnitude GLOWS out of it (cool ice-white → white-hot core). Swappable default.
KICK_SEQ = LinearSegmentedColormap.from_list(
    "kick_ice", ["#161A20", "#26323E", "#5A7488", "#AEC4D4", "#FFFFFF"])
# warm sequential ramp for DISCRETE marks that must stay legible on the dark pitch (passing-network node
# xT, any per-mark magnitude): dark ember → home orange → gold. Counterpart to KICK_SEQ — the ice ramp's
# dark end is the PITCH tone so it melts into a continuous SURFACE, which would make a low-value discrete
# node vanish (and its white top would collide with the away-team white); this stays warm and visible.
KICK_SEQ_WARM = LinearSegmentedColormap.from_list(
    "kick_warm", ["#6B3D10", KICK["home"], KICK["accent"]])
KICK_DIV = LinearSegmentedColormap.from_list("kick_div", [KICK["away"], KICK["panel"], KICK["home"]])
KICK_STATUS = {"gain": KICK["green"], "noise": KICK["muted"], "loss": KICK["danger"]}
# categorical grouping order — assign, never cycle. Teams lead (orange/white); teal/purple are extra groups.
KICK_CAT = [KICK["home"], KICK["away"], KICK["teal"], KICK["purple"]]

def W(a): return "#FFFFFF%02X" % round(a * 255)          # white text at opacity a

KICK_MARGIN_IN = 0.36    # house outer inset (inches): image edge → pitch touchline / label / logo, everywhere
LOGO_ALPHA = 0.55        # brand-mark opacity, hard-locked (subtler than the data)
LOGO_SCALE = 0.70        # brand-mark height as a fraction of the header block (a small top-right badge)
NODE_ICON_R = 1.05       # node-attached event icon radius (pitch-data units) — FIXED, the same on every node
NODE_ICON_EDGE = 0.62    # its inner edge sits at this fraction of a node's radius (the centre-colour boundary)


def _load_logo(path=None, icon_only=True):
    """Load the brand mark. icon_only=True (default) keeps ONLY the graphical 'KK' icon — the wordmark is
    trimmed to its ink, then cut at the first wide internal gap (the icon↔'PROJ. KICK' separator), leaving
    a clean, elegant square-ish mark for the chart corner. The asset is resolved relative to THIS module
    (not the caller's cwd) so the logo loads no matter which notebook / directory imports kick_style."""
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo_wordmark.png")
    try:
        img = mpimg.imread(path)
    except Exception:
        return None
    if not (img.ndim == 3 and img.shape[-1] == 4):
        return img
    ys, xs = np.where(img[:, :, 3] > 0.05)                # trim transparent padding
    if not len(xs):
        return img
    img = img[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    if icon_only:
        ink = (img[..., 3] > 0.05).any(axis=0)            # columns that carry ink
        run = 0; cut = None
        for i, on in enumerate(ink):                      # first internal gap ≥ 18 px = icon↔text boundary
            if not on:
                run += 1
                if run >= 18 and (i - run) > 0:
                    cut = i - run; break
            else:
                run = 0
        if cut:
            img = img[:, :cut]
            c = np.where((img[..., 3] > 0.05).any(axis=0))[0]   # re-trim to the icon's ink
            img = img[:, c.min():c.max() + 1]
    return img
KICK_LOGO = _load_logo()


# ── typography: register Chakra Petch (techy display face) if present; else fall back to Inter ─
def _register_fonts(substr):
    found = False
    for base in ("~/.local/share/fonts", "~/.fonts"):
        for f in glob.glob(os.path.join(os.path.expanduser(base), "**", "*.ttf"), recursive=True):
            if substr in os.path.basename(f).replace(" ", "").lower():
                try:
                    fm.fontManager.addfont(f); found = True
                except Exception:
                    pass
    return found
_HAS_CHAKRA = _register_fonts("chakrapetch")
KICK_FONT = (["Chakra Petch", "Inter", "DejaVu Sans"] if _HAS_CHAKRA else ["Inter", "DejaVu Sans"])


def apply_kick_style():
    mpl.rcParams.update({
        "figure.facecolor":  KICK["figure"], "savefig.facecolor": KICK["figure"],
        "axes.facecolor":    KICK["panel"],
        "text.color":        W(1.0), "axes.titlecolor": W(1.0),
        "axes.labelcolor":   W(0.75), "axes.edgecolor": W(0.35),   # axis label toned down (was 0.80)
        "xtick.color":       W(0.45), "ytick.color": W(0.45),      # ticks more muted (was 0.55)
        "axes.titlesize": 20, "axes.titleweight": "normal",
        "figure.titlesize": 20, "axes.labelsize": 14, "axes.labelpad": 10,   # axis label 14; gap to ticks
        "xtick.labelsize": 12, "ytick.labelsize": 12,              # tick labels 12
        "legend.fontsize": 14, "legend.frameon": False, "legend.labelcolor": W(0.55),
        "legend.handletextpad": 0.6,          # house gap between a legend marker/swatch and its text

        "font.family": "sans-serif", "font.sans-serif": KICK_FONT, "font.size": 16,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": False, "grid.color": KICK["grid"], "grid.linewidth": 0.8,
        "figure.dpi": 150,
    })
    try:
        get_ipython().run_line_magic(       # capture at true margins (no tight-crop)
            "config", "InlineBackend.print_figure_kwargs = {'bbox_inches': None, 'facecolor': '#0E1116'}")
    except Exception:
        pass

apply_kick_style()


# ── GOLDEN RULE — hard-locked layout manifest (every chart obeys; no chart re-derives these) ──
# Enforced through ONE header path per chart family (kick_title · kick_grid_title · kick_grid_header) and
# checked by kick_verify_margins. Sizes/colours also live in apply_kick_style rcParams (kept in sync here).
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
    "bar_label_pt":   5,           # value label ↔ bar end: a typographic gap, so it holds at any data range
    "bar_label_headroom": 0.10,    # …and the value axis grows 10% so the label never touches the plot edge
    "tick_pt":        12, "tick_opacity": 0.45,
    # node-attached event icons (subs/goals/assists/…): FIXED size, same on every node, placed TOP-RIGHT
    # with the inner edge on the centre-colour boundary so they never cover the jersey number.
    "node_icon_r":    NODE_ICON_R, "node_icon_edge": NODE_ICON_EDGE, "node_icon_pos": "top-right",
}


def _draw_logo(fig, anchor_x, header_top, header_h, logo, logo_alpha, logo_cap,
               align="right", scale=LOGO_SCALE):
    """Place the icon as a small corner badge: top edge at header_top, height = header_h*scale (width-capped).
    align='right' (house default) → right edge at anchor_x (top-right); 'left' → left edge at anchor_x."""
    if not (logo and KICK_LOGO is not None):
        return
    Wf, Hf = fig.get_size_inches()
    lh = header_h * scale
    lw = (KICK_LOGO.shape[1] / KICK_LOGO.shape[0]) * lh * (Hf / Wf)
    if lw > logo_cap:                                    # portrait: cap width, keep top-aligned
        lh *= logo_cap / lw; lw = logo_cap
    left = (anchor_x - lw) if align == "right" else anchor_x
    lax = fig.add_axes([left, header_top - lh, lw, lh]); lax.axis("off")
    img = KICK_LOGO.copy()
    if img.shape[-1] == 4:
        img[..., 3] = img[..., 3] * logo_alpha
    lax.imshow(img)


def _logo_width(fig, header_h, logo_cap):
    """Figure-fraction width of the wordmark for a given header height (mirrors _draw_logo's cap)."""
    if KICK_LOGO is None:
        return 0.0
    Wf, Hf = fig.get_size_inches()
    lw = (KICK_LOGO.shape[1] / KICK_LOGO.shape[0]) * header_h * (Hf / Wf)
    return min(lw, logo_cap)


def _xtick_overhang(axes, target_x, inv, renderer):
    """How far the last x tick label pokes RIGHT of `target_x`, in figure fraction (0 if it doesn't).

    The house solvers reserve the left/bottom margins to tick INK but the right one only to the axes
    SPINE — so an axis whose upper limit lands exactly on a tick ("10.0", "30") pushes half that label
    into the reserved margin. Subtracting this closes the asymmetry.

    Only ticks actually IN VIEW count: AutoLocator also emits ticks outside xlim, which are never drawn
    yet still carry text and a window extent far past the spine. Reading those would drag the axes
    right edge halfway across the figure."""
    over = 0.0
    for ax in axes:
        lo, hi = sorted(ax.get_xlim())
        for t in ax.get_xticklabels():
            if not t.get_text():
                continue
            tx = t.get_position()[0]                     # the tick's DATA x
            if not (lo - 1e-9 <= tx <= hi + 1e-9):
                continue                                 # locator emitted it, matplotlib never drew it
            x1 = t.get_window_extent(renderer).transformed(inv).x1
            over = max(over, x1 - target_x)
    return over


def kick_title(fig, ax, title, subtitle=None, pitch=True, size=20, sub_size=18,
               reserve=0.24, logo=True, logo_alpha=LOGO_ALPHA, logo_cap=0.26, margin_in=KICK_MARGIN_IN):
    """Bold title + optional muted subtitle, centred, with a small icon badge top-right. On a PITCH: header
    centred over the pitch, badge on the right touchline. On a NON-PITCH chart (ticks + labels): a **uniform
    inset** — the same margin `margin_in` from every image edge to the header top, the leftmost label, the
    x-label bottom, and the axes right; the y-label's left edge sits on the left margin. Gestalt:
    title+subtitle grouped, set a margin's gap above the plot."""
    Wf, Hf = fig.get_size_inches()
    th, sh = size / 72 / Hf, sub_size / 72 / Hf
    if pitch and hasattr(ax, "_kick_bounds"):
        fig.canvas.draw()
        x_lo, x_hi, y_lo, y_hi = ax._kick_bounds
        figc = fig.transFigure.inverted().transform(
            ax.transData.transform([(x_lo, y_lo), (x_lo, y_hi), (x_hi, y_lo), (x_hi, y_hi)]))
        top, xmid, right_x = figc[:, 1].max(), figc[:, 0].mean(), figc[:, 0].max()
        mid = (top + 1.0) / 2
        if subtitle:
            gap = 0.5 * th; y_top = mid + (th + gap + sh) / 2
            fig.text(xmid, y_top, title, ha="center", va="top", fontsize=size, fontweight="bold", color=W(1.0))
            fig.text(xmid, y_top - th - gap, subtitle, ha="center", va="top", fontsize=sub_size, color=W(0.60))
            _draw_logo(fig, right_x, y_top, th + gap + sh, logo, logo_alpha, logo_cap)   # top-right badge
        else:
            fig.text(xmid, mid, title, ha="center", va="center", fontsize=size, fontweight="bold", color=W(1.0))
            _draw_logo(fig, right_x, mid + th / 2, th, logo, logo_alpha, logo_cap)
        return
    # ---- non-pitch: uniform inset — same margin from every edge to logo-top / label-left / x-label-bottom /
    # axes-right; the y-label left aligns with the logo left, so the y-axis lands ~on the logo icon's edge ----
    ml, mv = margin_in / Wf, margin_in / Hf                # left/right and top/bottom margins (figure fraction)
    header_h = (th + 0.5 * th + sh) if subtitle else th
    top_ax = 1 - 2 * mv - header_h                        # top margin + header + a margin-gap above the plot
    fig.subplots_adjust(left=0.11, right=1 - ml, top=top_ax, bottom=0.16)   # provisional, to measure the labels
    fig.canvas.draw()
    pos = ax.get_position(); inv = fig.transFigure.inverted()
    yt = [t.get_window_extent().transformed(inv).x0 for t in ax.get_yticklabels() if t.get_text()]
    if ax.get_ylabel(): yt.append(ax.yaxis.label.get_window_extent().transformed(inv).x0)
    xt = [t.get_window_extent().transformed(inv).y0 for t in ax.get_xticklabels() if t.get_text()]
    if ax.get_xlabel(): xt.append(ax.xaxis.label.get_window_extent().transformed(inv).y0)
    gy = pos.x0 - (min(yt) if yt else pos.x0)            # y stack width (leftmost of ticks + label)
    hx = pos.y0 - (min(xt) if xt else pos.y0)            # x stack height (lowest of ticks + label)
    rx = _xtick_overhang([ax], pos.x1, inv, None)        # last x tick centred ON the axes-right spine
    fig.subplots_adjust(left=ml + gy, right=1 - ml - rx, top=top_ax, bottom=mv + hx)  # every edge → ink
    fig.canvas.draw()
    pos = ax.get_position(); xmid = (pos.x0 + pos.x1) / 2
    header_top = 1 - mv                                   # logo + title top at the top margin
    fig.text(xmid, header_top, title, ha="center", va="top", fontsize=size, fontweight="bold", color=W(1.0))
    if subtitle:
        fig.text(xmid, header_top - th - 0.5 * th, subtitle, ha="center", va="top",
                 fontsize=sub_size, color=W(0.60))
    _draw_logo(fig, 1 - ml, header_top, header_h, logo, logo_alpha, logo_cap)   # top-right badge
    for lab in (ax.xaxis.label, ax.yaxis.label):      # quantity bright, unit recessive (golden rule)
        _dim_units(fig, lab)


_UNIT_RE = re.compile(r"^(.+?)(\s*[(\[][^()\[\]]*[)\]])\s*$")


def _dim_units(fig, art, unit_alpha=None):
    """GOLDEN RULE — an axis label names the QUANTITY first and its unit second.

    Re-draws "Speed (m/s)" as a normal-weight "Speed" followed by a recessive "(m/s)", so the eye lands
    on what is being measured before how it is measured. The pair stays centred exactly where the single
    label sat, so the solved margins are untouched. A label with no trailing (unit) is left alone."""
    s = art.get_text()
    m = _UNIT_RE.match(s or "")
    if not m:
        return
    name, unit = m.group(1), m.group(2)
    alpha = KICK_LAYOUT["axis_unit_opacity"] if unit_alpha is None else unit_alpha
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    props = dict(fontsize=art.get_fontsize(), fontfamily=art.get_fontfamily(),
                 fontweight=art.get_fontweight())

    def advance(t):                               # unrotated advance width in display px
        probe = fig.text(0, 0, t, rotation=0, **props)
        w = probe.get_window_extent(r).width
        probe.remove()
        return w

    wn, total = advance(name), advance(name) + advance(unit)
    bb = art.get_window_extent(r)
    art.set_visible(False)
    inv = fig.transFigure.inverted()
    vertical = abs(art.get_rotation() % 180 - 90) < 1e-6
    cross = (bb.x0 + bb.x1) / 2 if vertical else (bb.y0 + bb.y1) / 2   # the axis the label doesn't run along
    start = ((bb.y0 + bb.y1) if vertical else (bb.x0 + bb.x1)) / 2 - total / 2
    for txt, col in ((name, art.get_color()), (unit, W(alpha))):
        px = (cross, start) if vertical else (start, cross)
        fx, fy = inv.transform(px)
        fig.text(fx, fy, txt, color=col, ha="left", va="center",
                 rotation=90 if vertical else 0, rotation_mode="anchor", **props)
        start += wn


def kick_bar_labels(ax, positions, values, fmt="{:.2f}", orient="v", pad_pt=None,
                    headroom=None, fontsize=11, color=None):
    """GOLDEN RULE — a bar's value label sits a fixed `bar_label_pt` gap off the bar END, in POINTS, not
    in data units: the same optical gap whatever the axis range or figure size. The value axis then grows
    by `bar_label_headroom` so the topmost label can never collide with the plot edge.
    orient="v" labels above vertical bars; "h" labels to the right of horizontal bars."""
    pad = KICK_LAYOUT["bar_label_pt"] if pad_pt is None else pad_pt
    room = KICK_LAYOUT["bar_label_headroom"] if headroom is None else headroom
    color = W(0.68) if color is None else color
    vals = np.asarray(list(values), dtype=float)
    vertical = orient == "v"
    for p, v in zip(positions, vals):
        if not np.isfinite(v):
            continue
        ax.annotate(fmt.format(v), (p, v) if vertical else (v, p),
                    textcoords="offset points", xytext=(0, pad) if vertical else (pad, 0),
                    ha="center" if vertical else "left", va="bottom" if vertical else "center",
                    fontsize=fontsize, color=color, annotation_clip=False)
    vmax = np.nanmax(vals) if np.isfinite(vals).any() else 0.0
    lo, hi = ax.get_ylim() if vertical else ax.get_xlim()
    (ax.set_ylim if vertical else ax.set_xlim)(lo, max(hi, vmax * (1 + room)))


def _nice_round(v):
    """Snap to the nearest 1 / 2 / 2.5 / 5 / 10 × 10^k, so a tick reads as a number a person would say."""
    if v <= 0:
        return 0.0
    e = 10.0 ** np.floor(np.log10(v))
    return float(min((1, 2, 2.5, 5, 10), key=lambda m: abs(m * e - v)) * e)


def _kick_cbar_ticks(cb, mappable, n=6, min_gap=0.09):
    """A non-linear norm (PowerNorm, LogNorm) squeezes the top of the ramp, so matplotlib's evenly
    spaced *values* land as a crowd of overlapping labels at the bright end. Sample evenly along the
    BAR instead, snap each sample to a round number, and drop any that still sit too close together.
    A linear norm keeps matplotlib's own ticks."""
    norm = getattr(mappable, "norm", None)
    if norm is None or type(norm) is mpl.colors.Normalize:
        return
    try:
        vmin, vmax = float(norm.vmin), float(norm.vmax)
    except (TypeError, ValueError):
        return
    if not np.isfinite([vmin, vmax]).all() or vmax <= vmin:
        return

    ticks, pos = [], []
    for t in np.linspace(0, 1, n):
        v = _nice_round(float(norm.inverse(t)))
        if not (vmin <= v <= vmax):
            continue                                   # snapping overshot the ramp — no tick there
        p = float(norm(v))
        if ticks and abs(p - pos[-1]) < min_gap:
            continue
        ticks.append(v)
        pos.append(p)
    if len(ticks) < 2:
        return
    cb.set_ticks(ticks)
    axis = cb.ax.xaxis if cb.orientation == "horizontal" else cb.ax.yaxis
    axis.set_major_formatter(FuncFormatter(
        lambda v, _: f"{v/1000:g}k" if vmax >= 10000 and v >= 1000 else f"{v:g}"))


def kick_cbar(fig, ax, mappable, label, frac=0.5):
    """Slim recessive colourbar, placed to match how the pitch reserved space (draw with cbar=True):
    a horizontal bar centred under the pitch (cbar_pos="bottom", default) or a vertical bar in the right
    gutter (cbar_pos="right"). frac is the horizontal bar's width as a fraction of the pitch width."""
    if getattr(ax, "_kick_cbar_pos", "right") == "bottom":
        fig.canvas.draw()
        x_lo, x_hi, y_lo, y_hi = ax._kick_bounds
        figc = fig.transFigure.inverted().transform(
            ax.transData.transform([(x_lo, y_lo), (x_hi, y_lo), (x_lo, y_hi), (x_hi, y_hi)]))
        bottom, xmid = figc[:, 1].min(), figc[:, 0].mean()
        pw = figc[:, 0].max() - figc[:, 0].min()
        Wf, Hf = fig.get_size_inches()
        m_in = figc[:, 0].min() * Wf                  # side margin (inches) → uniform inset
        cw, bar_h = frac * pw, 0.13 / Hf
        cax = fig.add_axes([xmid - cw / 2, bottom - m_in / Hf - bar_h, cw, bar_h])
        cb = fig.colorbar(mappable, cax=cax, orientation="horizontal")
        cb.set_label(label, color=W(0.80), fontsize=14)
        cb.ax.xaxis.labelpad = 12                     # breathing room between tick numbers and the label
        cb.ax.tick_params(colors=W(0.55), labelsize=12)
        cb.outline.set_edgecolor(KICK["grid"])
        _kick_cbar_ticks(cb, mappable)
        fig.canvas.draw()                             # shift so the LABEL's bottom (lowest ink) keeps a
        lb = cb.ax.xaxis.label.get_window_extent().transformed(fig.transFigure.inverted()).y0
        p = cax.get_position()                        # full side-margin above the image edge, not the bar
        cax.set_position([p.x0, p.y0 + (m_in / Hf - lb), p.width, p.height])
        _dim_units(fig, cb.ax.xaxis.label)            # quantity bright, unit recessive (golden rule)
        return cb
    pos = ax.get_position()
    cax = fig.add_axes([pos.x1 + 0.014, pos.y0 + pos.height * 0.14, 0.011, pos.height * 0.72])
    cb = fig.colorbar(mappable, cax=cax)
    cb.set_label(label, color=W(0.80), fontsize=14)
    cb.ax.tick_params(colors=W(0.55), labelsize=12)
    cb.outline.set_edgecolor(KICK["grid"])
    _kick_cbar_ticks(cb, mappable)
    _dim_units(fig, cb.ax.yaxis.label)
    return cb


def kick_clip(*axes):
    """Clip DATA artists to the pitch's touchline box, so off-pitch points can't bleed into the margin.

    A house pitch reserves its 0.36" margin to the TOUCHLINE, while mplsoccer's `pad` band sits INSIDE
    the axes — so matplotlib's default clipping lets a point plotted beyond the touchline (a run
    standardised to the team centroid, say) draw straight into the reserved margin. This clips only the
    lines/collections added AFTER the pitch was drawn (`_kick_data0`); the pitch's own boundary and goal
    strokes are left alone, so every frame keeps rendering identically."""
    flat = []
    for a in axes:
        flat.extend(np.asarray(a, dtype=object).ravel().tolist() if isinstance(a, (np.ndarray, list, tuple)) else [a])
    for ax in flat:
        if not hasattr(ax, "_kick_bounds"):
            continue
        x_lo, x_hi, y_lo, y_hi = ax._kick_bounds
        n_lines, n_coll = getattr(ax, "_kick_data0", (0, 0))
        box = Rectangle((x_lo, y_lo), x_hi - x_lo, y_hi - y_lo, transform=ax.transData)
        for art in list(ax.lines)[n_lines:] + list(ax.collections)[n_coll:]:
            art.set_clip_path(box)


def kick_pitch(pitch_type="statsbomb", vertical=False, line_zorder=2, pad=2, **kw):
    P = VerticalPitch if vertical else Pitch
    return P(pitch_type=pitch_type, pitch_color=KICK["figure"], line_color=KICK["pitch_line"],
             linewidth=1.2, line_zorder=line_zorder,
             pad_left=pad, pad_right=pad, pad_top=pad, pad_bottom=pad, **kw)


def _touchlines(pitch, vertical, xlim, ylim, pad):
    """Visible pitch box in DRAWN coords, plus the real per-axis pad.

    A plain `lim ± pad` is wrong on the 100×100 systems (wyscout / opta): mplsoccer scales the pad on
    the pitch's LENGTH axis by `dim.aspect`, so pad=2 is drawn as 1.295 there. Scale the same way and
    the box is exact for every pitch type, orientation, and for `half=True` (where the halfway cut is
    padded like a touchline, and `dim.pitch_extent` would wrongly report the full pitch)."""
    a = pitch.dim.aspect
    pad_x = pad * (1.0 if vertical else a)      # length runs along x when horizontal, y when vertical
    pad_y = pad * (a if vertical else 1.0)
    return (min(xlim) + pad_x, max(xlim) - pad_x, min(ylim) + pad_y, max(ylim) - pad_y), pad_x, pad_y


def draw_kick_pitch(pitch_type="statsbomb", vertical=False, line_zorder=2, pad=2,
                    width=None, margin_in=KICK_MARGIN_IN, title_pt=20, sub_pt=18,
                    legend=False, leg_in=0.72, caption=False, cap_in=2 * KICK_MARGIN_IN + 0.22,
                    cbar=False, cbar_pos="bottom", cbar_gutter=0.09, cbar_band=0.74, **pitch_kw):
    """House pitch filling the frame with a uniform inset (top gap above the header == side margin).
    The outer touchline margin is fixed at `margin_in` inches on every side. The PITCH SCALE (inches per
    metre) is the SAME in both orientations — the field's long side always spans `ref - 2*margin` — so a
    portrait pitch is NARROWER than a landscape one (same field rotated), NOT forced to the same width.
    Bottom band == side margin when no legend, or a wider band (leg_in) with a legend. cbar reserves
    room for the colourbar: cbar_pos="bottom" a band under the pitch (horizontal bar), or "right" a slim
    right gutter (vertical bar). Works for horizontal and vertical (bounds read from drawn limits)."""
    pitch = kick_pitch(pitch_type, vertical, line_zorder, pad=pad, **pitch_kw)
    tmp_fig, tmp_ax = pitch.draw(figsize=(4, 4))
    xr = abs(np.diff(tmp_ax.get_xlim())[0]); yr = abs(np.diff(tmp_ax.get_ylim())[0])
    aspect = xr / (yr * tmp_ax.get_aspect())   # true display aspect (get_aspect≠1 for wyscout/opta 100×100)
    bounds, pad_x, pad_y = _touchlines(pitch, vertical, tmp_ax.get_xlim(), tmp_ax.get_ylim(), pad)
    plt.close(tmp_fig)
    if width is None:
        # SAME pitch scale (inches per metre) in BOTH orientations — the field's LONG side always spans
        # (ref - 2*margin). So a PORTRAIT pitch comes out NARROWER than a landscape one (same field, just
        # rotated) — it does NOT share the landscape width. Type stays pixel-identical (constant DPI).
        field_x, field_y = bounds[1] - bounds[0], bounds[3] - bounds[2]   # touchline extents, data units
        ref = KICK_LAYOUT["width_in"]                        # house landscape width; its long side ↔ ref - 2m
        width = field_x * (ref - 2 * margin_in) / max(field_x, field_y) + 2 * margin_in
    pad_xfrac, pad_yfrac = pad_x / xr, pad_y / yr
    right_gutter = cbar_gutter if (cbar and cbar_pos == "right") else 0.0
    tgt = margin_in / width                              # solve h_margin so touchline margin == margin_in
    h_margin = ((tgt - pad_xfrac * (1 - right_gutter)) / (1 - pad_xfrac) if right_gutter
                else (tgt - pad_xfrac) / (1 - 2 * pad_xfrac))
    box_w = (1 - h_margin - right_gutter) if right_gutter else (1 - 2 * h_margin)
    m_in = margin_in
    header_in = (title_pt + 0.5 * title_pt + sub_pt) / 72.0
    top_band_in = header_in + 2 * m_in
    if legend:
        bot_band_in = leg_in
    elif caption:
        bot_band_in = cap_in                      # a slim band for a descriptive caption line
    elif cbar and cbar_pos == "bottom":
        bot_band_in = 2 * m_in + cbar_band        # side-margin above the bar AND below its label
    else:
        bot_band_in = m_in
    H = 9.0
    for _ in range(20):
        box_h = (1 - (top_band_in + bot_band_in) / H) / (1 - 2 * pad_yfrac)
        H = (box_w * width) / (aspect * box_h)
    box_h = (1 - (top_band_in + bot_band_in) / H) / (1 - 2 * pad_yfrac)
    bot_margin = bot_band_in / H - pad_yfrac * box_h
    fig = plt.figure(figsize=(width, H), facecolor=KICK["figure"])
    ax = fig.add_axes([h_margin, bot_margin, box_w, box_h]); ax.set_facecolor(KICK["figure"])
    pitch.draw(ax=ax)
    x_lo, x_hi, y_lo, y_hi = bounds                       # touchline bounds in DRAWN coords
    ax.add_patch(Rectangle((x_lo, y_lo), x_hi - x_lo, y_hi - y_lo,
                           facecolor=KICK["panel"], edgecolor="none", zorder=0.5))
    ax._kick_bounds = bounds
    ax._kick_data0 = (len(ax.lines), len(ax.collections))   # everything after this is DATA — see kick_clip
    ax._kick_cbar_pos = cbar_pos if cbar else None
    return pitch, fig, ax


def kick_legend(fig, ax, ncol=None):
    """Legend in the band under the pitch, its lowest INK on the golden margin (mirrors the title band).
    Auto-wraps to fewer columns / more rows if long labels would overflow the pitch width, so any label
    length displays correctly. Centring the box in the band (the old behaviour) floated the text ink to
    0.26" — pin the bottom and measure-and-shift, exactly as kick_flat_legend(loc="bottom") does."""
    fig.canvas.draw()
    x_lo, x_hi, y_lo, y_hi = ax._kick_bounds
    figc = fig.transFigure.inverted().transform(
        ax.transData.transform([(x_lo, y_lo), (x_hi, y_lo), (x_lo, y_hi), (x_hi, y_hi)]))
    xmid = figc[:, 0].mean()
    avail = figc[:, 0].max() - figc[:, 0].min()          # pitch width (figure fraction)
    yy = KICK_MARGIN_IN / fig.get_size_inches()[1]
    handles, labels = ax.get_legend_handles_labels()
    cols = ncol or len(labels)
    while True:
        leg = ax.legend(handles, labels, loc="lower center", bbox_to_anchor=(xmid, yy),
                        bbox_transform=fig.transFigure, ncol=cols, columnspacing=1.8,
                        borderpad=0, borderaxespad=0)    # no inner pad → the shift lands on the TEXT ink
        fig.canvas.draw()
        if cols <= 1 or leg.get_window_extent().transformed(fig.transFigure.inverted()).width <= avail:
            break
        leg.remove(); cols -= 1
    b = leg.get_window_extent(fig.canvas.get_renderer()).transformed(fig.transFigure.inverted())
    leg.set_bbox_to_anchor((xmid, yy + (yy - b.y0)), transform=fig.transFigure)
    return leg


def kick_swatch(color, label, alpha=0.32, lw=2):
    """Legend handle for a filled curve / area series (the Curves form): a square swatch whose OUTLINE is
    the line colour and whose translucent fill echoes the area under the curve — truer than a bare line.
    Pair with square handles: ax.legend(handles=[kick_swatch(KICK["home"], "Home")], handlelength=1.3,
    handleheight=1.3). (alpha is a touch above the on-chart area fill so it reads in the small swatch.)"""
    return Patch(facecolor=to_rgba(color, alpha), edgecolor=color, linewidth=lw, label=label)


def kick_header_legend(fig, ax, handles=None, labels=None, **kw):
    """Park the legend in the top-right of the HEADER band (to the right of the centred title/subtitle),
    freeing the whole plot area so data reaching the axes edges (end-of-axis spikes) is never covered —
    the default placement for non-pitch line/area charts. Call AFTER kick_title(..., pitch=False). Extra
    kwargs (handlelength, handleheight, ncol, ...) pass through to ax.legend."""
    fig.canvas.draw()
    pos = ax.get_position()
    if handles is None:
        handles, labels = ax.get_legend_handles_labels()
    if labels is None:
        labels = [h.get_label() for h in handles]        # read labels off the handles (e.g. kick_swatch)
    opts = dict(loc="center right", bbox_to_anchor=(pos.x1, (pos.y1 + 1.0) / 2),
                bbox_transform=fig.transFigure,
                borderpad=0.0,        # trim inner padding; the shift below nails the exact right edge
                labelspacing=0.85)    # a touch more air between rows
    opts.update(kw)
    leg = ax.legend(handles, labels, **opts)
    fig.canvas.draw()                    # pin the legend's ACTUAL right edge to the axes-right (longest label)
    r = leg.get_window_extent().transformed(fig.transFigure.inverted()).x1
    leg.set_bbox_to_anchor((2 * pos.x1 - r, (pos.y1 + 1.0) / 2), transform=fig.transFigure)
    return leg


def kick_inside_legend(ax, handles=None, labels=None, loc="best", **kw):
    """Legend placed INSIDE the plot — for 3+ series, where the header band (~2 rows) would overflow.
    Sits in the emptiest corner (loc="best") on a subtle semi-transparent figure-tone panel (no border)
    so it stays readable if it falls over faint data. Use the house swatch handles for area/curve charts."""
    if handles is None:
        handles, labels = ax.get_legend_handles_labels()
    if labels is None:
        labels = [h.get_label() for h in handles]
    opts = dict(loc=loc, frameon=True, framealpha=0.85, facecolor=KICK["figure"], edgecolor="none",
                labelspacing=0.7, borderpad=0.8, handlelength=1.3, handleheight=1.3)
    opts.update(kw)
    return ax.legend(handles, labels, **opts)


def kick_flat_legend(fig, handles, labels=None, loc="bottom", ncol=None, fontsize=13, y=None):
    """FLAT (single-row) shared legend — the house DEFAULT placement for a multi-series or small-multiple
    chart. `loc="bottom"` (default) centres it UNDERNEATH the plot with its lower edge on the house margin
    (reserve the room with `kick_grid_header(legend_band=…)` for a non-pitch grid, or `kick_grid(legend_band=…)`
    for a pitch grid). Override with `loc="top-left"`/`"upper right"`/any Matplotlib loc if the user prefers.
    `handles` are the legend handles (labels read off them if not given); it is laid out in ONE row (`ncol`
    defaults to the number of entries) so it never stacks tall enough to crowd panel titles."""
    if labels is None:
        labels = [h.get_label() for h in handles]
    ncol = ncol or (1 if loc == "top-left" else len(handles))   # top-left stacks vertically; bottom runs flat
    kw = dict(ncol=ncol, frameon=False, fontsize=fontsize, labelcolor=W(0.72),
              columnspacing=2.0, handletextpad=0.6, borderpad=0)   # no inner pad → the TEXT ink,
    #   not the (invisible) frame box, is what the measure-and-shift lands on the golden margin
    Wf, Hf = fig.get_size_inches()
    if loc == "bottom":
        yy = (KICK_MARGIN_IN / Hf) if y is None else y            # lower edge on the house margin
        leg = fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, yy),
                         borderaxespad=0, **kw)
        fig.canvas.draw()                                         # then pin the legend's TRUE bottom to the
        inv = fig.transFigure.inverted()                         # margin (its internal pad otherwise floats it
        b = leg.get_window_extent(fig.canvas.get_renderer()).transformed(inv)   # ~0.09" high, eating the margin
        leg.set_bbox_to_anchor((0.5, yy + (yy - b.y0)))
        return leg
    if loc == "top-left":
        return fig.legend(handles, labels, loc="upper left",
                          bbox_to_anchor=(KICK_MARGIN_IN / Wf, 1 - KICK_MARGIN_IN / Hf), **kw)
    return fig.legend(handles, labels, loc=loc, **kw)


def kick_reserve_legend(ax, leg, pad=0.05, min_target=0.30, dmax=None):
    """Raise the top y-limit JUST enough that an upper-corner legend clears the data BENEATH it — measured
    within the legend's OWN x-span, not globally. So a legend sitting over the low tails of left-peaked
    curves (or short right-hand bars) lets the data stay TALL, and every panel self-adjusts by its own
    legend + local data — a 3-series and a 6-series do NOT get forced onto the same y-scale. No-op if the
    legend already clears. `dmax` is a fallback if nothing is found under the legend. Call after the final
    layout, with the legend at loc='upper right'/'upper left'/'upper center'. Returns the new y-top."""
    fig = ax.figure; fig.canvas.draw()
    axinv = ax.transAxes.inverted(); datinv = ax.transData.inverted()
    lb = leg.get_window_extent()
    fbot = lb.transformed(axinv).y0                                   # legend bottom edge, axes fraction
    lo = datinv.transform((lb.x0, lb.y0))[0]; hi = datinv.transform((lb.x1, lb.y0))[0]
    lo, hi = min(lo, hi), max(lo, hi)
    vmax = 0.0                                                        # tallest DATA under the legend's x-span
    for ln in ax.get_lines():
        xd = np.asarray(ln.get_xdata(), float); yd = np.asarray(ln.get_ydata(), float)
        if xd.size:
            m = (xd >= lo) & (xd <= hi)
            if m.any(): vmax = max(vmax, float(np.nanmax(yd[m])))
    for p in ax.patches:                                             # bars
        if isinstance(p, Rectangle):
            x0, x1 = p.get_x(), p.get_x() + p.get_width()
            if x1 >= lo and x0 <= hi: vmax = max(vmax, p.get_y() + p.get_height())
    if vmax == 0.0 and dmax is not None:
        vmax = dmax
    y0, y1 = ax.get_ylim()
    target = max(min_target, fbot - pad)                             # local data must sit below this fraction
    need = y0 + (vmax - y0) / target
    if need > y1:
        ax.set_ylim(y0, need)
    return ax.get_ylim()[1]


def kick_caption(fig, ax, text, size=14):
    """A muted descriptive line centred below the plot (where a legend/colourbar would otherwise sit) —
    a home for 'how to read this' notation, so the subtitle stays data-context. Its BOTTOM edge keeps the
    house margin above the image edge, and the reserved `cap_in` band leaves the same margin above it (so
    the footnote is inset top AND bottom by the standard margin). On a pitch, draw with caption=True."""
    fig.canvas.draw()
    Hf = fig.get_size_inches()[1]
    if hasattr(ax, "_kick_bounds"):
        x_lo, x_hi, y_lo, y_hi = ax._kick_bounds
        figc = fig.transFigure.inverted().transform(
            ax.transData.transform([(x_lo, y_lo), (x_hi, y_lo), (x_lo, y_hi), (x_hi, y_hi)]))
        xmid = figc[:, 0].mean()
    else:
        pos = ax.get_position(); xmid = (pos.x0 + pos.x1) / 2
    return fig.text(xmid, KICK_MARGIN_IN / Hf, text, ha="center", va="bottom", fontsize=size, color=W(0.55))


def _badge_number(ax, x, y, txt, size_pt, color, zorder):
    """A number centred on its INK at data point (x,y), sized `size_pt` POINTS (screen) — same optical
    centring as the checker chip (TextPath outline + get_extents, with the '1' stem fix), so it sits dead
    centre in the badge. Robust to the axes being resized/repositioned afterwards (e.g. by kick_title)."""
    tp = TextPath((0, 0), txt, size=1.0, prop=fm.FontProperties(family=KICK_FONT, weight="bold"))
    bb = tp.get_extents()
    cx = (bb.x0 + bb.x1) / 2; cy = (bb.y0 + bb.y1) / 2
    if txt == "1":                                                   # its flag drags the ink centre off the stem
        xs1 = np.linspace(bb.x0, bb.x1, 48)
        gx1, gy1 = np.meshgrid(xs1, np.linspace(bb.y0, bb.y1, 48))
        colc = tp.contains_points(np.column_stack([gx1.ravel(), gy1.ravel()])).reshape(48, 48).sum(0)
        if colc.max(): stem = xs1[colc >= 0.9 * colc.max()]; cx = (stem.min() + stem.max()) / 2
    tr = (mtransforms.Affine2D().translate(-cx, -cy).scale(size_pt / 72.0)   # em → inches at size_pt
          + ax.figure.dpi_scale_trans                                       # inches → display px (size in points)
          + mtransforms.ScaledTranslation(x, y, ax.transData))             # → the data point (re-evaluated on draw)
    ax.add_patch(PathPatch(tp, transform=tr, facecolor=color, edgecolor="none", zorder=zorder))


def _two_tone_label(ax, x, y, dim_txt, bright_txt, ha="center", va="baseline",
                    off_pts=(0, 0), fontsize=10, dim=None, bright=None, zorder=6):
    """A two-tier inline label at data (x, y): a DIM prefix (e.g. a low-priority jersey number) + a BRIGHT
    name, packed on ONE line via offsetbox so the two opacities read as a hierarchy. `off_pts` = (dx, dy)
    offset in POINTS; ha/va anchor the whole box (matches ax.text semantics)."""
    from matplotlib.offsetbox import TextArea, HPacker, AnnotationBbox
    dim = dim or W(0.45); bright = bright or W(0.90)
    a = TextArea(dim_txt, textprops=dict(color=dim, fontsize=fontsize))
    b = TextArea(bright_txt, textprops=dict(color=bright, fontsize=fontsize))
    box = HPacker(children=[a, b], align="baseline", pad=0, sep=3)
    bx = {"left": 0.0, "center": 0.5, "right": 1.0}[ha]
    by = {"bottom": 0.0, "baseline": 0.0, "center": 0.5, "top": 1.0}[va]
    ax.add_artist(AnnotationBbox(box, (x, y), xybox=off_pts, xycoords="data", boxcoords="offset points",
                                 frameon=False, pad=0, box_alignment=(bx, by), zorder=zorder))


def kick_smart_labels(ax, xy, labels, eps=None, tight=4, accent=None,
                      key_loc="lower left", key_title="Clusters", off=None):
    """Label scatter points while DE-COLLIDING clusters (a hybrid). Proximity-groups the points
    (single-linkage, Euclidean distance ≤ `eps` in DATA units — call AFTER the axis limits / inversion are
    set), then labels each group by its density:
      • TIGHT  (≥ `tight`, default 4) → numbered gold badges, mapped in a key box in a chart corner;
      • SMALL  (2 .. tight-1)         → displaced labels fanned out from the group centre + short connectors;
      • ISOLATED (1)                 → a plain label just above the dot.
    `eps`/`off` default to a fraction of the data span; `accent` defaults to the house gold. Badges are
    numbered visual-top → bottom. Returns the key list [(n, label), …]."""
    accent = accent or KICK["accent"]
    xy = np.asarray(xy, float); n = len(xy)
    span = float(np.hypot(*(xy.max(0) - xy.min(0)))) if n > 1 else 1.0
    if eps is None: eps = 0.09 * span
    if off is None: off = 0.05 * span
    parent = list(range(n))
    def find(a):
        while parent[a] != a: parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for i in range(n):
        for j in range(i + 1, n):
            if np.hypot(*(xy[i] - xy[j])) <= eps: parent[find(i)] = find(j)
    groups = {}
    for i in range(n): groups.setdefault(find(i), []).append(i)
    key = []; num = 0
    ysign = 1 if ax.yaxis_inverted() else -1                        # visual top = smaller y when inverted
    for g in sorted(groups.values(), key=lambda g: ysign * xy[g][:, 1].mean()):
        if len(g) >= tight:                                        # numbered badges + key
            for idx in sorted(g, key=lambda k: (ysign * xy[k, 1], xy[k, 0])):
                num += 1
                ax.scatter(*xy[idx], s=250, c=accent, edgecolors="#14120A", linewidths=1.0, zorder=6)
                _badge_number(ax, xy[idx, 0], xy[idx, 1], str(num), 13, "#14120A", 7)   # optically centred
                key.append((num, labels[idx]))
        elif len(g) >= 2:                                          # displaced labels + connectors
            c = xy[g].mean(0)
            gap = 0.22 * off                                       # equal breathing room at BOTH ends of the
            for idx in g:                                          # connector — off the dot AND off the name
                d = xy[idx] - c; d = d / (np.hypot(*d) + 1e-9)
                lx, ly = xy[idx] + d * off                         # label anchor
                s0 = xy[idx] + d * gap                             # start a gap out from the dot
                s1 = np.array([lx, ly]) - d * gap                  # stop a matching gap short of the name
                ax.plot([s0[0], s1[0]], [s0[1], s1[1]], color=accent, lw=0.8, alpha=0.7, zorder=2)
                lab = labels[idx]; lha = "left" if d[0] >= 0 else "right"
                if isinstance(lab, tuple):                          # (dim prefix, bright name) → two-tone
                    _two_tone_label(ax, lx, ly, lab[0], lab[1], ha=lha, va="center", fontsize=10)
                else:
                    ax.text(lx, ly, lab, ha=lha, va="center", fontsize=10, color=W(0.82), zorder=6)
        else:                                                      # isolated → direct label
            idx = g[0]; lab = labels[idx]
            if isinstance(lab, tuple):                              # (dim prefix, bright name) → two-tone
                _two_tone_label(ax, xy[idx, 0], xy[idx, 1], lab[0], lab[1], ha="center", va="bottom",
                                off_pts=(0, 14), fontsize=10)        # clear the dot with a gap
            else:
                ax.annotate(lab, xy[idx], xytext=(0, 14), textcoords="offset points",
                            ha="center", fontsize=10, color=W(0.82), zorder=6)   # clear the dot with a gap
    if key:
        # anchor at a corner, then offset by EQUAL POINTS on both axes (not axes-fraction, which differs in
        # x vs y on a non-square axes → the box would sit farther from one axis than the other)
        corner = {"lower left": (0, 0, "left", "bottom", 1, 1), "lower right": (1, 0, "right", "bottom", -1, 1),
                  "upper left": (0, 1, "left", "top", 1, -1), "upper right": (1, 1, "right", "top", -1, -1)}
        fx, fy, ha, va, sx, sy = corner.get(key_loc, corner["lower left"])
        pad = 18.0                                                   # equal points from each axis (~3× the old 10pt gap)
        tr = ax.transAxes + mtransforms.ScaledTranslation(sx * pad / 72, sy * pad / 72, ax.figure.dpi_scale_trans)
        lines = [key_title] + [f"{k}  {(' '.join(lab) if isinstance(lab, tuple) else lab)}" for k, lab in key]
        ax.text(fx, fy, "\n".join(lines), transform=tr, ha=ha, va=va, fontsize=10.5,
                color=W(0.82), zorder=7, linespacing=1.5,
                bbox=dict(boxstyle="round,pad=0.5", fc="#14120A", ec=accent, lw=1.2))
    return key


# ── magnitude-surface helpers: two options (grid heatmap / contour) ────────────
def kick_heatmap(ax, x_edges, y_edges, z, cmap=KICK_SEQ, edge=False):
    """Grid-cell heatmap (blocky zones) — default for threat / xT surfaces. Cells abut with no
    separator (edge=False) so the surface reads clean; pass edge=True for thin figure-tone gridlines."""
    return ax.pcolormesh(x_edges, y_edges, z, cmap=cmap, alpha=0.92, zorder=1,
                         edgecolors=(KICK["figure"] if edge else "face"),
                         linewidth=(0.6 if edge else 0))

def kick_contour(ax, xs, ys, z, levels=12, cmap=KICK_SEQ, vmin=None, vmax=None):
    """Filled contour surface (smooth bands) — default for control fields."""
    gx, gy = np.meshgrid(xs, ys)
    kw = {} if vmin is None else dict(vmin=vmin, vmax=vmax)
    return ax.contourf(gx, gy, z, levels=levels, cmap=cmap, alpha=0.92, zorder=1, **kw)


# ── node marks: the beveled "checker" chip (pass-network node) ──────────
def _shade(hx, f):    # darken toward black
    return tuple(c * f for c in to_rgb(hx))

def _lighten(hx, f):  # lift toward white
    return tuple(c + (1 - c) * f for c in to_rgb(hx))

def _lum(c):          # perceived luminance of an (r,g,b) 0-1 tuple
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]

def _bevel(color):
    """The chip's three layers — rim (shadow), main (body), highlight (cap) — with a visible bevel for ANY
    base. Normal colours lift a lighter cap. A light/near-WHITE base has no room to lighten (cap would equal
    the body), so instead the BODY is dropped and the cap becomes the lightest layer: dark rim → grey body →
    white cap. Keeps the poker-chip read for white teams."""
    base, hi = to_rgb(color), _lighten(color, 0.34)
    if _lum(hi) - _lum(base) < 0.10:                          # not enough headroom → light/white base
        return _shade(color, 0.60), _shade(color, 0.88), base  # rim · body-down · cap = base (the lightest)
    return _shade(color, 0.5), base, hi                        # normal · rim · body · lifted cap

def _num_col(color):  # white number, or dark on a light chip (keeps the bevel readable)
    return "#2B2B2B" if _lum(to_rgb(color)) > 0.70 else "#FFFFFF"

def kick_checker(ax, x, y, r, color, number=None, name=None, num_size=None, name_size=13,
                 name_gap=1.6, name_weight="normal", fail_angle=None, fail_ratio=0.0,
                 zorder=10, shadow=(0.10, 0.14)):
    """Beveled poker-chip node — a soft offset shadow, a white-rimmed dark rim, the main (team) colour,
    then a lighter highlight cap, an optional centred number, and an optional player-name label in a
    rounded black pill ABOVE the chip (the pass-network nametag). `r`/`name_gap` in pitch-data
    units; `color` the base team hex. Chip size and edge width are set FREELY (continuous) — no discrete
    tiers. Layers: rim r · main 0.86r · highlight 0.62r, shadow 1.06r; rim = base×0.5, highlight = base
    lifted 34% to white. The number is a glyph OUTLINE centred on its ink bounds (exact optical centre,
    not font metrics), auto-sized in r with 2-digit numbers smaller so they fit the same chip; num_size
    overrides the digit height (pitch units).

    Optional 'crack' (fail-direction, ported from passing_network.ipynb's Wedge): pass fail_angle (deg,
    0=East/forward) + fail_ratio (0..1). Rather than a dirty black overlay, it NOTCHES the red middle
    ring in that direction and fills it with the chip's own OUTER (brown/rim) tone — so the outer band
    appears to dip inward, no new colour, pink centre and white edge kept. Arc width ∝ fail rate."""
    rim, main, hi = _bevel(color)                             # adaptive: handles white (no lighter cap) too
    ax.add_patch(Circle((x + shadow[0] * r, y + shadow[1] * r), r * 1.06,
                        facecolor="black", edgecolor="none", alpha=0.28, zorder=zorder - 0.5))
    ax.add_patch(Circle((x, y), r,        facecolor=rim,  edgecolor="white", linewidth=1.1, zorder=zorder))
    ax.add_patch(Circle((x, y), r * 0.86, facecolor=main, edgecolor="none", zorder=zorder + 0.1))
    ax.add_patch(Circle((x, y), r * 0.62, facecolor=hi,   edgecolor="none", zorder=zorder + 0.2))
    if fail_angle is not None and fail_ratio > 0:
        sweep = min(fail_ratio, 0.6) * 360                    # arc ∝ fail rate (capped so it never eats the chip)
        ax.add_patch(Wedge((x, y), r * 0.86, fail_angle - sweep / 2, fail_angle + sweep / 2,
                           width=r * 0.24, facecolor=rim, edgecolor="none", zorder=zorder + 0.25))
    if number is not None:
        s = str(number)                                       # glyph OUTLINE centred on its TRUE bbox
        tp = TextPath((0, 0), s, size=1.0,
                      prop=fm.FontProperties(family=KICK_FONT, weight="bold"))
        bb = tp.get_extents()                                 # get_extents ignores CLOSEPOLY (0,0) placeholder
        cx = (bb.x0 + bb.x1) / 2; cy = (bb.y0 + bb.y1) / 2    # verts that skewed raw-vertex x-centring
        gh, gw = bb.height, bb.width
        if s == "1":                                          # "1" is special: its top flag drags the ink centre
            xs1 = np.linspace(bb.x0, bb.x1, 48)               # left of the STEM. Rasterise + centre on the
            gx1, gy1 = np.meshgrid(xs1, np.linspace(bb.y0, bb.y1, 48))   # full-height stem columns, not the flag
            col = tp.contains_points(np.column_stack([gx1.ravel(), gy1.ravel()])).reshape(48, 48).sum(0)
            if col.max():
                stem = xs1[col >= 0.9 * col.max()]
                cx = (stem.min() + stem.max()) / 2
        target_h = num_size or r * (0.82 if len(s) < 2 else 0.62)   # 2-digit smaller so it fits the SAME chip
        scale = target_h / gh
        if gw * scale > r * 1.4:                              # keep a wide number inside the chip
            scale = r * 1.4 / gw
        ysign = -1.0 if ax.yaxis_inverted() else 1.0          # counter the pitch's inverted y-axis (else upside-down)
        tr = mtransforms.Affine2D().translate(-cx, -cy).scale(scale, scale * ysign).translate(x, y) + ax.transData
        ax.add_patch(PathPatch(tp, transform=tr, facecolor=_num_col(main), edgecolor="none",
                               zorder=zorder + 0.3))
    if name is not None:
        # keep the pill BELOW the chip with a `name_gap` gap in BOTH orientations: on a horizontal pitch
        # the y-axis is inverted (va="bottom" grows the pill up, away from the chip), but on a vertical
        # pitch it is NOT inverted, so va="top" is needed or the pill would grow up INTO the chip.
        below_va = "bottom" if ax.yaxis_inverted() else "top"
        t = ax.text(x, y - r - name_gap, name, color="#F4F4F4", fontsize=name_size, fontweight=name_weight,
                    ha="center", va=below_va, zorder=zorder + 2,
                    bbox=dict(boxstyle="round,pad=0.35", fc="#0C0C0C", ec=W(0.60), lw=1.0))
        t.set_path_effects([pe.withStroke(linewidth=2.4, foreground="#1C1C1C")])


# ── node-attached event icons (golden-rule standard) ──────────────────────────
# One vocabulary of small badges pinned to player nodes (substitutions now; goals / assists / cards to
# come). GOLDEN RULE for these: a FIXED size (NODE_ICON_R — the same on every node, so they never look
# lopsided), placed at the node's visual TOP-RIGHT with the inner edge on the centre-colour boundary
# (NODE_ICON_EDGE·r) — so an icon steps onto the outer rings but NEVER covers the jersey number, at any
# node size. Each icon = a coloured disc + an ink-centred white glyph. Extend by adding to KICK_ICONS.
KICK_ICONS = {
    "sub_on":  {"color": KICK["green"],  "glyph": "→"},   # came on
    "sub_off": {"color": KICK["danger"], "glyph": "←"},   # subbed off
    "goal":    {"color": KICK["ball"],   "glyph": ""},    # a ball (placeholder — refine markings later)
    "assist":  {"color": KICK["teal"],   "glyph": "A"},   # placeholder — refine glyph later
}


def _icon_glyph(ax, cx, cy, size, glyph, color="white", zorder=13):
    """A glyph drawn as a TextPath OUTLINE, ink-centred on (cx, cy) via get_extents — TRUE optical centring
    (like the chip number); matplotlib's font-metric va/ha centring leaves a glyph visibly off. `size` is
    the target of the glyph's LARGER dimension in DATA units, so wide arrows and tall letters both fit."""
    tp = TextPath((0, 0), glyph, size=1.0, prop=fm.FontProperties(family=KICK_FONT, weight="bold"))
    bb = tp.get_extents()
    gcx, gcy = (bb.x0 + bb.x1) / 2, (bb.y0 + bb.y1) / 2
    scale = size / max(bb.width, bb.height, 1e-6)
    ysign = -1.0 if ax.yaxis_inverted() else 1.0            # counter an inverted (horizontal) pitch y-axis
    tr = (mtransforms.Affine2D().translate(-gcx, -gcy).scale(scale, scale * ysign).translate(cx, cy)
          + ax.transData)
    ax.add_patch(PathPatch(tp, transform=tr, facecolor=color, edgecolor="none", zorder=zorder))


def kick_node_icon(ax, x, y, r, icon, label=None, slot=0, rho=NODE_ICON_R):
    """Pin a house event icon to a player node (see kick_checker) — the golden-rule node-icon standard: a
    FIXED-size coloured disc (`rho` = NODE_ICON_R pitch units, the SAME on every node) at the node's visual
    TOP-RIGHT, its inner edge on the centre-colour boundary (NODE_ICON_EDGE·r) so it never covers the
    number. `icon` is a KICK_ICONS key (sub_on/sub_off/goal/assist/…) or a {color, glyph} dict; optional
    `label` (e.g. a minute) sits to the right; `slot` (0,1,2…) stacks multiple icons outward along the
    diagonal. Works on horizontal AND vertical pitches (top-right honours the y-axis inversion). Returns
    the icon centre (bx, by)."""
    spec = KICK_ICONS[icon] if isinstance(icon, str) else icon
    ysign = -1.0 if ax.yaxis_inverted() else 1.0
    d = NODE_ICON_EDGE * r + rho + slot * (2 * rho + 0.4)
    bx, by = x + d / 2 ** 0.5, y + ysign * d / 2 ** 0.5     # visual top-right (honours inversion)
    ax.add_patch(Circle((bx, by), rho, facecolor=spec["color"], edgecolor="white", linewidth=1.3, zorder=12))
    if spec.get("glyph"):
        _icon_glyph(ax, bx, by, 1.28 * rho, spec["glyph"], "white", 13)   # glyph ~5% smaller than the disc-fit
    if label is not None:
        ax.text(bx + rho + 0.8, by, label, ha="left", va="center", fontsize=8.5,
                fontweight="bold", color=spec["color"], zorder=13)
    return bx, by


# ── small-multiples: a grid of house pitches for comparisons ───────────────────
def kick_grid(nrows, ncols, vertical=False, line_zorder=2, pad=2, width=13.0,
              col_gap=0.30, row_gap=0.44, panel_label=0.46,
              title_pt=20, sub_pt=18, cbar=False, cbar_pos="right", cbar_gutter=0.6, cbar_band=0.74,
              pitch_type="statsbomb", legend_band=0.0, **pitch_kw):
    """Grid of house pitches for small-multiple comparisons. Returns (pitch, fig, axes[nrows, ncols]).
    Reserve the overall header with kick_grid_title(fig, axes, ...); label each panel with
    kick_panel_label(ax, ...); a shared colourbar via cbar=True + kick_grid_cbar(...): cbar_pos="right"
    (a slim vertical bar in a right gutter) or "bottom" (a horizontal bar centred UNDER the grid with the
    label beneath, like the single pitch). Gaps in inches. Outer touchline margin solved to KICK_MARGIN_IN.
    `pitch_type` passes through to the pitch (statsbomb / wyscout / opta / …); the layout adapts to the
    drawn pitch extents, so any coordinate system works."""
    pitch = kick_pitch(pitch_type, vertical, line_zorder, pad=pad, **pitch_kw)
    tf, ta = pitch.draw(figsize=(4, 4))
    xr = abs(np.diff(ta.get_xlim())[0]); yr = abs(np.diff(ta.get_ylim())[0])
    aspect = xr / (yr * ta.get_aspect())    # true display aspect (get_aspect≠1 for wyscout/opta 100×100)
    bounds, pad_x, pad_y = _touchlines(pitch, vertical, ta.get_xlim(), ta.get_ylim(), pad)
    plt.close(tf)
    pad_xfrac = pad_x / xr
    m_in = KICK_MARGIN_IN                                     # same outer touchline margin as every other chart
    gutter = cbar_gutter if (cbar and cbar_pos == "right") else 0.0   # right gutter only for a right colourbar
    free = width - gutter - (ncols - 1) * col_gap
    side = (m_in - pad_xfrac * free / ncols) / (1 - 2 * pad_xfrac / ncols)   # panel margin so outer == m_in
    pitch_w = (width - 2 * side - gutter - (ncols - 1) * col_gap) / ncols
    pitch_h = pitch_w / aspect
    header = (title_pt + 0.5 * title_pt + sub_pt) / 72.0 + 2 * m_in   # band = header text + 2 true margins,
    #   so the centred header leaves exactly m_in above it (matches draw_kick_pitch; NOT the panel inset `side`)
    extra_bottom = (m_in + cbar_band) if (cbar and cbar_pos == "bottom") else 0.0   # band below the grid for a bottom bar
    extra_bottom += legend_band                                    # strip for a flat bottom legend (kick_flat_legend)
    H = header + nrows * (panel_label + pitch_h) + (nrows - 1) * row_gap + side + extra_bottom
    fig = plt.figure(figsize=(width, H), facecolor=KICK["figure"])
    axes = np.empty((nrows, ncols), dtype=object)
    for r in range(nrows):
        row_top = H - header - r * (panel_label + pitch_h + row_gap)
        py = row_top - panel_label - pitch_h
        for c in range(ncols):
            px = side + c * (pitch_w + col_gap)
            ax = fig.add_axes([px / width, py / H, pitch_w / width, pitch_h / H])
            ax.set_facecolor(KICK["figure"]); pitch.draw(ax=ax)
            x_lo, x_hi, y_lo, y_hi = bounds                # touchline bounds in DRAWN coords
            ax.add_patch(Rectangle((x_lo, y_lo), x_hi - x_lo, y_hi - y_lo,
                                   facecolor=KICK["panel"], edgecolor="none", zorder=0.5))
            ax._kick_bounds = bounds; ax._kick_panel = panel_label / H
            ax._kick_data0 = (len(ax.lines), len(ax.collections))   # see kick_clip
            ax._kick_above = (m_in if r == 0 else row_gap) / H   # gap ABOVE the label band (header vs row-gap)
            axes[r, c] = ax
    fig._kick_header_frac = header / H
    fig._kick_grid_cbar_pos = cbar_pos if cbar else None
    return pitch, fig, axes


def kick_panel_label(ax, label, size=16, weight="normal"):
    """Small label above a grid panel, **vertically centred in the whole gap between the panel's pitch and
    what sits above it** (the header for the top row, the row-gap for lower rows) — NOT just in its own
    label band, so it never crowds the pitch top. Regular weight by default: bold is reserved for the one
    overall grid title (kick_grid_title), so panel labels stay subordinate to it."""
    fig = ax.figure; fig.canvas.draw()
    x_lo, x_hi, y_lo, y_hi = ax._kick_bounds
    figc = fig.transFigure.inverted().transform(       # all 4 corners -> true visual top (y-axis may invert)
        ax.transData.transform([(x_lo, y_lo), (x_lo, y_hi), (x_hi, y_lo), (x_hi, y_hi)]))
    top, xmid = figc[:, 1].max(), figc[:, 0].mean()
    above = getattr(ax, "_kick_above", KICK_MARGIN_IN / fig.get_size_inches()[1])
    gap = ax._kick_panel + above                       # pitch-top → (subtitle / row above) span
    fig.text(xmid, top + gap * 0.5, label, ha="center", va="center",
             fontsize=size, fontweight=weight, color=W(0.90))


def kick_tiered_title(ax, segments, pad=13, fontsize=None, weight="normal", sep=5, zorder=6):
    """A per-panel title split into brightness TIERS on ONE centred line via offsetbox — e.g. a DIM jersey
    number + a BRIGHT name + a DIM role, so the eye lands on the name and the number/role stay subordinate
    (same hierarchy idea as _two_tone_label, but as a centred panel title). `segments` is a list of
    (text, alpha). Sits `pad` points above the axes top, matching the spacing of ax.set_title(pad=)."""
    from matplotlib.offsetbox import TextArea, HPacker, AnnotationBbox
    fs = fontsize if fontsize is not None else plt.rcParams["axes.titlesize"]
    tas = [TextArea(t, textprops=dict(color=W(a), fontsize=fs, fontweight=weight)) for t, a in segments]
    box = HPacker(children=tas, align="baseline", pad=0, sep=sep)
    ax.add_artist(AnnotationBbox(box, (0.5, 1.0), xybox=(0, pad), xycoords="axes fraction",
                                 boxcoords="offset points", frameon=False, pad=0,
                                 box_alignment=(0.5, 0.0), zorder=zorder))


def kick_tilt_big_ticks(axes, axis="y", min_digits=4, deg=45):
    """Tilt tick labels whose value carries >= `min_digits` digits (e.g. 1000, 2000 on a metres axis) by
    `deg`° CCW; smaller labels (0, single digits) stay flat, so the big numbers read on a slant and take less
    width. FREEZES the ticks (FixedFormatter) so the rotation survives later redraws — call BEFORE the grid
    header so its solved margin measures the slimmer slanted text."""
    axs = np.asarray(axes, dtype=object).ravel()
    fig = axs[0].figure; fig.canvas.draw()
    thr = 10 ** (min_digits - 1)
    for ax in axs:
        if not ax.get_visible():
            continue
        lo, hi = ax.get_ylim() if axis == "y" else ax.get_xlim()
        lo, hi = min(lo, hi), max(lo, hi)
        locs = ax.get_yticks() if axis == "y" else ax.get_xticks()
        labs = ax.get_yticklabels() if axis == "y" else ax.get_xticklabels()
        keep = [(t, l.get_text()) for t, l in zip(locs, labs) if l.get_text() and lo <= t <= hi]
        if not keep:
            continue
        (ax.set_yticks if axis == "y" else ax.set_xticks)([t for t, _ in keep])
        (ax.set_yticklabels if axis == "y" else ax.set_xticklabels)([c for _, c in keep])
        for (t, _), lbl in zip(keep, ax.get_yticklabels() if axis == "y" else ax.get_xticklabels()):
            if abs(t) >= thr:
                lbl.set_rotation(deg); lbl.set_rotation_mode("anchor")
                lbl.set_ha("right"); lbl.set_va("center" if axis == "y" else "top")


def kick_grid_title(fig, axes, title, subtitle=None, size=20, sub_size=18,
                    logo=True, logo_alpha=LOGO_ALPHA, logo_cap=0.26):
    """Overall header for a pitch grid: bold title + optional subtitle centred over the whole grid, with a
    small icon badge top-right on the top-right panel's touchline. The header TOP is pinned at the top margin
    (golden rule) — robust whether or not a subtitle is present, so the top margin is always KICK_MARGIN_IN."""
    fig.canvas.draw()
    tl, tr = axes[0, 0], axes[0, -1]
    L = fig.transFigure.inverted().transform(tl.transData.transform([(tl._kick_bounds[0], tl._kick_bounds[3])]))[0]
    R = fig.transFigure.inverted().transform(tr.transData.transform([(tr._kick_bounds[1], tr._kick_bounds[3])]))[0]
    xmid, right_x = (L[0] + R[0]) / 2, R[0]
    Wf, Hf = fig.get_size_inches()
    mv = KICK_MARGIN_IN / Hf
    th, sh = size / 72 / Hf, sub_size / 72 / Hf
    header_top = 1 - mv                                       # header top at the top margin
    fig.text(xmid, header_top, title, ha="center", va="top", fontsize=size, fontweight="bold", color=W(1.0))
    if subtitle:
        fig.text(xmid, header_top - th - 0.5 * th, subtitle, ha="center", va="top",
                 fontsize=sub_size, color=W(0.60))
        header_h = th + 0.5 * th + sh
    else:
        header_h = th
    _draw_logo(fig, right_x, header_top, header_h, logo, logo_alpha, logo_cap)   # top-right badge


def kick_grid_cbar(fig, axes, mappable, label, frac=0.5):
    """One shared colourbar for a pitch grid. Default (cbar_pos="right"): a slim VERTICAL bar in the right
    gutter. If the grid was built with cbar_pos="bottom": a HORIZONTAL bar centred BELOW the grid with the
    label underneath (matches the single-pitch below-pitch bar) — the bar sits a full margin under the grid,
    and the whole thing is shifted so the LABEL's bottom keeps a full margin above the image edge."""
    fig.canvas.draw()
    if getattr(fig, "_kick_grid_cbar_pos", None) == "bottom":
        inv = fig.transFigure.inverted()
        pts = np.vstack([inv.transform(ax.transData.transform(
            [(ax._kick_bounds[0], ax._kick_bounds[2]), (ax._kick_bounds[1], ax._kick_bounds[2]),
             (ax._kick_bounds[0], ax._kick_bounds[3]), (ax._kick_bounds[1], ax._kick_bounds[3])]))
            for ax in axes.flat])                                    # all panels' touchline corners → figure fraction
        bottom = pts[:, 1].min(); left = pts[:, 0].min(); right = pts[:, 0].max()
        xmid = (left + right) / 2; gw = right - left
        Hf = fig.get_size_inches()[1]; m_in = KICK_MARGIN_IN
        cw, bar_h = frac * gw, 0.13 / Hf
        cax = fig.add_axes([xmid - cw / 2, bottom - m_in / Hf - bar_h, cw, bar_h])
        cb = fig.colorbar(mappable, cax=cax, orientation="horizontal")
        cb.set_label(label, color=W(0.80), fontsize=14); cb.ax.xaxis.labelpad = 12
        cb.ax.tick_params(colors=W(0.55), labelsize=12); cb.outline.set_edgecolor(KICK["grid"])
        fig.canvas.draw()                                            # shift so the LABEL's bottom keeps a full margin
        lb = cb.ax.xaxis.label.get_window_extent().transformed(inv).y0
        p = cax.get_position(); cax.set_position([p.x0, p.y0 + (m_in / Hf - lb), p.width, p.height])
        _dim_units(fig, cb.ax.xaxis.label)            # quantity bright, unit recessive (golden rule)
        return cb
    tr, br = axes[0, -1].get_position(), axes[-1, -1].get_position()
    x = tr.x1 + 0.014
    y0 = br.y0 + br.height * 0.06; y1 = tr.y1 - tr.height * 0.06
    cax = fig.add_axes([x, y0, 0.010, y1 - y0])
    cb = fig.colorbar(mappable, cax=cax)
    cb.set_label(label, color=W(0.80), fontsize=14)
    cb.ax.tick_params(colors=W(0.55), labelsize=12)
    cb.outline.set_edgecolor(KICK["grid"])
    _dim_units(fig, cb.ax.yaxis.label)
    return cb


def kick_hide_origin_zero(ax, axis="y", fmt=None):
    """Only ONE zero at the origin: blank the y-axis's 0/0.0 (the x-axis '0' serves both corners), so two
    zeros don't over-print where the axes meet. For numeric charts whose axes start at 0. `fmt` formats the
    surviving labels — inferred as 1 decimal if any tick is fractional, else integer."""
    a = ax.yaxis if axis == "y" else ax.xaxis
    if fmt is None:
        frac = any(abs(t - round(t)) > 1e-6 for t in a.get_ticklocs())
        fmt = "{:.1f}" if frac else "{:.0f}"
    a.set_major_formatter(FuncFormatter(lambda v, _: "" if abs(v) < 1e-9 else fmt.format(v)))


def kick_grid_header(fig, axes, title, subtitle=None, xlabel=None, ylabel=None,
                     size=20, sub_size=18, hspace=0.66, wspace=0.16, panel_pad=13,
                     logo=True, logo_alpha=LOGO_ALPHA, logo_cap=0.26, margin_in=KICK_MARGIN_IN):
    """GOLDEN-RULE header + margins for a NON-PITCH subplot grid (plt.subplots). The single solved path so a
    grid can't drift: it sets subplots_adjust so every outer edge sits `margin_in` from the nearest ink
    (leftmost tick/label, lowest x-label, axes-right, header/logo top), draws the centred title+subtitle and
    the top-left icon, and — when every panel shares the metric — ONE shared axis label per axis (drawn once,
    not per-panel). Call AFTER plotting panel content + per-panel titles/legends."""
    Wf, Hf = fig.get_size_inches()
    ml, mv = margin_in / Wf, margin_in / Hf
    gap_h, gap_v = 0.12 / Wf, 0.12 / Hf                    # shared-label → tick-numbers gap
    th, sh = size / 72 / Hf, sub_size / 72 / Hf
    header_h = (th + 0.5 * th + sh) if subtitle else th
    label_band = (panel_pad + 16) / 72 / Hf + 0.015        # room above the top row for its panel titles
    top_ax = 1 - 2 * mv - header_h - label_band
    right = 1 - ml
    axes2 = np.atleast_2d(axes); left_col, bot_row, right_col = axes2[:, 0], axes2[-1, :], axes2[:, -1]
    fig.subplots_adjust(left=0.13, right=right, top=top_ax, bottom=0.16, hspace=hspace, wspace=wspace)
    fig.canvas.draw(); inv = fig.transFigure.inverted(); r = fig.canvas.get_renderer()
    def _tick_over(axs, which):                            # axes edge → outermost tick-label ink (a width)
        vals = []
        for ax in axs:
            e = ax.get_position()
            for t in (ax.get_yticklabels() if which == "y" else ax.get_xticklabels()):
                if not t.get_text():
                    continue
                b = t.get_window_extent(r).transformed(inv)
                vals.append((e.x0 - b.x0) if which == "y" else (e.y0 - b.y0))
        return max(vals) if vals else 0.0
    gy, hx = _tick_over(left_col, "y"), _tick_over(bot_row, "x")
    yl = xl = None; wy = wh = 0.0
    if ylabel:
        yl = fig.text(0.06, 0.5, ylabel, rotation=90, va="center", ha="center", fontsize=14, color=W(0.75))
        fig.canvas.draw(); b = yl.get_window_extent(r).transformed(inv); wy = b.x1 - b.x0
    if xlabel:
        xl = fig.text(0.5, 0.06, xlabel, va="center", ha="center", fontsize=14, color=W(0.75))
        fig.canvas.draw(); b = xl.get_window_extent(r).transformed(inv); wh = b.y1 - b.y0
    left = ml + (wy + gap_h if ylabel else 0.0) + gy
    bottom = mv + (wh + gap_v if xlabel else 0.0) + hx
    for _ in range(4):     # pull `right` in until the last x tick's ink — not the spine — sits on the margin
        fig.subplots_adjust(left=left, right=right, top=top_ax, bottom=bottom, hspace=hspace, wspace=wspace)
        fig.canvas.draw()
        over = _xtick_overhang(right_col, 1 - ml, inv, r)   # 0 when the tick is interior, or aspect-letterboxed
        if over <= 0.0015:
            break
        right -= over                                       # monotonic: `right` only ever narrows
    xmid = (left + right) / 2; header_top = 1 - mv
    fig.text(xmid, header_top, title, ha="center", va="top", fontsize=size, fontweight="bold", color=W(1.0))
    if subtitle:
        fig.text(xmid, header_top - th - 0.5 * th, subtitle, ha="center", va="top",
                 fontsize=sub_size, color=W(0.60))
    _draw_logo(fig, 1 - ml, header_top, header_h, logo, logo_alpha, logo_cap)   # top-right badge
    if yl is not None:
        yl.set_position((ml + wy / 2, (bottom + top_ax) / 2))    # ink flush to the left margin
    if xl is not None:
        xl.set_position(((left + right) / 2, mv + wh / 2))        # ink flush to the bottom margin
    for lab in (yl, xl):                                          # quantity bright, unit recessive
        if lab is not None:
            _dim_units(fig, lab)
    return {"left": left, "right": right, "top": top_ax, "bottom": bottom}


def kick_verify_margins(fig, target=KICK_MARGIN_IN, tol=0.02, label=""):
    """Enforcement teeth for the golden rule: measure the four outer margins (image edge → nearest ink), in
    inches, and print OK / WARN vs `target`. Pitches measure to the touchline (`_kick_bounds`); other axes to
    their tight bbox (ticks + labels); figure texts and the logo axes are included. Returns the four values."""
    fig.canvas.draw(); r = fig.canvas.get_renderer()
    Wf, Hf = fig.get_size_inches(); dpi = fig.dpi
    xs0, xs1, ys0, ys1 = [], [], [], []
    for ax in fig.axes:
        if hasattr(ax, "_kick_bounds"):
            x_lo, x_hi, y_lo, y_hi = ax._kick_bounds
            p = ax.transData.transform([(x_lo, y_lo), (x_hi, y_lo), (x_lo, y_hi), (x_hi, y_hi)])
            xs0.append(p[:, 0].min()); xs1.append(p[:, 0].max())
            ys0.append(p[:, 1].min()); ys1.append(p[:, 1].max())
        else:
            try:
                b = ax.get_tightbbox(r)
            except Exception:
                b = None
            if b is None or b.width == 0:
                continue
            xs0.append(b.x0); xs1.append(b.x1); ys0.append(b.y0); ys1.append(b.y1)
    for t in fig.texts:
        if not t.get_text().strip():
            continue
        b = t.get_window_extent(r)
        xs0.append(b.x0); xs1.append(b.x1); ys0.append(b.y0); ys1.append(b.y1)
    if not xs0:
        print(f"[margins ????] {label}: no content"); return None
    m = {"L": min(xs0) / dpi, "R": Wf - max(xs1) / dpi, "T": Hf - max(ys1) / dpi, "B": min(ys0) / dpi}
    bad = any(abs(v - target) > tol for v in m.values())
    print(f"[margins {'WARN' if bad else ' OK '}] {label:20s} " +
          " ".join(f"{k}={v:.3f}" for k, v in m.items()) + (f"   target={target}" if bad else ""))
    return m
