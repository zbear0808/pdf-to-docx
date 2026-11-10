"""Figure library: drawings with a given layer (student) and an answer layer (key)."""
from .core import BLACK, RED, Figure, figure, load_module, render_all, trim
from .geometry import (
    P, angle_deg, assert_dilation, assert_distinct, assert_lengths, assert_similar, collinear,
    congruence_statement, congruent_pair, correspondence, cross2, dilate, dilation_task, dist, extend, fit_rigid,
    foot, is_parallel, is_rigid_image, law_of_sines_side, mark_congruent, mark_parallel, midpoint,
    needs_reflection, on_ray, orientation, rect_pair, reflect, reflection_build, rotate, rotation_build,
    side_splitter, signed_area, similarity_ratio, ssa_triangles, translate, triangle_from_angles, triangle_sas,
    vertex_directions,
)

__all__ = [
    "BLACK", "RED", "Figure", "figure", "load_module", "render_all", "trim",
    "P", "angle_deg", "assert_dilation", "assert_distinct", "assert_lengths", "assert_similar", "collinear",
    "congruence_statement", "congruent_pair", "correspondence", "cross2", "dilate", "dilation_task", "dist",
    "extend", "fit_rigid", "foot", "is_parallel", "is_rigid_image", "law_of_sines_side", "mark_congruent",
    "mark_parallel", "midpoint", "needs_reflection", "on_ray", "orientation", "rect_pair", "reflect",
    "reflection_build", "rotate", "rotation_build", "side_splitter", "signed_area", "similarity_ratio",
    "ssa_triangles", "translate", "triangle_from_angles", "triangle_sas", "vertex_directions",
]
