"""project_kick visualization style — the house design system.

Import in a notebook with:  from kick_style import *  ; then call apply_kick_style().
Colour by job (categorical teams / sequential magma / diverging team-poles), Inter type scale
(20/18/16/14, white-opacity tiers), dark pitch with a lighter touchline interior, logo header.
"""
import os, glob
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
KICK_DIV = LinearSegmentedColormap.from_list("kick_div", [KICK["away"], KICK["panel"], KICK["home"]])
KICK_STATUS = {"gain": KICK["green"], "noise": KICK["muted"], "loss": KICK["danger"]}
# categorical grouping order — assign, never cycle. Teams lead (orange/white); teal/purple are extra groups.
KICK_CAT = [KICK["home"], KICK["away"], KICK["teal"], KICK["purple"]]

def W(a): return "#FFFFFF%02X" % round(a * 255)          # white text at opacity a

KICK_MARGIN_IN = 0.36    # house outer inset (inches): image edge → pitch touchline / label / logo, everywhere
LOGO_ALPHA = 0.55        # brand-mark opacity, hard-locked (subtler than the data)
LOGO_SCALE = 0.70        # brand-mark height as a fraction of the header block (a small top-right badge)


def _load_logo(path="assets/logo_wordmark.png", icon_only=True):
    """Load the brand mark. icon_only=True (default) keeps ONLY the graphical 'KK' icon — the wordmark is
    trimmed to its ink, then cut at the first wide internal gap (the icon↔'PROJ. KICK' separator), leaving
    a clean, elegant square-ish mark for the chart corner."""
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
    "tick_pt":        12, "tick_opacity": 0.45,
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
    fig.subplots_adjust(left=ml + gy, right=1 - ml, top=top_ax, bottom=mv + hx)   # label-left = ml, x-label bot = mv
    fig.canvas.draw()
    pos = ax.get_position(); xmid = (pos.x0 + pos.x1) / 2
    header_top = 1 - mv                                   # logo + title top at the top margin
    fig.text(xmid, header_top, title, ha="center", va="top", fontsize=size, fontweight="bold", color=W(1.0))
    if subtitle:
        fig.text(xmid, header_top - th - 0.5 * th, subtitle, ha="center", va="top",
                 fontsize=sub_size, color=W(0.60))
    _draw_logo(fig, 1 - ml, header_top, header_h, logo, logo_alpha, logo_cap)   # top-right badge


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
        fig.canvas.draw()                             # shift so the LABEL's bottom (lowest ink) keeps a
        lb = cb.ax.xaxis.label.get_window_extent().transformed(fig.transFigure.inverted()).y0
        p = cax.get_position()                        # full side-margin above the image edge, not the bar
        cax.set_position([p.x0, p.y0 + (m_in / Hf - lb), p.width, p.height])
        return cb
    pos = ax.get_position()
    cax = fig.add_axes([pos.x1 + 0.014, pos.y0 + pos.height * 0.14, 0.011, pos.height * 0.72])
    cb = fig.colorbar(mappable, cax=cax)
    cb.set_label(label, color=W(0.80), fontsize=14)
    cb.ax.tick_params(colors=W(0.55), labelsize=12)
    cb.outline.set_edgecolor(KICK["grid"])
    return cb


def kick_pitch(pitch_type="statsbomb", vertical=False, line_zorder=2, pad=2, **kw):
    P = VerticalPitch if vertical else Pitch
    return P(pitch_type=pitch_type, pitch_color=KICK["figure"], line_color=KICK["pitch_line"],
             linewidth=1.2, line_zorder=line_zorder,
             pad_left=pad, pad_right=pad, pad_top=pad, pad_bottom=pad, **kw)


def draw_kick_pitch(pitch_type="statsbomb", vertical=False, line_zorder=2, pad=2,
                    width=None, margin_in=KICK_MARGIN_IN, title_pt=20, sub_pt=18,
                    legend=False, leg_in=0.72, caption=False, cap_in=2 * KICK_MARGIN_IN + 0.22,
                    cbar=False, cbar_pos="bottom", cbar_gutter=0.09, cbar_band=0.74):
    """House pitch filling the frame with a uniform inset (top gap above the header == side margin).
    The outer touchline margin is fixed at `margin_in` inches on every side. The PITCH SCALE (inches per
    metre) is the SAME in both orientations — the field's long side always spans `ref - 2*margin` — so a
    portrait pitch is NARROWER than a landscape one (same field rotated), NOT forced to the same width.
    Bottom band == side margin when no legend, or a wider band (leg_in) with a legend. cbar reserves
    room for the colourbar: cbar_pos="bottom" a band under the pitch (horizontal bar), or "right" a slim
    right gutter (vertical bar). Works for horizontal and vertical (bounds read from drawn limits)."""
    pitch = kick_pitch(pitch_type, vertical, line_zorder, pad=pad)
    tmp_fig, tmp_ax = pitch.draw(figsize=(4, 4))
    xr = abs(np.diff(tmp_ax.get_xlim())[0]); yr = abs(np.diff(tmp_ax.get_ylim())[0])
    aspect = xr / yr
    plt.close(tmp_fig)
    if width is None:
        # SAME pitch scale (inches per metre) in BOTH orientations — the field's LONG side always spans
        # (ref - 2*margin). So a PORTRAIT pitch comes out NARROWER than a landscape one (same field, just
        # rotated) — it does NOT share the landscape width. Type stays pixel-identical (constant DPI).
        field_x, field_y = xr - 2 * pad, yr - 2 * pad        # touchline extents, data units
        ref = KICK_LAYOUT["width_in"]                        # house landscape width; its long side ↔ ref - 2m
        width = field_x * (ref - 2 * margin_in) / max(field_x, field_y) + 2 * margin_in
    pad_xfrac, pad_yfrac = pad / xr, pad / yr
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
    xl, yl = ax.get_xlim(), ax.get_ylim()
    x_lo, x_hi = min(xl) + pad, max(xl) - pad             # touchline bounds in DRAWN coords
    y_lo, y_hi = min(yl) + pad, max(yl) - pad
    ax.add_patch(Rectangle((x_lo, y_lo), x_hi - x_lo, y_hi - y_lo,
                           facecolor=KICK["panel"], edgecolor="none", zorder=0.5))
    ax._kick_bounds = (x_lo, x_hi, y_lo, y_hi)
    ax._kick_cbar_pos = cbar_pos if cbar else None
    return pitch, fig, ax


def kick_legend(fig, ax, ncol=None):
    """Legend centred in the bottom margin (mirrors the title band). Auto-wraps to fewer columns /
    more rows if long labels would overflow the pitch width, so any label length displays correctly."""
    fig.canvas.draw()
    x_lo, x_hi, y_lo, y_hi = ax._kick_bounds
    figc = fig.transFigure.inverted().transform(
        ax.transData.transform([(x_lo, y_lo), (x_hi, y_lo), (x_lo, y_hi), (x_hi, y_hi)]))
    bottom, xmid = figc[:, 1].min(), figc[:, 0].mean()
    avail = figc[:, 0].max() - figc[:, 0].min()          # pitch width (figure fraction)
    handles, labels = ax.get_legend_handles_labels()
    cols = ncol or len(labels)
    while True:
        leg = ax.legend(handles, labels, loc="center", bbox_to_anchor=(xmid, bottom / 2),
                        bbox_transform=fig.transFigure, ncol=cols, columnspacing=1.8)   # handletextpad = house rcParam
        fig.canvas.draw()
        if cols <= 1 or leg.get_window_extent().transformed(fig.transFigure.inverted()).width <= avail:
            return leg
        leg.remove(); cols -= 1


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
            for idx in g:
                d = xy[idx] - c; d = d / (np.hypot(*d) + 1e-9)
                lx, ly = xy[idx] + d * off
                ax.plot([xy[idx, 0], lx], [xy[idx, 1], ly], color=accent, lw=0.8, alpha=0.7, zorder=2)
                ax.text(lx, ly, labels[idx], ha=("left" if d[0] >= 0 else "right"), va="center",
                        fontsize=10, color=W(0.82), zorder=6)
        else:                                                      # isolated → direct label
            idx = g[0]
            ax.annotate(labels[idx], xy[idx], xytext=(0, 9), textcoords="offset points",
                        ha="center", fontsize=10, color=W(0.82), zorder=6)
    if key:
        # anchor at a corner, then offset by EQUAL POINTS on both axes (not axes-fraction, which differs in
        # x vs y on a non-square axes → the box would sit farther from one axis than the other)
        corner = {"lower left": (0, 0, "left", "bottom", 1, 1), "lower right": (1, 0, "right", "bottom", -1, 1),
                  "upper left": (0, 1, "left", "top", 1, -1), "upper right": (1, 1, "right", "top", -1, -1)}
        fx, fy, ha, va, sx, sy = corner.get(key_loc, corner["lower left"])
        pad = 18.0                                                   # equal points from each axis (~3× the old 10pt gap)
        tr = ax.transAxes + mtransforms.ScaledTranslation(sx * pad / 72, sy * pad / 72, ax.figure.dpi_scale_trans)
        lines = [key_title] + [f"{k}  {lab}" for k, lab in key]
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
        t = ax.text(x, y - r - name_gap, name, color="#F4F4F4", fontsize=name_size, fontweight=name_weight,
                    ha="center", va="bottom", zorder=zorder + 2,
                    bbox=dict(boxstyle="round,pad=0.35", fc="#0C0C0C", ec=W(0.60), lw=1.0))
        t.set_path_effects([pe.withStroke(linewidth=2.4, foreground="#1C1C1C")])


# ── small-multiples: a grid of house pitches for comparisons ───────────────────
def kick_grid(nrows, ncols, vertical=False, line_zorder=2, pad=2, width=13.0,
              col_gap=0.30, row_gap=0.44, panel_label=0.46,
              title_pt=20, sub_pt=18, cbar=False, cbar_pos="right", cbar_gutter=0.6, cbar_band=0.74):
    """Grid of house pitches for small-multiple comparisons. Returns (pitch, fig, axes[nrows, ncols]).
    Reserve the overall header with kick_grid_title(fig, axes, ...); label each panel with
    kick_panel_label(ax, ...); a shared colourbar via cbar=True + kick_grid_cbar(...): cbar_pos="right"
    (a slim vertical bar in a right gutter) or "bottom" (a horizontal bar centred UNDER the grid with the
    label beneath, like the single pitch). Gaps in inches. Outer touchline margin solved to KICK_MARGIN_IN."""
    pitch = kick_pitch("statsbomb", vertical, line_zorder, pad=pad)
    tf, ta = pitch.draw(figsize=(4, 4))
    xr = abs(np.diff(ta.get_xlim())[0]); yr = abs(np.diff(ta.get_ylim())[0]); aspect = xr / yr
    plt.close(tf)
    pad_xfrac = pad / xr
    m_in = KICK_MARGIN_IN                                     # same outer touchline margin as every other chart
    gutter = cbar_gutter if (cbar and cbar_pos == "right") else 0.0   # right gutter only for a right colourbar
    free = width - gutter - (ncols - 1) * col_gap
    side = (m_in - pad_xfrac * free / ncols) / (1 - 2 * pad_xfrac / ncols)   # panel margin so outer == m_in
    pitch_w = (width - 2 * side - gutter - (ncols - 1) * col_gap) / ncols
    pitch_h = pitch_w / aspect
    header = (title_pt + 0.5 * title_pt + sub_pt) / 72.0 + 2 * m_in   # band = header text + 2 true margins,
    #   so the centred header leaves exactly m_in above it (matches draw_kick_pitch; NOT the panel inset `side`)
    extra_bottom = (m_in + cbar_band) if (cbar and cbar_pos == "bottom") else 0.0   # band below the grid for a bottom bar
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
            xl, yl = ax.get_xlim(), ax.get_ylim()
            x_lo, x_hi = min(xl) + pad, max(xl) - pad; y_lo, y_hi = min(yl) + pad, max(yl) - pad
            ax.add_patch(Rectangle((x_lo, y_lo), x_hi - x_lo, y_hi - y_lo,
                                   facecolor=KICK["panel"], edgecolor="none", zorder=0.5))
            ax._kick_bounds = (x_lo, x_hi, y_lo, y_hi); ax._kick_panel = panel_label / H
            axes[r, c] = ax
    fig._kick_header_frac = header / H
    fig._kick_grid_cbar_pos = cbar_pos if cbar else None
    return pitch, fig, axes


def kick_panel_label(ax, label, size=16, weight="normal"):
    """Small label centred in the band above a grid panel. Regular weight by default: bold is
    reserved for the one overall grid title (kick_grid_title), so panel labels stay subordinate to it."""
    fig = ax.figure; fig.canvas.draw()
    x_lo, x_hi, y_lo, y_hi = ax._kick_bounds
    figc = fig.transFigure.inverted().transform(       # all 4 corners -> true visual top (y-axis may invert)
        ax.transData.transform([(x_lo, y_lo), (x_lo, y_hi), (x_hi, y_lo), (x_hi, y_hi)]))
    top, xmid = figc[:, 1].max(), figc[:, 0].mean()
    fig.text(xmid, top + ax._kick_panel * 0.5, label, ha="center", va="center",
             fontsize=size, fontweight=weight, color=W(0.90))


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
        return cb
    tr, br = axes[0, -1].get_position(), axes[-1, -1].get_position()
    x = tr.x1 + 0.014
    y0 = br.y0 + br.height * 0.06; y1 = tr.y1 - tr.height * 0.06
    cax = fig.add_axes([x, y0, 0.010, y1 - y0])
    cb = fig.colorbar(mappable, cax=cax)
    cb.set_label(label, color=W(0.80), fontsize=14)
    cb.ax.tick_params(colors=W(0.55), labelsize=12)
    cb.outline.set_edgecolor(KICK["grid"])
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
    axes2 = np.atleast_2d(axes); left_col, bot_row = axes2[:, 0], axes2[-1, :]
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
    fig.subplots_adjust(left=left, right=right, top=top_ax, bottom=bottom, hspace=hspace, wspace=wspace)
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
