"""
=======================
Opta event processor for the pitch pilot pipeline.

For every relevant Opta event this module emits one dict record containing:
  - Full tactical context  (chain, location, outcome, qualifiers)
  - An inference feature vector ('feat') for pass/shot events in regulation

Import
------
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))   # if notebook is in a subfolder
    from opta_event_processor import (
        OptaEventProcessor, dedup_opta_events, INFERENCE_EVENT_TYPES
    )

Quick usage
-----------
    clean   = dedup_opta_events(raw_events)
    stream  = OptaEventProcessor(h_id="<home_contestantId>")
    records = [r for ev in clean if (r := stream.process(ev)) is not None]

    # Inference features only (regulation pass/shot)
    import numpy as np
    feats = np.stack([r["feat"] for r in records if r["feat"] is not None])

    # All tactical events for FLARE triggers
    tactical = [r for r in records if not r["is_passthrough"]]

Output record keys (24)
-----------------------
IDENTITY
    event_id      str         e["id"]  (deduped logical event id)
    ts            int         seconds since kick-off  (timeMin*60 + timeSec)
    minute        float       timeMin + timeSec / 60
    period_id     int         1=H1  2=H2  3=ET1  4=ET2  5=Pens
    type_id       int         Opta typeId

PARTICIPANT
    p_id          str|None    opPlayerId
    p_name        str|None    playerName
    t_id          str         contestantId
    team_side     float|None  +1.0=home  -1.0=away  (None for passthrough)
    is_passthrough bool       True for typeId 18-21 (substitutions)

MATCH STATE  — POST-event score
    score_home    int         home goals after this event
    score_away    int         away goals after this event
    is_own_goal   bool        typeId==16 and qualifier 28 present

POSSESSION CHAIN  — None for passthrough events
    chain_id      int         monotonic; increments on turnover or set-piece start
    chain_len     int         passes in current chain (typeId=1 only)
    play_pattern  str         "Regular Play" | "From Corner" | "From Free Kick" |
                              "From Throw-in" | "From Goal Kick" | "From Kick Off"

LOCATION  — normalised [0, 1]  (None for passthrough)
    start_x       float       x / 100
    start_y       float       y / 100
    end_x         float|None  qualifier 140 / 100  (passes only)
    end_y         float|None  qualifier 141 / 100  (passes only)
    dx            float|None  end_x - start_x      (passes only)

RAW
    outcome       int|None    e["outcome"]  (None for passthrough)
    quals         dict        {qualifierId_str: value}

INFERENCE FEATURE
    feat          np.ndarray  shape (14,) float32  — regulation pass/shot only
                  None        all other events

    feat column layout (matches finalScore COL_NAMES):
      0  event_type   0.0=pass  1.0=shot
      1  x_norm       start_x
      2  y_norm       start_y
      3  team_side    +1=home  -1=away
      4  t_match      minute / 90, clipped [0, 1]
      5  score_home   PRE-event home goals, capped 5  ← intentionally pre-event
      6  score_away   PRE-event away goals, capped 5  ← intentionally pre-event
      7  chain_len    chain_len / CHAIN_CAP
      8  t_since      minutes since last pass / T_SINCE_CAP
      9  end_x        pass end x / 100  (0.0 for shots)
     10  end_y        pass end y / 100  (0.0 for shots)
     11  dx           end_x - start_x  (0.0 for shots)
     12  is_goal      1.0 if typeId==16 regular goal  (0.0 otherwise)
     13  pass_subtype {0,1,2,3,4}  first pass of chain only; 0 elsewhere
                      0=open/kickoff  1=corner  2=free kick
                      3=throw-in      4=goal kick

    NOTE: feat[5/6] are PRE-event; dict score_home/away are POST-event.
          This distinction is intentional: feat matches training convention.
"""

import numpy as np

# ── Event type taxonomy ────────────────────────────────────────────────────────

# Tactical events: produce a full stream record with chain/location context
TACTICAL_EVENT_TYPES = {
    1,   # Pass
    2,   # Offside Pass
    3,   # Take On
    4,   # Foul
    5,   # Out
    6,   # Corner Awarded
    7,   # Tackle
    8,   # Interception
    10,  # Save
    11,  # Claim
    12,  # Clearance
    13,  # Miss (shot off target)
    14,  # Post (shot hits post)
    15,  # Blocked Shot
    16,  # Goal  (incl. own goals — handled via qualifier 28)
    17,  # Card
    41,  # Ball Recovery
    44,  # Aerial
    45,  # Challenge
    49,  # Ball Touch
    50, 52, 54, 55, 59, 61, 74, 83,
}

# Passthrough events: substitutions — emitted as-is, no chain/location
PASSTHROUGH_EVENT_TYPES = {
    18,  # Player Off
    19,  # Player On
    20,  # Player Retired
    21,  # Player Returned
}

# Inference feature events: subset of tactical; produce 14-float feat array
INFERENCE_EVENT_TYPES = {1, 13, 14, 15, 16}   # pass + all shot types

# ── Inference feature constants (must match finalScore Block 1) ────────────────
CHAIN_CAP     = 30
T_SINCE_CAP   = 2.0
MAX_GOALS     = 5
MATCH_MINUTES = 90.0
EVT_PASS      = 0
EVT_SHOT      = 1

# Opta qualifier IDs
_Q_KICKOFF   = "279"
_Q_GOALKICK  = "124"
_Q_CORNER    = "6"
_Q_FREEKICK  = "5"
_Q_THROW     = "107"
_Q_OWN_GOAL  = "28"

# Play-pattern string → pass_subtype float (matches finalScore PASS_SUBTYPE values)
_PATTERN_SUBTYPE = {
    "From Corner"   : 1.0,
    "From Free Kick": 2.0,
    "From Throw-in" : 3.0,
    "From Goal Kick": 4.0,
}


# ── Helper functions ───────────────────────────────────────────────────────────

def _parse_quals(ev: dict) -> dict:
    """Return {qualifierId_str: value} from any Opta event shape."""
    raw = ev.get("qualifier", ev.get("qualifiers", []))
    if isinstance(raw, dict):
        raw = [raw]
    return {
        str(q.get("qualifierId")): q.get("value")
        for q in raw if isinstance(q, dict)
    }


def _detect_play_pattern(quals: dict, is_turnover: bool, prev: str) -> str:
    """
    Detect play pattern from Opta qualifiers.
    Qualifiers are checked BEFORE the is_turnover flag so that goal kicks
    and corners (which are always turnovers) are correctly classified.
    """
    if _Q_KICKOFF  in quals: return "From Kick Off"
    if _Q_GOALKICK in quals: return "From Goal Kick"
    if _Q_CORNER   in quals: return "From Corner"
    if _Q_FREEKICK in quals: return "From Free Kick"
    if _Q_THROW    in quals: return "From Throw-in"
    if is_turnover:          return "Regular Play"
    return prev


def dedup_opta_events(raw_events: list) -> list:
    """
    Dedup raw Opta event list by logical event id (e["id"]).
    Keeps the revision with the highest seqId (most recent update).
    Returns events sorted chronologically: periodId → timeMin → timeSec → seqId.

    Always call this before feeding events to OptaEventProcessor.
    """
    raw_sorted = sorted(raw_events, key=lambda e: e["seqId"])
    best = {}
    for ev in raw_sorted:
        eid = ev["id"]
        if eid not in best or ev["seqId"] > best[eid]["seqId"]:
            best[eid] = ev
    return sorted(
        best.values(),
        key=lambda e: (e["periodId"], e["timeMin"], e["timeSec"], e["seqId"])
    )


# ── Main class ─────────────────────────────────────────────────────────────────

class OptaEventProcessor:
    """
    Stateful Opta event processor. Feed deduped events one at a time via
    .process(ev). Call .reset() between matches when reusing the instance.

    Parameters
    ----------
    h_id : str
        contestantId of the home team.
    """

    def __init__(self, h_id: str):
        self.h_id = h_id

        # Score state
        self.home_goals = 0
        self.away_goals = 0

        # Chain state (updated on all tactical events)
        self.chain_id     = 0
        self.chain_len    = 0           # passes in current chain
        self.play_pattern = "Regular Play"
        self.last_team    = None

        # Timing state (regulation pass/shot inference only)
        self.last_pass_time = None      # minutes, for t_since calculation

    def reset(self):
        """Reset all state. Call between matches when reusing the instance."""
        self.__init__(self.h_id)

    def _chain_reset(self, new_pattern: str):
        self.chain_id      += 1
        self.chain_len      = 0
        self.play_pattern   = new_pattern
        self.last_pass_time = None

    def process(self, ev: dict):
        """
        Process a single deduped Opta event.

        Returns
        -------
        dict
            One record per relevant event (see module docstring for format).
        None
            If the event is skipped (not in TACTICAL or PASSTHROUGH types,
            or period_id in {14, 16}).
        """
        type_id   = int(ev.get("typeId", 0))
        period_id = int(ev.get("periodId", 1))
        t_id      = ev.get("contestantId")

        # Skip pre/post-match stubs
        if period_id in {14, 16}:
            return None

        quals  = _parse_quals(ev)
        minute = float(ev.get("timeMin", 0)) + float(ev.get("timeSec", 0)) / 60.0
        ts     = int(ev.get("timeMin", 0)) * 60 + int(ev.get("timeSec", 0))

        # ── Passthrough: substitutions ─────────────────────────────────────────
        if type_id in PASSTHROUGH_EVENT_TYPES:
            return {
                "event_id"      : ev.get("id"),
                "ts"            : ts,
                "minute"        : minute,
                "period_id"     : period_id,
                "type_id"       : type_id,
                "p_id"          : ev.get("opPlayerId"),
                "p_name"        : ev.get("playerName"),
                "t_id"          : t_id,
                "team_side"     : None,
                "is_passthrough": True,
                "score_home"    : self.home_goals,
                "score_away"    : self.away_goals,
                "is_own_goal"   : False,
                "chain_id"      : None,
                "chain_len"     : None,
                "play_pattern"  : None,
                "start_x"       : None,
                "start_y"       : None,
                "end_x"         : None,
                "end_y"         : None,
                "dx"            : None,
                "outcome"       : None,
                "quals"         : quals,
                "feat"          : None,
            }

        if type_id not in TACTICAL_EVENT_TYPES:
            return None

        # ── Own goal detection ─────────────────────────────────────────────────
        # typeId=16 + qualifier 28: contestantId is the DEFENDING team,
        # so the goal is credited to the OTHER side.
        is_own_goal = (type_id == 16 and _Q_OWN_GOAL in quals)
        team_side   = 1.0 if t_id == self.h_id else -1.0

        # ── Score: snapshot PRE-event for feat, then update ────────────────────
        pre_score_h = self.home_goals
        pre_score_a = self.away_goals

        if type_id == 16:
            # XOR: own goal flips who benefits
            if (t_id == self.h_id) ^ is_own_goal:
                self.home_goals += 1
            else:
                self.away_goals += 1

        # ── Chain state ────────────────────────────────────────────────────────
        is_turnover = (self.last_team is not None and t_id != self.last_team)
        new_pattern = _detect_play_pattern(quals, is_turnover, self.play_pattern)

        if self.last_team is None or is_turnover or new_pattern != self.play_pattern:
            self._chain_reset(new_pattern)

        if type_id == 1:
            self.chain_len = min(self.chain_len + 1, CHAIN_CAP)

        self.last_team = t_id

        # ── Location ──────────────────────────────────────────────────────────
        start_x = float(ev.get("x", 0.0)) / 100.0
        start_y = float(ev.get("y", 0.0)) / 100.0

        if type_id == 1:
            end_x = float(quals.get("140", ev.get("x", 0.0))) / 100.0
            end_y = float(quals.get("141", ev.get("y", 0.0))) / 100.0
            dx    = end_x - start_x
        else:
            end_x = end_y = dx = None

        # ── Inference feature ──────────────────────────────────────────────────
        # Produced only for regulation (period 1 or 2) pass/shot events
        # that are NOT own goals.
        feat = None
        if period_id in {1, 2} and type_id in INFERENCE_EVENT_TYPES and not is_own_goal:
            t_match = float(np.clip(minute / MATCH_MINUTES, 0.0, 1.0))
            t_since = (
                0.0 if self.last_pass_time is None
                else float(np.clip(minute - self.last_pass_time, 0.0, T_SINCE_CAP))
            )

            # Shared prefix: cols 0–8 identical for pass and shot
            feat_common = [
                0.0,                                    # col 0: event_type — filled below
                start_x, start_y, team_side, t_match,
                float(min(pre_score_h, MAX_GOALS)),
                float(min(pre_score_a, MAX_GOALS)),
                float(self.chain_len) / CHAIN_CAP,
                t_since / T_SINCE_CAP,
            ]

            if type_id == 1:   # Pass
                pass_sub = (
                    _PATTERN_SUBTYPE.get(self.play_pattern, 0.0)
                    if self.chain_len == 1 else 0.0
                )
                feat_common[0] = float(EVT_PASS)
                feat = np.array(feat_common + [end_x, end_y, dx, 0.0, pass_sub],
                                dtype=np.float32)
                self.last_pass_time = minute

            else:   # Shot (typeId 13, 14, 15, 16)
                feat_common[0] = float(EVT_SHOT)
                feat = np.array(feat_common + [0.0, 0.0, 0.0,
                                               1.0 if type_id == 16 else 0.0, 0.0],
                                dtype=np.float32)

        return {
            "event_id"      : ev.get("id"),
            "ts"            : ts,
            "minute"        : minute,
            "period_id"     : period_id,
            "type_id"       : type_id,
            "p_id"          : ev.get("opPlayerId"),
            "p_name"        : ev.get("playerName"),
            "t_id"          : t_id,
            "team_side"     : team_side,
            "is_passthrough": False,
            "score_home"    : self.home_goals,
            "score_away"    : self.away_goals,
            "is_own_goal"   : is_own_goal,
            "chain_id"      : self.chain_id,
            "chain_len"     : self.chain_len,
            "play_pattern"  : self.play_pattern,
            "start_x"       : start_x,
            "start_y"       : start_y,
            "end_x"         : end_x,
            "end_y"         : end_y,
            "dx"            : dx,
            "outcome"       : (int(ev["outcome"]) if ev.get("outcome") is not None else None),
            "quals"         : quals,
            "feat"          : feat,
        }