"""Figure library: drawings with a given layer (student) and an answer layer (key)."""
from .core import BLACK, RED, Figure, figure, load_module, render_all, trim
from .geometry import (
    P, angle_deg, congruence_statement, congruent_pair, correspondence, dist, fit_rigid, is_rigid_image, midpoint,
    needs_reflection, orientation, reflect, rotate, rotation_build, ssa_triangles, translate, vertex_directions,
)

__all__ = [
    "BLACK", "RED", "Figure", "figure", "load_module", "render_all", "trim",
    "P", "angle_deg", "congruence_statement", "congruent_pair", "correspondence", "dist", "fit_rigid",
    "is_rigid_image", "midpoint", "needs_reflection", "orientation", "reflect", "rotate", "rotation_build",
    "ssa_triangles", "translate", "vertex_directions",
]
