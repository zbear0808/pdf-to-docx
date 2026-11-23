"""Figures for assessment "4.1-4.5 Progress Check Retake" (assessments/4.1-4.5 Progress Check Retake.yaml). Name each figure f"{S}_<item>".
Given ink (layer="given") prints on the student copy and the key; answer ink (layer="answer") is red, key only.
"""
import numpy as np

from lesson_builder.figures import Figure, P, angle_deg, dist, figure

S = '4.1-4.5 Progress Check Retake'


@figure(f"{S}_1")
def q1() -> Figure:
    """No letters; right angle bottom-right; 30 degrees marked at the top. Opposite = bottom leg."""
    a, r, t = P(0, 0), P(2.4, 0), P(2.4, 4.157)
    assert np.isclose(angle_deg(r, a, t), 90)
    assert abs(angle_deg(t, a, r) - 30) < 0.1
    tri = np.array([a, r, t])
    ctr = tri.mean(axis=0)
    f = Figure(width_in=2.4, height_in=2.4, key_frame="same")
    f.poly(tri)
    f.right_angle(r, a, t, size=0.3)
    f.arc(t, a, r, r=0.7)
    f.angle_label(t, a, r, '$30^\\circ$', dist=1.15)
    f.side_label(a, r, 'opposite', ctr, layer="answer")
    f.text(P(3.35, 2.08), 'adjacent', layer="answer")
    f.text(P(0.15, 2.9), 'hypotenuse', layer="answer")
    return f


@figure(f"{S}_3")
def q3() -> Figure:
    """Triangle KLM, right angle at L; KM = 17, LM = 8, KL = x = 15."""
    L, M, K = P(0, 0), P(8, 0), P(0, 15)
    assert np.isclose(dist(K, M), 17) and np.isclose(dist(L, M), 8)
    assert np.isclose(dist(K, L), 15) and np.isclose(angle_deg(L, K, M), 90)
    tri = np.array([K, L, M])
    ctr = tri.mean(axis=0)
    f = Figure(width_in=1.9, height_in=2.9)
    f.poly(tri)
    f.right_angle(L, K, M, size=1.0)
    f.label_poly(tri, "KLM")
    f.side_label(K, M, '17', ctr)
    f.side_label(L, M, '8', ctr)
    f.side_label(K, L, '$x$', ctr)
    f.text(P(-2.2, 4.0), '$x = 15$', layer="answer")
    return f
