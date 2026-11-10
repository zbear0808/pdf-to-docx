"""Helpers shared by the kitchen-sink figure files (imported as `from _helpers import ...`)."""
import numpy as np

from lesson_builder.figures import Figure


def labeled_triangle(f: Figure, pts, names, layer="given"):
    """Triangle with dots and outward vertex labels on one layer. Returns the points as an array."""
    pts = np.asarray(pts, float)
    f.poly(pts, layer=layer)
    f.dots(pts, layer=layer)
    f.label_poly(pts, names, layer=layer)
    return pts
