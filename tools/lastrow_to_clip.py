"""Convert a "Last Row" (Friends of Tracking) single-goal CSV → assets/viz_clips_data.js.

The Last Row goal CSVs are continuous tracking (frame,player,team,dx,dy,x,y) at 20 fps, one goal each,
attacking toward x=100 on a 0..100 x 0..100 normalised pitch (verified empirically: dx/dy are per-frame
displacement; a 95th-pct player step → ~9 m/s only at 20 fps; the ball ends in the goal mouth).

We emit ONE clip in the site's kick_goalclip_v1 schema (the same shape render_viz_clip.py dumps from
Tier-5), so it drives the existing chapter-2 broadcast engine unchanged.

Real tracking is kept as the truth for every player who actually moves. Three things are repaired so the
scene reads like live football (the raw feed has artefacts — the goalkeeper is not tracked, and a few
players sit frozen):
  • FLOW      — a light centred moving-average on every outfield track removes 20 fps jitter.
  • UN-FREEZE — players the feed leaves stationary (≈0 m travel) drift with their team's collective
                motion (centroid delta) + a small idle walk, so no one stands rooted while play flows past.
  • KEEPER    — a goalkeeper is synthesised for the defending side: it holds the goal line, shades along
                the ball→goal angle (advancing as the ball nears), then lunges as the shot crosses.
Fabricated metadata (jersey/pos/gk, score, scorer, clock) is plausible and pseudonymised, like the
Tier-5 path (the site already de-brands to gold/white kits — no real names or club marks).

Usage:  python3 tools/lastrow_to_clip.py [path/to/goal.csv]
"""
import csv, collections, json, math, os, re, sys, random

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # kick_site/ (this tool lives in tools/)
DEFAULT_CSV = "/home/liyi/Documents/project_kick/kick_lab/data/friends-of-tracking_data/tracking_data_examples/014_Liverpool_[2]_-_0_Man_City.csv"
OUT = os.path.join(SITE, "assets", "viz_clips_data.js")

FPS = 20                        # Last Row native rate (empirically the only rate giving realistic speeds)
SPD_ENGINE = 0.48               # clip_engine.js build-up tempo — cancelled so dur reads as real seconds (true real-time)
PX, PY = 105.0, 68.0            # pitch metres; Last Row is 0..100 on each axis
GOAL_X, POST = 105.0, 3.66      # attacking goal (home attacks +x) · half goal-width
SMOOTH_R = 2                    # centred moving-average radius (5-frame ≈ 0.25 s window) — flow, not mush
FROZEN_M = 1.0                  # total-travel (m) below which a track is a feed dropout (full team-follow synthesis)
LIVELY_M = 14.0                 # below this a track reads as static → keep it but add drift + idle so play flows
NET_DEPTH = 2.2                 # metres the ball marches PAST the goal line into the net (so a goal reads as scored, not saved)
R = lambda v: round(float(v), 2)
SURNAMES = ["Almeida","Bianchi","Costa","Duarte","Ferreira","Gomez","Haddad","Iglesias","Moreau","Novak",
            "Okafor","Pereira","Rossi","Sato","Torres","Varga","Weiss","Ximenes"]


def to_metre(x, y):
    return [min(105.0, max(0.0, x / 100.0 * PX)), min(34.0, max(-34.0, y / 100.0 * PY - 34.0))]


def ball_metre(x, y):   # ball x is NOT clamped at the goal line — it must be able to cross into the net
    return [x / 100.0 * PX, min(34.0, max(-34.0, y / 100.0 * PY - 34.0))]


def ease(t):   # smoothstep
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


def smooth(track, r=SMOOTH_R):
    n = len(track); out = []
    for f in range(n):
        lo, hi = max(0, f - r), min(n - 1, f + r)
        sx = sum(track[g][0] for g in range(lo, hi + 1)); sy = sum(track[g][1] for g in range(lo, hi + 1))
        out.append([sx / (hi - lo + 1), sy / (hi - lo + 1)])
    return out


def path_len(track):
    return sum(math.hypot(track[f][0] - track[f - 1][0], track[f][1] - track[f - 1][1]) for f in range(1, len(track)))


def clampf(track):
    return [[R(min(105.0, max(0.0, x))), R(min(34.0, max(-34.0, y)))] for x, y in track]


def parse_score(fname):
    # We force home = attackers = the team that just scored (the bracketed side in the filename), so the score
    # must be keyed to the SCORER, not to filename order — otherwise 'away scored' goals increment the wrong side.
    base = os.path.basename(fname).rsplit(".", 1)[0]
    m = re.match(r"\d+_(.+?)_(\[?\d+\]?)_-_(\[?\d+\]?)_(.+)", base)
    if not m:
        return {"home_post": 1, "away_post": 0, "home_pre": 0, "away_pre": 0}
    g2, g3 = m.group(2), m.group(3)
    scorer_first = "[" in g2                                   # bracketed side = team that scored this goal = our "home"
    sc = int((g2 if scorer_first else g3).strip("[]"))         # scorer tally AFTER the goal
    oth = int((g3 if scorer_first else g2).strip("[]"))        # the other side
    return {"home_post": sc, "away_post": oth, "home_pre": sc - 1, "away_pre": oth}


def home_keeper_track(ball_m, nf, own_goal_x, atk_dir):
    """Synthesise the ATTACKING team's keeper — it is never in the feed (far from the ball). It starts by its
    OWN goal (the opposite end) and slowly pushes up as its team attacks (sweeper-keeper), staying central."""
    raw = []
    for f in range(nf):
        fwd = 3.0 + 28.0 * ease(f / max(1, nf - 1))       # advances 3 m → ~31 m off its own line over the clip
        gx = own_goal_x + atk_dir * fwd                    # atk_dir points upfield (toward the attacked goal)
        gy = max(-6.0, min(6.0, ball_m[f][1] * 0.12)) + 0.6 * math.sin(f / max(1, nf) * 5.0)   # central, slight ball-side lean + gentle shuffle
        raw.append([gx, gy])
    return smooth(raw, 2)


def keeper_track(ball_m, nf, goal_x):
    """Synthesise a defending goalkeeper (goal line at goal_x, either end): it shades continuously along the
    ball→goal angle the WHOLE time (subtle, never pinned to a post) with a small live weight-shift, then makes
    a modest late reaction as the shot comes in — but stays clearly SHORT of the ball, so the goal beats it."""
    shot_by = ball_m[-1][1]
    sgn = 1.0 if goal_x >= 52.5 else -1.0                     # +1 attacking x=105 · -1 attacking x=0
    raw = []
    for f in range(nf):
        bx, by = ball_m[f]
        prog = bx if sgn > 0 else (105.0 - bx)                # how far the ball has advanced toward the goal (0..105)
        adv = max(0.0, min(1.0, (prog - 55.0) / 50.0))        # 0 (ball far) → 1 (ball at goal)
        depth = 3.4 - 2.0 * adv                               # comes off the line: 3.4 m out (far) → 1.4 m (near) — clear x travel
        gx = goal_x - sgn * depth
        gy = max(-POST + 0.4, min(POST - 0.4, by * (0.11 + 0.33 * adv)))   # continuous shading — small when the ball is far, growing as it nears (no early post-pin)
        gy += 0.7 * math.sin(f / max(1, nf) * 6.0)            # visible weight-shift/shuffle so the keeper is clearly alive, never frozen
        raw.append([gx, gy])
    dive = 10                                                 # modest late reaction toward the shot side — comes up SHORT (beaten), never onto the ball
    for f in range(max(0, nf - dive), nf):
        w = (f - (nf - dive)) / dive
        raw[f][1] = raw[f][1] + (shot_by * 0.55 - raw[f][1]) * w         # only ~55% toward the ball's corner
        raw[f][0] = raw[f][0] + ((goal_x - sgn * 1.6) - raw[f][0]) * w * 0.4   # stays ~1.6 m off the line — the ball crosses well past it
    return smooth(raw, 1)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV
    random.seed(sum(ord(c) for c in os.path.basename(src)))
    rows = list(csv.DictReader(open(src)))
    frames = collections.defaultdict(dict)                    # frame -> {player: (x,y)}
    team_of = {}
    for r in rows:
        frames[int(r["frame"])][r["player"]] = (float(r["x"]), float(r["y"]))
        team_of[r["player"]] = r["team"]
    fr_ids = sorted(frames); nf = len(fr_ids)

    ball_m = [ball_metre(*frames[f][p]) for f in fr_ids for p in frames[f] if team_of[p] == ""]
    atk_ids = sorted({p for p, t in team_of.items() if t == "attack"}, key=int)
    dfn_ids = sorted({p for p, t in team_of.items() if t == "defense"}, key=int)

    # raw metre tracks per outfield player (carry last-known if a frame is missing that id)
    def raw_track(pid):
        tr, last = [], None
        for f in fr_ids:
            if pid in frames[f]:
                last = to_metre(*frames[f][pid])
            tr.append(last if last else [52.5, 0.0])
        return tr
    tracks = {p: raw_track(p) for p in atk_ids + dfn_ids}

    # attack direction (from the ball's net travel) → the goal the defence protects
    atk_dir = 1.0 if ball_m[-1][0] >= ball_m[0][0] else -1.0
    goal_x = 105.0 if atk_dir > 0 else 0.0

    # REAL GOALKEEPER? the deepest defender parked by its own goal line IS the keeper — use it as-is. Only
    # synthesise a keeper when the feed tracked nobody near the line (e.g. clip 001). Avoids two keepers.
    def _meanx(pid): return sum(pt[0] for pt in tracks[pid]) / nf
    gk_real = min(dfn_ids, key=lambda p: abs(_meanx(p) - goal_x)) if dfn_ids else None
    if gk_real is not None and abs(_meanx(gk_real) - goal_x) >= 9.0:
        gk_real = None                                    # nobody near the line → synthesise one below

    # KEEP-ALIVE: no outfield player should read as static. Truly rooted tracks (feed dropouts) follow their
    # team's collective motion; merely near-static tracks keep their real path but gain a gentle drift + idle
    # shuffle. Players who already move plenty are left untouched (only smoothed later).
    def centroid(ids, f):
        movers = [tracks[p][f] for p in ids if path_len(tracks[p]) >= 3.0]
        if not movers:
            return [0.0, 0.0]
        return [sum(m[0] for m in movers) / len(movers), sum(m[1] for m in movers) / len(movers)]
    for side_ids in (atk_ids, dfn_ids):
        cen0 = centroid(side_ids, 0)
        for p in side_ids:
            if p == gk_real:                              # a real keeper stays home — don't drag it upfield with the outfield centroid
                continue
            pl = path_len(tracks[p])
            if pl >= LIVELY_M:
                continue
            frozen = pl < FROZEN_M
            p0 = tracks[p][0]; ph = random.uniform(0, 6.283); amp = random.uniform(0.9, 1.7)
            new = []
            for f in range(nf):
                cen = centroid(side_ids, f); dx, dy = cen[0] - cen0[0], cen[1] - cen0[1]
                if frozen:                                        # no usable track → move with the team's shape
                    bx, by = p0[0] + dx * 0.65, p0[1] + dy * 0.65
                else:                                             # real but sluggish → keep it, ride more of the team drift so it clearly translates (not just wiggles)
                    bx, by = tracks[p][f][0] + dx * 0.45, tracks[p][f][1] + dy * 0.45
                bx += amp * 0.8 * math.sin(ph + f / nf * 5.0)     # idle shuffle (low frequency → drift, not jitter)
                by += amp * 0.8 * math.sin(ph * 1.6 + f / nf * 4.0)
                new.append([bx, by])
            tracks[p] = new

    # FLOW: light smoothing on every outfield track
    for p in tracks:
        tracks[p] = clampf(smooth(tracks[p]))

    # BALL INTO THE NET: once the ball crosses the goal line, march it on INTO the net (instead of parking on
    # the line) so the goal reads as scored, not saved. The renderer then fades it out as it enters the net.
    crossed = next((f for f in range(nf) if (ball_m[f][0] >= GOAL_X if atk_dir > 0 else ball_m[f][0] <= 0.0)), None)
    if crossed is not None:
        net_x = goal_x + atk_dir * NET_DEPTH
        bx0, by0, byN = ball_m[crossed][0], ball_m[crossed][1], ball_m[-1][1]
        span = max(1, nf - 1 - crossed)
        for f in range(crossed, nf):
            w = (f - crossed) / span
            ball_m[f] = [bx0 + (net_x - bx0) * w, by0 + (byN - by0) * w]

    # AWAY KEEPER: use the real tracked keeper if the feed has one; otherwise synthesise one on the line
    if gk_real is not None:
        GK_ID, gk_track = gk_real, None                   # real keeper — already in dfn_ids, just labelled below
    else:
        GK_ID, gk_track = "gk_away", clampf(keeper_track(ball_m, nf, goal_x))

    # HOME KEEPER: always synthesised — the attacking team's keeper is off-camera in the feed. Parked by its
    # OWN goal (opposite end), slowly pushing up as the team attacks.
    own_goal_x = 0.0 if goal_x >= 52.5 else 105.0
    home_gk = clampf(home_keeper_track(ball_m, nf, own_goal_x, atk_dir))

    # rosters (jersey + crude role; GK explicit). Sort by depth so tags are plausible; render is discs-only anyway.
    def roster(ids, side, gk_id=None):
        meanx = {i: sum(pt[0] for pt in tracks[i]) / nf for i in ids}
        order = sorted(ids, key=lambda i: meanx[i], reverse=(side == "away"))
        meta = {}
        for n, i in enumerate(order):
            meta[i] = {"j": str(n + 2), "pos": "DF" if n < 4 else "MF" if n < 7 else "FW", "gk": False}
        if gk_id in meta:
            meta[gk_id] = {"j": "1", "pos": "GK", "gk": True}   # the real keeper
        return meta
    ameta = roster(atk_ids, "home")
    dmeta = roster(dfn_ids, "away", gk_id=gk_real)

    def frame_players(ids, meta, f, gk_track=None, gk_id=None):
        out = []
        for i in ids:
            m = meta[i]
            out.append({"id": i, "pos": m["pos"], "j": m["j"], "gk": m["gk"], "xy": [R(tracks[i][f][0]), R(tracks[i][f][1])]})
        if gk_track is not None:                          # a SYNTHESISED keeper
            out.append({"id": gk_id, "pos": "GK", "j": "1", "gk": True, "xy": [R(gk_track[f][0]), R(gk_track[f][1])]})
        return out

    dur = round((1.0 / FPS) / SPD_ENGINE, 4)
    clip_frames = []
    for f in range(nf):
        ball = [R(ball_m[f][0]), R(ball_m[f][1])]
        h = frame_players(atk_ids, ameta, f, gk_track=home_gk, gk_id="gk_home")   # attackers + synth keeper = home (gold)
        a = frame_players(dfn_ids, dmeta, f, gk_track=gk_track, gk_id=GK_ID)       # defenders + (synth?) keeper = away (white)
        cand = [(math.hypot(p["xy"][0] - ball[0], p["xy"][1] - ball[1]), p["id"]) for p in h if not p["gk"]]
        clip_frames.append({"dur": dur, "carrier": (min(cand)[1] if cand else None), "ball": ball, "h": h, "a": a})

    sc = parse_score(src)
    last_ball = clip_frames[-1]["ball"]
    mouth = [round(min(1.0, max(0.0, last_ball[0] / 105.0)), 3), round(last_ball[1] / 68.0 + 0.5, 3)]
    hh = 0
    for c in os.path.basename(src):
        hh = (hh * 131 + ord(c)) & 0x7fffffff

    clip = {
        "schema": "kick_goalclip_v1", "fps": FPS, "nf": nf, "ltr": True, "period": 2,
        "goal_side": "home", "is_goal": True, "set_piece": False,
        "is_penalty": False, "is_own_goal": False, "is_corner_led": False,
        "clock": {"period_label": "2H", "minute": 74, "text": "2H 74'"},
        "score": {"home_post": sc["home_post"], "away_post": sc["away_post"],
                  "home_pre": sc["home_pre"], "away_pre": sc["away_pre"], "home_atk_dir": atk_dir},
        "scorer": {"name": SURNAMES[hh % len(SURNAMES)], "descriptor": "Goal", "xg": 0.09},
        "teams": {"home": {"id": "lastrow_home", "icon": "home", "kit": "#fbbf24"},
                  "away": {"id": "lastrow_away", "icon": "away", "kit": "#ffffff"}},
        "mouth": mouth,
        "marks": {"shot_f": nf - 1, "goal_f": nf - 1, "checker_kick_f": -1},
        "frames": clip_frames,
    }

    with open(OUT, "w") as f:
        f.write("window.VIZ_CLIPS=" + json.dumps([clip], separators=(",", ":")) + ";\n")
    frozen = [p for p in (atk_ids + dfn_ids) if path_len(raw_track(p)) < FROZEN_M]
    print(f"wrote {OUT}")
    print(f"  source: {os.path.basename(src)}  | {nf} frames @ {FPS}fps ({nf/FPS:.1f}s) | dur/frame={dur}s")
    gkdesc = f"real GK id {gk_real}" if gk_real is not None else "synth GK"
    print(f"  roster: {len(atk_ids)} attack + synth home GK (gold) = {len(atk_ids)+1} | {len(dfn_ids)} defense (away/white incl {gkdesc})")
    print(f"  un-frozen: {frozen} | smoothed all tracks (R={SMOOTH_R}) | mouth={mouth}")
    print(f"  score: home {sc['home_pre']}→{sc['home_post']}  away {sc['away_pre']}→{sc['away_post']} | {os.path.getsize(OUT)//1024} KB")


if __name__ == "__main__":
    main()
