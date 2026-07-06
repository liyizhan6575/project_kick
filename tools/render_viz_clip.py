"""Website-owned Viz-clip renderer.

Reads tier5/goal_sequence.py READ-ONLY, applies web-mode patches in memory, writes a throwaway
temp into tier5/ (so the pristine Tier-5 modules still import), renders, then deletes the temp.
NO Tier-5 source file is ever modified. Output → kick_site/assets/viz_clip.mp4.

Web changes: brand checkers (gold/white) · no sponsor logos · grey placeholder flags · "REPLAY"
tab · no narration box · English labels · pseudo player names · position-only on-pitch nametags.
"""
import os, sys, subprocess, shutil

HERE = os.path.dirname(os.path.abspath(__file__))   # kick_site/tools
SITE = os.path.dirname(HERE)                         # kick_site/
TIER5 = os.path.normpath(os.path.join(SITE, "..", "pitch_pilot", "tier5"))
SRC = os.path.join(TIER5, "goal_sequence.py")
TMP = os.path.join(TIER5, "_viz_web_tmp.py")
WORK = os.path.normpath(os.path.join(SITE, "..", "pitch_pilot", "output", "_work"))
KEY = os.environ.get("VIZ_KEY", "pitch_pilot/20260620巴西vs海地")
CLIP = os.environ.get("VIZ_CLIP", "0")
NAME = os.environ.get("VIZ_NAME", CLIP)   # output slot (so different fixtures don't collide on clip index)
OUT = os.path.join(SITE, "assets", f"viz_clip_{NAME}.mp4")
ICON_HOME = os.path.join(SITE, "assets", "_icon_home.png")   # gold shield  → home team
ICON_AWAY = os.path.join(SITE, "assets", "_icon_away.png")   # white attack → away team
DUMP = os.environ.get("PP_DUMP_JSON")    # if set: dump per-frame position JSON here + exit before any render


def patch(code, old, new, label, soft=False):
    if old not in code:
        if soft:   # render-only patch (cosmetic mp4 tweak) — irrelevant to the JSON dump, so skip if Tier-5 moved the anchor
            print(f"  skip soft patch [{label}] — anchor not found (render-only, harmless for the dump)")
            return code
        raise SystemExit(f"PATCH MISS [{label}]: anchor not found — Tier-5 source changed?")
    return code.replace(old, new, 1)


code = open(SRC, encoding="utf-8").read()

# A · brand checkers (gold home / white away — the accent colours)
code = patch(code, 'KOR=_kitk["home"]; CZE=_kitk["away"]', 'KOR="#fbbf24"; CZE="#ffffff"', "checkers")
# A2 · GK checker matches its outfielders (so EVERY checker is one of the two brand colours)
code = patch(code, 'GK_COL=_tk.gk_colors(KOR,CZE)', 'GK_COL={"home":KOR,"away":CZE}', "gk_color", soft=True)
# A3 · xG-box accent pinned to brand gold (never auto-switch to a third hue)
code = patch(code, 'ACCENT=_tkc.goal_accent(KOR,CZE)', 'ACCENT="#fbbf24"', "accent", soft=True)
# A4 · NO tactical / threat-ranking replay (render-only; the JSON dump exits before any render)
code = patch(code, '_DO_PASS2 = bool(IS_GOAL and not SETPIECE and not _IS_OG and not _CORNER_LED and not _SCRAMBLE_LED and _NPASS > 2)', '_DO_PASS2 = False', "no_pass2", soft=True)
# C · on-pitch nametag = POSITION only
code = patch(code,
    'def _tag_path(nm):                                # "POS | Name": POSITION in BOLD, " | name" in regular, as one glyph path\n'
    '    p=POS_BY_NAME.get(nm,"")\n'
    '    if not p: return TextPath((0,0),nm,size=10,prop=fp_reg)',
    'def _tag_path(nm):                                # WEB: POSITION abbreviation only\n'
    '    p=POS_BY_NAME.get(nm,"")\n'
    '    return TextPath((0,0),p or nm,size=10,prop=fp)', "nametag", soft=True)
# D · drop the narrator box (invisible outline + empty text; speaker icon blanked via imread patch)
code = patch(code, 'ec="#4a5260",lw=1.7', 'ec="none",lw=0', "narr_box", soft=True)
code = patch(code, '(_narr_lead+(NARRATION or ""))', '""', "narr_text", soft=True)
# B · pseudonymise names right after the data load (before POS_BY_NAME is built)
code = patch(code,
    'off=MatchEngine.process_offline(str(path),hid,aid); import cn_names as _cn; _cn.localize(off.events); chains=build_chains(off.events)',
    'off=MatchEngine.process_offline(str(path),hid,aid); import cn_names as _cn; _cn.localize(off.events); _WEB_pseudonymize(off.events); _WEB_teams["home"]=hn; _WEB_teams["away"]=an; chains=build_chains(off.events)',
    "pseudo_call")

INJECT = '''
# ===== WEB-ONLY runtime patches (generated temp; production goal_sequence.py is untouched) =====
import numpy as _wnp, matplotlib.pyplot as _wplt
_WEB_SURNAMES=["Almeida","Bianchi","Costa","Duarte","Engqvist","Ferreira","Gomez","Haddad","Iglesias","Jensen","Keller","Lindqvist","Moreau","Novak","Okafor","Pereira","Quinn","Rossi","Sato","Torres","Ulloa","Varga","Weiss","Ximenes","Yilmaz","Zappa","Bauer","Crespo","Diallo","Esposito"]
_WEB_pmap={}
def _WEB_pseudonymize(events):
    for _e in events:
        for _o in (_e, getattr(_e,"raw_event",None)):
            if _o is None: continue
            _nm=getattr(_o,"player_name",None)
            if not _nm: continue
            if _nm not in _WEB_pmap:
                _h=0
                for _c in str(_nm): _h=(_h*131+ord(_c))&0x7fffffff
                _WEB_pmap[_nm]=_WEB_SURNAMES[_h%len(_WEB_SURNAMES)]
            try: _o.player_name=_WEB_pmap[_nm]
            except Exception: pass
# team icons (gold shield = home · white attack = away) on the grass flag + clock badge; blanked speaker
import os as _wos
_WEB_imread0=_wplt.imread
_WEB_HOME_ICON=_WEB_imread0(r"__HOME_ICON__"); _WEB_AWAY_ICON=_WEB_imread0(r"__AWAY_ICON__")
_WEB_grey=_wnp.zeros((64,64,4)); _WEB_grey[...,:3]=0.34; _WEB_grey[...,3]=1.0   # fallback if a name doesn't match
_WEB_blank=_wnp.zeros((4,4,4)); _WEB_teams={}
def _WEB_imread(p,*a,**k):
    _ps=str(p)
    if "speaker" in _ps: return _WEB_blank.copy()
    if "flags" in _ps and _ps.endswith(".png"):
        _nm=_wos.path.basename(_ps)[:-4]
        if _nm==_WEB_teams.get("home"): return _WEB_HOME_ICON.copy()
        if _nm==_WEB_teams.get("away"): return _WEB_AWAY_ICON.copy()
        return _WEB_grey.copy()
    return _WEB_imread0(p,*a,**k)
_wplt.imread=_WEB_imread
# "REPLAY" tab label
import lang as _wlang
_WEB_t0=_wlang.t
def _WEB_t(key,*a,**k):
    if key=="tab.goal_replay": return "REPLAY"
    return _WEB_t0(key,*a,**k)
_wlang.t=_WEB_t
# drop the momentum timeline entirely
import momentum_timeline as _wmt
_wmt.draw=lambda *a,**k: []
# ================================================================================================
'''
INJECT = INJECT.replace("__HOME_ICON__", ICON_HOME).replace("__AWAY_ICON__", ICON_AWAY)
code = patch(code, 'import pitch_logo\n', 'import pitch_logo\n' + INJECT, "inject")

# E · DATA-EXPORT mode — dump per-frame positions to JSON, then exit BEFORE any matplotlib/ffmpeg work.
#     Hooked at the GSTART line (1159): G/ball/durs/meta/ops/mouth/flags are all final there. Production
#     (PP_DUMP_JSON unset) falls straight through to the GSTART assignment unchanged.
DUMP_HOOK = '''GSTART=next((i for i,v in enumerate(VID) if v[5]),len(VID))
if _wos.environ.get("PP_DUMP_JSON"):
    import json as _dj
    def _m(p): return [round(float(p[0])*105.0,2), round(float((p[1]-0.5)*68.0),2)]   # display[0,1] -> metre space
    def _pl(side):
        out=[]
        for op in ops:
            if op not in G[f]: continue
            mt=meta[op]
            if (mt["side"]=="home")!=(side=="home"): continue
            nm=mt["name"]; pos=POS_BY_NAME.get(nm,"") or (mt.get("role") or "")
            out.append({"id":str(op),"pos":pos,"j":str(mt["jersey"]),"gk":str(mt.get("role") or "").upper()=="GK","xy":_m(G[f][op])})
        return out
    frames=[]
    for f in range(NF):
        _c=carrier_op(f); _b=None
        if _c is not None and _c in G[f]: _b=_m(G[f][_c])
        elif ball[f] is not None: _b=_m(ball[f])
        frames.append({"dur":round(float(durs[f]),3),"carrier":(str(_c) if _c is not None else None),"ball":_b,"h":_pl("home"),"a":_pl("away")})
    _kick_f=-1
    if SETPIECE_OK:
        try: _kick_f=next((f for f in range(NF) if seq[f][2].id==CORNER_EID),-1)
        except Exception: _kick_f=-1
    _preh=int(GOAL_SH)-(1 if (IS_GOAL and GOAL_SIDE=="home") else 0)
    _prea=int(GOAL_SA)-(1 if (IS_GOAL and GOAL_SIDE=="away") else 0)
    _txt=("1H" if spec.period==1 else "2H")+" "+str(int(round(g.raw_event.time_min)))+"'"
    _dump={"schema":"kick_goalclip_v1","fps":int(FPS),"nf":int(NF),"ltr":bool(ltr),"period":int(spec.period),"goal_side":GOAL_SIDE,"is_goal":bool(IS_GOAL),"set_piece":bool(SETPIECE_OK),"is_penalty":bool(_IS_PEN),"is_own_goal":bool(_IS_OG),"is_corner_led":bool(_CORNER_LED),"clock":{"period_label":("1H" if spec.period==1 else "2H"),"minute":int(round(g.raw_event.time_min)),"text":_txt},"score":{"home_post":int(GOAL_SH),"away_post":int(GOAL_SA),"home_pre":int(_preh),"away_pre":int(_prea),"home_atk_dir":float(_HOME_ATK)},"scorer":{"name":str(getattr(g,"player_name","") or ""),"descriptor":("Own goal" if _IS_OG else ("Goal (pen.)" if _IS_PEN else "Goal")),"xg":round(float(SHOT_XG or 0.0),2)},"teams":{"home":{"id":str(hid),"icon":"home","kit":KOR},"away":{"id":str(aid),"icon":"away","kit":CZE}},"mouth":[float(mouth[0]),float(mouth[1])],"marks":{"shot_f":int(NF-1),"goal_f":int(NF-1),"checker_kick_f":int(_kick_f)},"frames":frames}
    _dj.dump(_dump,open(_wos.environ["PP_DUMP_JSON"],"w",encoding="utf-8"),ensure_ascii=False)
    raise SystemExit(0)
'''
code = patch(code, 'GSTART=next((i for i,v in enumerate(VID) if v[5]),len(VID))', DUMP_HOOK, "dump_hook")

open(TMP, "w", encoding="utf-8").write(code)
print(f"temp written ({len(code)} chars) -> rendering --film clip {CLIP} ...")
env = dict(os.environ, PP_STADIUM="1", PP_SPONSOR="0", FILM_LANG="en")
rc = 1
try:
    rc = subprocess.run([sys.executable, TMP, "--key", KEY, "--clip", CLIP, "--film"], cwd=TIER5, env=env).returncode
finally:
    if os.path.exists(TMP):
        os.remove(TMP)
if DUMP:
    if rc == 0 and os.path.exists(DUMP):
        import json as _j
        _d = _j.load(open(DUMP))
        print(f"OK (json) -> {DUMP}  nf={_d['nf']} frames={len(_d['frames'])} goal_side={_d['goal_side']} set_piece={_d['set_piece']}")
    else:
        print("dump failed, rc", rc)
        sys.exit(rc or 1)
else:
    src_mp4 = os.path.join(WORK, f"30_sequence_clip{CLIP}_3d.mp4")
    if rc == 0 and os.path.exists(src_mp4):
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        shutil.copy(src_mp4, OUT)
        print("OK ->", OUT)
    else:
        print("render failed, rc", rc)
        sys.exit(rc or 1)
