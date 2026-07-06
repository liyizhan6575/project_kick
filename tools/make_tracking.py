"""Generate synthetic-but-realistic player+ball tracking segments for the CV pitch demo.

Output: assets/tracking.js  ->  window.TRACK = {fps, segments:[{frames:[{h:[[x,y]x11],a:[[x,y]x11],b:[x,y]}]}]}
Pitch coords match the site: x in [0,105] (home attacks +x), y in [-34,34], centre (52.5,0).
Centroids only (no skeletons). Owned, swap-in file — replace with own-pipeline tracking when it ships.
"""
import json, math, os, random
random.seed(7)

HOME = [(8,0),(25,-22),(20,-8),(20,8),(25,22),(45,-14),(42,0),(45,14),(70,-20),(75,0),(70,20)]   # 4-3-3, attacks +x
AWAY = [(97,0),(80,20),(85,7),(85,-7),(80,-20),(62,22),(60,8),(60,-8),(62,-22),(46,-6),(46,6)]   # 4-4-2, defends high-x

# ball paths: (home_player_idx, travel_frames, hold_frames) — ball travels to that player, then is held while play shifts
PATHS = [
    [(0,1,5),(2,7,4),(1,8,4),(5,10,3),(6,7,3),(7,9,3),(10,12,5),(8,9,3),(5,8,4)],   # build from the back
    [(6,1,4),(7,8,3),(8,11,4),(7,9,3),(10,12,4),(9,8,4),(7,10,3),(3,12,5)],          # switch + circulate
    [(6,1,3),(9,12,3),(10,9,3),(8,8,3),(9,7,3),(10,8,4),(9,6,4)],                    # attack into the box
]
FPS = 12
CLY = lambda y: max(-33.0, min(33.0, y))
CLX = lambda x: max(2.0, min(103.0, x))
R = lambda v: round(v, 1)


def ease(s):  # smoothstep
    s = max(0.0, min(1.0, s)); return s * s * (3 - 2 * s)


def nearest(team, x, y, exclude=()):
    bi, bd = 0, 1e9
    for i, (px, py) in enumerate(team):
        if i in exclude: continue
        d = (px - x) ** 2 + (py - y) ** 2
        if d < bd: bd, bi = d, i
    return bi


def sim(path):
    home = [list(p) for p in HOME]; away = [list(p) for p in AWAY]
    frames = []
    bx, by = HOME[path[0][0]]
    for (tgt, travel, hold) in path:
        sx, sy = bx, by; ex, ey = HOME[tgt]
        steps = [(i / max(1, travel), True) for i in range(1, travel + 1)] + [(1.0, False) for _ in range(hold)]
        for prog, moving in steps:
            e = ease(prog); bx, by = sx + (ex - sx) * e, sy + (ey - sy) * e
            # team shape: slide whole block toward ball x/y (compactness), home pushes up a touch
            for team, base, atk in ((home, HOME, 1), (away, AWAY, -1)):
                for i in range(11):
                    tx = base[i][0] + (bx - 52.5) * 0.16 + atk * 1.5
                    ty = base[i][1] + by * 0.13
                    team[i][0] += (CLX(tx) - team[i][0]) * 0.10 + random.gauss(0, 0.10)
                    team[i][1] += (CLY(ty) - team[i][1]) * 0.10 + random.gauss(0, 0.10)
            # ball carrier glued to the ball; receiver anticipates
            home[tgt][0] += (ex - home[tgt][0]) * 0.25; home[tgt][1] += (ey - home[tgt][1]) * 0.25
            # nearest defender presses the ball
            d = nearest(away, bx, by)
            away[d][0] += (bx + 2.0 - away[d][0]) * 0.16; away[d][1] += (by - away[d][1]) * 0.16
            frames.append({"h": [[R(CLX(x)), R(CLY(y))] for x, y in home],
                           "a": [[R(CLX(x)), R(CLY(y))] for x, y in away],
                           "b": [R(CLX(bx)), R(CLY(by))]})
    return {"frames": frames}


data = {"fps": FPS, "segments": [sim(p) for p in PATHS]}
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "tracking.js")   # kick_site/assets (this tool lives in tools/)
with open(out, "w") as f:
    f.write("window.TRACK=" + json.dumps(data, separators=(",", ":")) + ";\n")
print("wrote", out, "| segments:", [len(s["frames"]) for s in data["segments"]], "frames")
