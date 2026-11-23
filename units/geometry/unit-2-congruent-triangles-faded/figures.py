"""Unit 2 figures. Each @figure makes the student image (given layer) and, if it has an answer layer, the key image."""
from lesson_builder.figures import Figure, P, figure, reflect, rotation_build


@figure("parallelogram_build")
def parallelogram_build() -> Figure:
    # Lesson 2.1 Problem 5: triangle ABC (AC longest), rotate 180 deg about the midpoint M of AC -> parallelogram ABCD
    return rotation_build(P((0, 0), (1.1, 1.7), (4.0, 0)), names="ABC", image_name="D", width_in=2.8)


@figure("right_triangle_reflect")
def right_triangle_reflect() -> Figure:
    # Lesson 2.1 practice #3: reflect right triangle ABC across line BC; the key shows A' and the marks
    B, A, C = P((0, 0), (1.3, 0), (0, 2.2))
    A2 = reflect([A], B, C)[0]
    f = Figure(width_in=2.0, height_in=2.4)
    f.poly([A, B, C])
    f.right_angle(B, A, C)
    f.dots([A, B, C])
    f.label(A, "A", direction=(1, -0.6))
    f.label(B, "B", direction=(0, -1))
    f.label(C, "C", direction=(0, 1))
    f.seg(A2, B, layer="answer")
    f.seg(A2, C, layer="answer")
    f.dots([A2], layer="answer")
    f.label(A2, "A'", layer="answer", direction=(-1, -0.6))
    f.ticks(A, C, 1, layer="answer")
    f.ticks(A2, C, 1, layer="answer")
    f.ticks(A, B, 2, layer="answer")
    f.ticks(A2, B, 2, layer="answer")
    return f
