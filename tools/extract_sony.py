"""Extract player + ball CENTROID segments from the licensed Sony feed -> assets/tracking.js.

Centroids only (no skeletons/joints, no IDs in the output — just motion). Picks the most active ~8s
window per chosen minute (max ball travel) so it's live play, not a dead ball. Output frames are
{h:[[x,y]x11], a:[[x,y]x11], b:[x,y]} in site coords (x 0..105, y -34..34), downsampled to 12.5 fps.
"""
import json, collections, os

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # kick_site/ (this tool lives in tools/)
OUT = os.path.join(SITE, "assets", "tracking.js")
BASE = "/home/liyi/Documents/project_kick/kick_lab/data/sony_data_feed/20221112_SSC Napoli_Udinese"
STEM = "2023_1r097lpxe0xn03ihb7wi98kao_4z1wr3asvyoyfrc6jd7g1mrkk_{}.football.samples.{}"
MINUTES = ["1_10", "1_27", "2_70"]          # early / mid-1H / 2H — variety
WIN_S, STEP, SRC_FPS = 15.0, 4, 50          # 15s window, take every 4th frame -> 12.5 fps
R = lambda v: round(v, 1)


def load_minute(mn):
    c = json.load(open(f"{BASE}/scrubbed.samples.centroids/{STEM.format(mn,'centroids')}"))
    teams = {t["id"]["optaId"]: ("h" if t["home"] else "a") for t in c["details"]["teams"]}
    pteam = {p["id"]["optaId"]: teams.get(p["teamId"]["optaId"]) for p in c["details"]["players"]}
    ftd = collections.defaultdict(dict); tteam = {}
    for r in c["samples"]["people"]:
        s = r["centroid"][0]; tid = r["trackId"]; tm = pteam.get(r["personId"].get("optaId"))
        if tm not in ("h", "a"):                       # refs / unmapped -> skip
            continue
        ftd[round(s["time"], 3)][tid] = s["pos"]; tteam[tid] = tm
    b = json.load(open(f"{BASE}/scrubbed.samples.ball/{STEM.format(mn,'ball')}"))
    btd = {round(s["time"], 3): s["pos"] for s in b["samples"]["ball"]}
    return sorted(ftd), ftd, btd, tteam


def best_window(times, btd):
    n = int(WIN_S * SRC_FPS)
    bpos = [btd.get(t) for t in times]
    best, bi = -1, 0
    for i in range(0, len(times) - n, SRC_FPS):
        d = 0.0
        for j in range(i + 1, i + n):
            a, b = bpos[j - 1], bpos[j]
            if a and b:
                d += abs(a[0] - b[0]) + abs(a[1] - b[1])
        if d > best:
            best, bi = d, i
    return bi, bi + n


def to_site(p):  return [R(max(0.0, min(105.0, p[0] + 52.5))), R(max(-34.5, min(34.5, p[1])))]


def nearest_ball(btd, times, t):
    if t in btd: return btd[t]
    return btd[min(btd, key=lambda k: abs(k - t))]


def extract(mn):
    times, ftd, btd, tteam = load_minute(mn)
    a0, a1 = best_window(times, btd)
    win = times[a0:a1]
    # stable roster: the 11 most-present trackIds per team across the window
    pres = {"h": collections.Counter(), "a": collections.Counter()}
    for t in win:
        for tid in ftd[t]:
            pres[tteam[tid]][tid] += 1
    roster = {k: [tid for tid, _ in pres[k].most_common(11)] for k in ("h", "a")}
    last = {tid: None for tid in roster["h"] + roster["a"]}
    frames = []
    for t in win[::STEP]:
        fr = {}
        for k in ("h", "a"):
            row = []
            for tid in roster[k]:
                p = ftd[t].get(tid) or last[tid]
                if p: last[tid] = p
                row.append(to_site(p) if p else [52.5, 0.0])
            fr[k] = row
        bp = nearest_ball(btd, times, t)
        fr["b"] = to_site(bp) if bp else [52.5, 0.0]
        frames.append(fr)
    print(f"  {mn}: window {win[0]:.1f}-{win[-1]:.1f}s -> {len(frames)} frames, {len(roster['h'])}h+{len(roster['a'])}a")
    return {"frames": frames}


print("Extracting Sony centroid segments...")
segs = [extract(mn) for mn in MINUTES]
data = {"fps": round(SRC_FPS / STEP, 1), "segments": segs}
with open(OUT, "w") as f:
    f.write("window.TRACK=" + json.dumps(data, separators=(",", ":")) + ";\n")
print("wrote %s (%d KB)" % (OUT, os.path.getsize(OUT) // 1024))
