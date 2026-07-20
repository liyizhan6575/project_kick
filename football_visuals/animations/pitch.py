"""A FIFA-dimension football pitch as a manim `VGroup`, plus the coordinate conversions that map
data-feed coordinates onto it.

This module owns the *drawing* and the *coordinate frame*. The tessellation maths lives in
`geometry`, which imports no manim at all — so pitch-control geometry can be computed and tested
without building a scene graph.
"""
from manim import *
import math

import numpy as np

from .geometry import rectangle, voronoi_cells

__all__ = ["StandardPitch"]


class StandardPitch(VGroup):
    """Standard 105x68 m pitch. `scale` converts metres to manim units.

    Orientation is either "horizontal" (length along x) or "vertical" (length along y); every
    coordinate helper honours it, so callers work in pitch metres and never branch on it.
    """

    # FIFA constants (metres)
    DIMS = {
        "length": 105,
        "width": 68,
        "pa_depth": 16.5,
        "pa_width": 40.32,
        "ga_depth": 5.5,
        "ga_width": 18.32,
        "penalty_spot": 11,
        "center_circle": 9.15,
    }

    def __init__(self, scale=0.08, orientation="horizontal", **kwargs):
        super().__init__(**kwargs)
        # Named pitch_scale so it doesn't shadow Mobject.scale()
        self.pitch_scale = scale
        self.orientation = orientation
        self.dims = dict(self.DIMS)

    # ── coordinate conversion ────────────────────────────────────────────────────────────────
    def to_coord(self, x, y):
        """Map pitch metres (origin at the centre spot) to a manim vector."""
        if self.orientation == "vertical":
            # Vertical: length runs along y, width along x (inverted for the standard view)
            return np.array([-y * self.pitch_scale, x * self.pitch_scale, 0])
        return np.array([x * self.pitch_scale, y * self.pitch_scale, 0])

    def wyscout_to_meters(self, x_ws, y_ws):
        """Wyscout 0-100 coordinates -> pitch metres (Wyscout's y axis is inverted)."""
        x_m = (x_ws / 100.0 - 0.5) * self.dims["length"]
        y_m = (0.5 - y_ws / 100.0) * self.dims["width"]
        return x_m, y_m

    def wyscout_to_manim(self, x_ws, y_ws):
        """Wyscout 0-100 coordinates -> manim vector."""
        return self.to_coord(*self.wyscout_to_meters(x_ws, y_ws))

    def extent(self):
        """(width, height) of the pitch in manim units, already accounting for orientation."""
        length = self.dims["length"] * self.pitch_scale
        width = self.dims["width"] * self.pitch_scale
        return (length, width) if self.orientation == "horizontal" else (width, length)

    def boundary_polygon(self):
        """The touchline rectangle as a polygon, in manim units, centred on the origin."""
        w, h = self.extent()
        return rectangle(w / 2, h / 2)

    def get_voronoi_cells(self, points_ws):
        """Voronoi cells (clipped to the touchlines) for a list of Wyscout points."""
        sites = [self.wyscout_to_manim(x, y) for x, y in points_ws]
        return voronoi_cells(sites, self.boundary_polygon())

    # ── drawing ──────────────────────────────────────────────────────────────────────────────
    def draw_base_pitch(self, stroke_color=WHITE, stroke_width=3):
        """Add the standard lines and markings to this group, and return self."""
        d = self.dims
        l, w = d["length"], d["width"]
        horizontal = self.orientation == "horizontal"

        # 1. Main boundary & halfway line
        pitch_w, pitch_h = self.extent()
        boundary = Rectangle(
            width=pitch_w, height=pitch_h,
            stroke_color=stroke_color, stroke_width=stroke_width,
        )
        # to_coord handles the orientation swap, so the same pitch-frame endpoints
        # work for both orientations
        halfway = Line(
            self.to_coord(0, -w / 2), self.to_coord(0, w / 2),
            stroke_color=stroke_color, stroke_width=stroke_width,
        )

        # 2. Centre markings
        center_circle = Circle(
            radius=d["center_circle"] * self.pitch_scale,
            color=stroke_color, stroke_width=stroke_width,
        )
        center_spot = Dot(ORIGIN, color=stroke_color, radius=0.04)

        # 3. Penalty and goal areas
        pa_w, pa_h = d["pa_depth"] * self.pitch_scale, d["pa_width"] * self.pitch_scale
        ga_w, ga_h = d["ga_depth"] * self.pitch_scale, d["ga_width"] * self.pitch_scale

        pa_l = Rectangle(
            width=pa_w if horizontal else pa_h,
            height=pa_h if horizontal else pa_w,
            stroke_color=stroke_color, stroke_width=stroke_width,
        ).move_to(self.to_coord(-l / 2 + d["pa_depth"] / 2, 0))

        ga_l = Rectangle(
            width=ga_w if horizontal else ga_h,
            height=ga_h if horizontal else ga_w,
            stroke_color=stroke_color, stroke_width=stroke_width,
        ).move_to(self.to_coord(-l / 2 + d["ga_depth"] / 2, 0))

        pa_r = pa_l.copy().move_to(self.to_coord(l / 2 - d["pa_depth"] / 2, 0))
        ga_r = ga_l.copy().move_to(self.to_coord(l / 2 - d["ga_depth"] / 2, 0))

        # 4. Penalty spots & arcs
        ps_l = Dot(self.to_coord(-l / 2 + d["penalty_spot"], 0), color=stroke_color, radius=0.04)
        ps_r = Dot(self.to_coord(l / 2 - d["penalty_spot"], 0), color=stroke_color, radius=0.04)

        # Visible part of the 9.15 m circle around the spot that falls outside the
        # penalty area: half-angle = arccos((16.5 - 11) / 9.15)
        arc_angle = 2 * math.acos((d["pa_depth"] - d["penalty_spot"]) / d["center_circle"])
        arc_rad = d["center_circle"] * self.pitch_scale

        penalty_arc_l = Arc(
            radius=arc_rad,
            start_angle=-arc_angle / 2 if horizontal else PI / 2 - arc_angle / 2,
            angle=arc_angle, stroke_color=stroke_color, stroke_width=stroke_width,
        ).shift(ps_l.get_center())

        penalty_arc_r = Arc(
            radius=arc_rad,
            start_angle=PI - arc_angle / 2 if horizontal else -PI / 2 - arc_angle / 2,
            angle=arc_angle, stroke_color=stroke_color, stroke_width=stroke_width,
        ).shift(ps_r.get_center())

        self.add(
            boundary, halfway, center_circle, center_spot,
            pa_l, pa_r, ga_l, ga_r, ps_l, ps_r, penalty_arc_l, penalty_arc_r,
        )
        return self
