"""A 2.5D bar surface over a pitch: one prism per matrix cell, height and colour driven by value.

Useful for rendering any gridded metric (xT, pitch control, occupancy) as relief over the pitch.
"""
from manim import *
import numpy as np

from .tokens import KICK, seq, KICK_SEQ_STOPS, pt_to_px

__all__ = ["MetricSurface"]


def _pitch_extent(pitch):
    """(width, height) of a pitch in manim units.

    Prefers `StandardPitch.extent()`; the remaining branches keep foreign pitch objects working.
    """
    if hasattr(pitch, "extent"):
        return pitch.extent()
    if hasattr(pitch, "field_width"):
        return pitch.field_width, pitch.field_height
    return pitch.width, pitch.height


class MetricSurface(VGroup):
    """A gridded metric as relief over the pitch — one prism per cell.

    House colouring is the ICE ramp: its dark end IS the panel tone, so a zero cell melts into the
    pitch and magnitude glows out of it. `ramp=` takes any `kick_tokens` stop list.

    `normalize` decides what a bar's height and colour MEAN, and the default matters:

    * ``"zero"`` (default) — scale by the maximum alone, so height is proportional to value and an
      empty cell is genuinely flat. Right for every magnitude field the repo has (xT, threat,
      occupancy, pitch control): they are non-negative with a meaningful zero.
    * ``"minmax"`` — the old behaviour, subtracting the minimum. It rescales the FLOOR to zero,
      which for a magnitude field silently promotes the quietest cell on the pitch to "no value at
      all" and lifts everything else off a false baseline — a whole pitch of blue bars where the
      data says nothing is happening. Keep it only for a signed or offset field where the minimum
      really is the reference.
    """

    def __init__(
        self,
        pitch,
        matrix,
        max_height=3.5,
        ramp=None,
        normalize="zero",
        stroke_color=KICK["figure"],
        stroke_width=pt_to_px(0.1),
        fill_opacity=0.9,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.pitch = pitch
        self.matrix = np.array(matrix, dtype=float)
        self.max_height = max_height
        self.ramp = ramp or KICK_SEQ_STOPS
        self.normalize = normalize
        self.stroke_color = stroke_color
        self.stroke_width = stroke_width
        self.fill_opacity = fill_opacity

        self._build_bars()

    def _normalized(self):
        """The matrix mapped to [0,1] under the chosen convention."""
        mat_max = float(np.max(self.matrix))
        if self.normalize == "minmax":
            mat_min = float(np.min(self.matrix))
            span = mat_max - mat_min
            return (self.matrix - mat_min) / span if span > 0 else np.zeros_like(self.matrix)
        return self.matrix / mat_max if mat_max > 0 else np.zeros_like(self.matrix)

    def _build_bars(self):
        rows, cols = self.matrix.shape

        p_width, p_height = _pitch_extent(self.pitch)

        cell_w = p_width / cols
        cell_h = p_height / rows
        # Anchor bars to wherever the pitch actually sits, not the scene origin
        pitch_center = self.pitch.get_center()

        norm_matrix = self._normalized()

        for r in range(rows):
            for c in range(cols):
                norm_val = float(norm_matrix[r, c])

                h = (norm_val * self.max_height) + 0.01
                bar_color = ManimColor(seq(norm_val, self.ramp))

                bar = Prism(dimensions=[cell_w, cell_h, h])
                bar.set_fill(bar_color, opacity=self.fill_opacity)

                if self.stroke_width > 0:
                    bar.set_stroke(color=self.stroke_color, width=self.stroke_width)
                else:
                    bar.set_stroke(width=0)

                bar.set_shade_in_3d(True)

                x = (c - cols/2 + 0.5) * cell_w
                y = ((rows - 1 - r) - rows/2 + 0.5) * cell_h
                z = h / 2

                bar.move_to(pitch_center + np.array([x, y, z]))
                self.add(bar)

    def get_growth_animation(self, run_time=2.5, lag_ratio=None, direction="bottom_up"):
        """Grow the bars out of the pitch, as a sweep across it.

        Args:
            run_time: total duration.
            lag_ratio: gap between successive bars. ``None`` (default) spreads the sweep over the
                whole run — the old default of 0.0 started every bar simultaneously, which made the
                `direction` sort below a no-op and the sweep invisible. Pass 0.0 explicitly for a
                deliberate all-at-once rise.
            direction: 'bottom_up' (near to far) or 'top_down' (far to near).
        """
        if lag_ratio is None:
            lag_ratio = min(0.02, 1.5 / max(1, len(self)))
        # Sort based on Y position (screen depth)
        if direction == "bottom_up":
            # Sort by Y ascending (Screen Bottom -> Top)
            sorted_bars = sorted(self, key=lambda m: m.get_y())
        elif direction == "top_down":
            sorted_bars = sorted(self, key=lambda m: -m.get_y())
        else:
            sorted_bars = self

        return LaggedStart(
            *[
                GrowFromPoint(
                    bar, 
                    point=np.array([bar.get_x(), bar.get_y(), 0])
                ) 
                for bar in sorted_bars
            ],
            lag_ratio=lag_ratio,
            run_time=run_time
        )