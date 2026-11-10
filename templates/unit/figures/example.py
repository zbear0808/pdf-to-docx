"""Figures for the example documents (lessons/example.yaml and assessments/example.yaml share the stem
`example`, so both see these names). A new document gets its own figures/<stem>.py; name its figures
f"{S}_<item>" so names never collide. Given ink is black (student and key); answer ink is red (key only)."""
import numpy as np

from lesson_builder.figures import Figure, P, dilate, dist, figure, similarity_ratio

S = "example"
CENTER = np.array((0.0, 0.0))
ABC = P((1, 0.5), (2, 0.5), (1, 1.5))
K = 2
IMG = dilate(ABC, K, center=CENTER)
assert np.isclose(similarity_ratio(ABC, IMG), K)                       # the key's scale factor
assert np.isclose(dist(CENTER, IMG[0]), K * dist(CENTER, ABC[0]))      # image is on ray PA, twice as far


@figure("dilate_abc")
def dilate_abc() -> Figure:
    """Assessment item 1: dilate triangle ABC from center P by scale factor 2. The image is the answer layer."""
    f = Figure(width_in=2.2, height_in=1.9)
    f.grid(0, 4, 0, 3)
    f.dots([CENTER])
    f.label(CENTER, "P", direction=(-1, -1))
    f.poly(ABC)
    f.dots(ABC)
    f.label_poly(ABC, "ABC")
    for b in IMG:
        f.seg(CENTER, b, layer="answer", lw=0.5, dashed=True)   # thin rays: labels may sit on them
    f.poly(IMG, layer="answer")
    f.dots(IMG, layer="answer")
    f.label_poly(IMG, ["A'", "B'", "C'"], layer="answer")
    return f
