"""Voronoi (pitch-control) animation driver.

Wraps a `StandardPitch` and a manim `Scene` to deploy players, tessellate the pitch between
them, and play back a tracking sequence frame by frame.

Expected dataframe columns: `frame`, `x`, `y` (Wyscout 0-100), `team`, `player`.
"""
from manim import *

__all__ = ["VoronoiManager"]

# ── shared visual constants: one place to retune the look of every method below ──
PLAYER_RADIUS = 0.1
PLAYER_STROKE_WIDTH = 2
BALL_RADIUS = 0.07
CELL_STROKE_WIDTH = 1
CELL_ALPHA = 0.28

Z_CELLS, Z_PLAYERS, Z_BALL = -1, 10, 20

PLAYER_TEAMS = ("attack", "defense")


class VoronoiManager:
    def __init__(self, scene, pitch, attack_color=ORANGE, defense_color=BLUE_E):
        self.scene = scene
        self.pitch = pitch
        self.attack_color = attack_color
        self.defense_color = defense_color
        self.alpha = CELL_ALPHA

        self.player_dots = {}
        self.polygons = VGroup()
        self.ball = None

    # ── construction helpers ─────────────────────────────────────────────────────────────────
    def _cell_polygons(self, sites, colors):
        """Tessellate `sites` and return the cells as a styled VGroup.

        Degenerate cells (fewer than 3 vertices, i.e. clipped away entirely) are dropped, so the
        colour list is zipped against the cells before filtering — order is preserved.
        """
        cells = self.pitch.get_voronoi_cells(sites)
        return VGroup(*[
            Polygon(
                *cell,
                fill_color=color, fill_opacity=self.alpha,
                stroke_width=CELL_STROKE_WIDTH, stroke_color=WHITE,
            ).set_z_index(Z_CELLS)
            for cell, color in zip(cells, colors) if len(cell) >= 3
        ])

    def _player_dot(self, pos, color):
        return Dot(
            self.pitch.wyscout_to_manim(*pos),
            color=color, radius=PLAYER_RADIUS,
            stroke_width=PLAYER_STROKE_WIDTH, stroke_color=WHITE,
        ).set_z_index(Z_PLAYERS)

    def get_frame_data(self, df, frame_id):
        """Split one frame into (players, ball_pos).

        Convention: a row whose `team` is "attack" or "defense" is a player; ANY other value
        (including blank) is taken to be the ball, and the last such row in the frame wins.
        """
        frame = df[df["frame"] == frame_id]
        players, ball_pos = [], None

        for _, row in frame.iterrows():
            team = str(row.get("team", "")).strip().lower()
            pos = (row["x"], row["y"])
            if team in PLAYER_TEAMS:
                players.append({
                    "pos": pos,
                    "color": self.attack_color if team == "attack" else self.defense_color,
                    "id": row.get("player", -1),
                    "team": team,
                })
            else:
                ball_pos = pos
        return players, ball_pos

    # ── entry animations ─────────────────────────────────────────────────────────────────────
    def animate_intro_one_by_one(self, df, deploy_time=0.4, frame_id=0):
        """Deploy players one at a time, alternating teams, re-tessellating after each."""
        players, _ = self.get_frame_data(df, frame_id)

        attackers = [p for p in players if p["team"] == "attack"]
        defenders = [p for p in players if p["team"] == "defense"]

        # Alternate defender/attacker, then append whichever side has players left over.
        interleaved = [p for pair in zip(defenders, attackers) for p in pair]
        interleaved += defenders[len(attackers):] + attackers[len(defenders):]

        current_sites, current_colors = [], []
        self.polygons = VGroup()

        for p in interleaved:
            dot = self._player_dot(p["pos"], p["color"])
            current_sites.append(p["pos"])
            current_colors.append(p["color"])
            self.player_dots[(p["team"], p["id"])] = dot

            new_vgroup = self._cell_polygons(current_sites, current_colors)

            if len(self.polygons) == 0:
                self.polygons.become(new_vgroup)
                self.scene.play(FadeIn(dot), FadeIn(self.polygons), run_time=deploy_time)
            else:
                self.scene.play(
                    FadeIn(dot),
                    self.polygons.animate.become(new_vgroup),
                    run_time=deploy_time,
                )

    def display_direct(self, df, frame_id=0, run_time=1):
        """Fade in every player and the full tessellation at once."""
        players, _ = self.get_frame_data(df, frame_id)
        sites = [p["pos"] for p in players]
        colors = [p["color"] for p in players]

        dots = []
        for p in players:
            dot = self._player_dot(p["pos"], p["color"])
            self.player_dots[(p["team"], p["id"])] = dot
            dots.append(dot)

        self.polygons = self._cell_polygons(sites, colors)
        self.scene.play(FadeIn(VGroup(*dots)), FadeIn(self.polygons), run_time=run_time)

    # ── playback ─────────────────────────────────────────────────────────────────────────────
    def run_animation(self, df, fps=25):
        """Step through every frame, updating cells, players and ball in place.

        Uses `.become()` rather than re-adding mobjects so nothing ghosts between frames.
        """
        frames = sorted(df["frame"].unique())

        # Works standalone too: attach the polygon group if no intro method ran
        if self.polygons not in self.scene.mobjects:
            self.scene.add(self.polygons)

        for f in frames:
            players, ball_pos = self.get_frame_data(df, f)
            sites = [p["pos"] for p in players]
            colors = [p["color"] for p in players]

            self.polygons.become(self._cell_polygons(sites, colors))

            for p in players:
                key = (p["team"], p["id"])
                if key in self.player_dots:
                    self.player_dots[key].move_to(self.pitch.wyscout_to_manim(*p["pos"]))
                else:
                    dot = self._player_dot(p["pos"], p["color"])
                    self.player_dots[key] = dot
                    self.scene.add(dot)

            if ball_pos:
                b_pos = self.pitch.wyscout_to_manim(*ball_pos)
                if self.ball is None:
                    self.ball = Dot(b_pos, color=WHITE, radius=BALL_RADIUS).set_z_index(Z_BALL)
                    self.scene.add(self.ball)
                else:
                    self.ball.move_to(b_pos)

            self.scene.wait(1 / fps)
