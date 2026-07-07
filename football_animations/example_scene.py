from manim import *
from pitch_utils import StandardPitch

# Render from the football_animations directory with:
#   manim -pqh example_scene.py VoronoiFrameScene

# Synthetic player positions in Wyscout coordinates (0-100 on both axes).
# Attack plays right-to-left in a 4-3-3; defense holds a 4-4-2 block.
ATTACK_POSITIONS = [
    (95, 50),                                    # GK
    (80, 15), (82, 38), (82, 62), (80, 85),     # back four
    (68, 30), (70, 50), (68, 70),               # midfield three
    (56, 20), (54, 50), (56, 80),               # front three
]
DEFENSE_POSITIONS = [
    (5, 50),                                     # GK
    (22, 20), (20, 40), (20, 60), (22, 80),     # back four
    (36, 18), (34, 40), (34, 60), (36, 82),     # midfield four
    (46, 38), (46, 62),                          # strikers
]


def build_voronoi_frame(pitch_scale=0.11):
    """Builds a static frame: pitch markings, Voronoi cells, and player dots."""
    pitch = StandardPitch(pitch_scale).draw_base_pitch()

    positions = ATTACK_POSITIONS + DEFENSE_POSITIONS
    colors = [ORANGE] * len(ATTACK_POSITIONS) + [BLUE_E] * len(DEFENSE_POSITIONS)

    cells = pitch.get_voronoi_cells(positions)
    polygons = VGroup(*[
        Polygon(
            *cell,
            fill_color=color, fill_opacity=0.28,
            stroke_width=1, stroke_color=WHITE,
        ).set_z_index(-1)
        for cell, color in zip(cells, colors) if len(cell) >= 3
    ])
    dots = VGroup(*[
        Dot(
            pitch.wyscout_to_manim(*pos),
            color=color, radius=0.1,
            stroke_width=2, stroke_color=WHITE,
        ).set_z_index(10)
        for pos, color in zip(positions, colors)
    ])
    return VGroup(polygons, pitch, dots)


class VoronoiFrameScene(Scene):
    def construct(self):
        self.add(build_voronoi_frame())
        self.wait(2)
