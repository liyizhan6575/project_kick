"""Manim-based football animation utilities.

Modules are deliberately NOT imported here. Importing manim is expensive (it pulls in cairo and
ffmpeg bindings), and `geometry` is intentionally manim-free — an eager re-export would force the
whole rendering stack on anyone who only wanted the maths. Import what you need directly:

    from football_visuals.animations.geometry import voronoi_cells   # pure numpy, no manim
    from football_visuals.animations.pitch import StandardPitch
    from football_visuals.animations.voronoi import VoronoiManager
    from football_visuals.animations.metric_surface import MetricSurface

The parent package `football_visuals` has no ``__init__.py`` on purpose (PEP 420), so importing
``football_visuals.kick_style`` never reaches this subpackage and never imports manim.
"""
