"""Computational geometry for the pitch animations — deliberately free of any manim import.

The Voronoi maths used to live inside the `StandardPitch` mobject, which meant you could not
compute a pitch-control tessellation without constructing a manim scene graph. Keeping it here
makes it reusable and testable on its own; `pitch.StandardPitch` simply delegates to it.

Points are 3D `(x, y, z)` numpy vectors (manim's convention); every test below uses only the
xy components, so the z coordinate rides along untouched.
"""
from __future__ import annotations

import numpy as np

__all__ = ["rectangle", "clip_polygon_halfspace", "voronoi_cells"]


def rectangle(half_width: float, half_height: float) -> list[np.ndarray]:
    """Axis-aligned rectangle centred on the origin, counter-clockwise, as 3D points."""
    return [np.array([x, y, 0.0]) for x, y in (
        (-half_width, -half_height), (half_width, -half_height),
        (half_width, half_height), (-half_width, half_height),
    )]


def clip_polygon_halfspace(poly, normal, offset, eps: float = 1e-9) -> list[np.ndarray]:
    """Sutherland-Hodgman clip of `poly` against the half-space {p : normal·p <= offset}.

    Returns the (possibly empty) clipped polygon. Vertices are emitted in input order, with an
    intersection point inserted wherever an edge crosses the boundary.
    """
    if not poly:
        return []
    n2 = np.asarray(normal, dtype=float)[:2]
    out: list[np.ndarray] = []
    prev = poly[-1]
    prev_in = bool(np.dot(n2, prev[:2]) <= offset + eps)
    for cur in poly:
        cur_in = bool(np.dot(n2, cur[:2]) <= offset + eps)
        if cur_in != prev_in:                       # edge crosses the boundary -> add the crossing
            edge = cur - prev
            denom = np.dot(n2, edge[:2])
            if abs(denom) > 1e-12:                  # skip edges parallel to the boundary
                t = (offset - np.dot(n2, prev[:2])) / denom
                out.append(prev + t * edge)
        if cur_in:
            out.append(cur)
        prev, prev_in = cur, cur_in
    return out


def voronoi_cells(sites, boundary, min_separation: float = 1e-7) -> list[list[np.ndarray]]:
    """Voronoi cell for each site, clipped to `boundary`.

    Built by successive half-space clipping: cell i is the boundary polygon cut by the
    perpendicular bisector between site i and every other site. That is O(n^2) in the number of
    sites, which is ample for the 22 players of a football frame and avoids a scipy dependency.

    Sites closer together than `min_separation` are skipped rather than producing a degenerate
    bisector, so duplicated coordinates cannot blow the cell away.
    """
    pts = [np.asarray(p, dtype=float) for p in sites]
    cells = []
    for i, pi in enumerate(pts):
        cell = list(boundary)
        for j, pj in enumerate(pts):
            if i == j:
                continue
            normal = pj - pi
            if np.linalg.norm(normal) < min_separation:
                continue
            midpoint = (pi + pj) / 2.0
            cell = clip_polygon_halfspace(cell, normal, float(np.dot(normal[:2], midpoint[:2])))
        cells.append(cell)
    return cells
