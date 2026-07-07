#!/usr/bin/env python3
"""Bake the hero-circle morph shapes into assets/shapes.js.

Produces three equal-length, angle-sorted particle sets (logo / player / ball) in a
shared ring-centred coordinate frame so the front-end can morph between them by
index-paired linear interpolation. Run offline from cached sources:

    assets/halftone.js   -> logo dots (kept as-is; no source PNG exists)
    assets/src/*.svg      -> player + ball silhouettes (game-icons, CC BY 3.0)

Coordinate frame: each shape is fit into a box of width 1 (BOX == logo width LW on
screen), centred at the origin. A particle is [px, py, r] with px,py in width-units
about centre and r the dot radius as a fraction of BOX. py already folds in the
shape's own aspect so x and y share one scale.
"""
import io, json, math, re
from pathlib import Path
import numpy as np, cairosvg
from PIL import Image

HERE = Path(__file__).parent          # kick_site/tools
ASSETS = HERE.parent / "assets"       # kick_site/assets
N = 320              # particles per shape (all sets resampled to this)
COLS = 24           # halftone grid columns — matches the logo's 24-col grid
K = 0.0150          # dot radius at full ink (fraction of box width) — matches logo r_max
GAMMA = 0.70        # ink->radius perceptual curve
INK_THR = 0.14      # drop grid cells fainter than this

# ---- logo: reuse existing dots (centre + fold aspect into y) -------------------
def load_logo():
    hj = ASSETS / "halftone.js"
    if hj.exists():
        txt = hj.read_text()
        obj = json.loads(txt[txt.index("{"): txt.rindex("}") + 1])
        asp = obj["aspect"]
        return [(x - 0.5, (y - 0.5) / asp, r) for x, y, r in obj["dots"]]
    # halftone.js is gone — reuse the already-baked logo dots from shapes.js (already in the centred frame)
    txt = (ASSETS / "shapes.js").read_text()
    obj = json.loads(txt[txt.index("{"): txt.rindex("}") + 1])
    return [(x, y, r) for x, y, r in obj["shapes"][obj["names"].index("logo")]]

# ---- ink mask: works for transparent silhouettes AND opaque-background pictograms
def ink_map(rgba):
    arr = np.asarray(rgba).astype(float) / 255.0
    a = arr[:, :, 3]
    if a.mean() < 0.9:                               # transparent bg -> alpha is the shape
        return a
    bg = arr[0, 0, :3]                               # opaque bg -> distance from corner colour
    return np.sqrt(((arr[:, :, :3] - bg) ** 2).sum(2)) / (3 ** 0.5)

# ---- svg silhouette -> halftone dots in the same centred frame ----------------
def svg_dots(path):
    png = cairosvg.svg2png(bytestring=Path(path).read_bytes(), output_width=640)
    a = ink_map(Image.open(io.BytesIO(png)).convert("RGBA"))
    ys, xs = np.where(a > 0.25)
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    H, W = a.shape
    rows = max(1, round(H / (W / COLS)))
    asp = W / H
    out = []
    for ri in range(rows):
        for ci in range(COLS):
            blk = a[int(ri * H / rows):int((ri + 1) * H / rows),
                    int(ci * W / COLS):int((ci + 1) * W / COLS)]
            if blk.size == 0:
                continue
            v = float(blk.mean())
            if v < INK_THR:
                continue
            x, y = (ci + 0.5) / COLS, (ri + 0.5) / rows
            out.append((x - 0.5, (y - 0.5) / asp, (v ** GAMMA) * K))
    return out

# ---- resample to exactly N, then sort by angle for coherent index-pairing ------
def resample(dots, n):
    d = sorted(dots, key=lambda p: p[2], reverse=True)      # by radius (importance)
    if len(d) >= n:
        d = d[:n]
    else:
        i = 0
        while len(d) < n:                                   # duplicate the boldest dots
            d.append(d[i % len(dots)]); i += 1
    return d

def angle_sort(dots):
    cx = sum(p[0] for p in dots) / len(dots)
    cy = sum(p[1] for p in dots) / len(dots)
    return sorted(dots, key=lambda p: (math.atan2(p[1] - cy, p[0] - cx),
                                       math.hypot(p[0] - cx, p[1] - cy)))

def prep(dots):
    return [[round(x, 4), round(y, 4), round(r, 5)] for x, y, r in angle_sort(resample(dots, N))]

def main():
    raw = {"logo": load_logo(),
           "player": svg_dots(ASSETS / "src" / "player_1972.svg"),
           "ball": svg_dots(ASSETS / "src" / "ball.svg")}
    shapes = {name: prep(d) for name, d in raw.items()}
    names = ["logo", "player", "ball"]
    payload = {"N": N, "names": names, "shapes": [shapes[k] for k in names]}
    out = ASSETS / "shapes.js"
    out.write_text("window.HALFTONE_SHAPES=" + json.dumps(payload, separators=(",", ":")) + ";\n")
    for k in names:
        print(f"  {k:7s} raw={len(raw[k]):4d} -> {N}  (dup={max(0, N - len(raw[k]))})")
    print(f"wrote {out} ({out.stat().st_size} B)")

if __name__ == "__main__":
    main()
