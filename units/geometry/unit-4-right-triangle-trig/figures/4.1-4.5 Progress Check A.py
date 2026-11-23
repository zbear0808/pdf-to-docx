"""Figures for assessment "4.1-4.5 Progress Check A" (assessments/4.1-4.5 Progress Check A.yaml).
Given ink (layer="given") prints on the student copy and the key; answer ink (layer="answer") is red, key only.
"""
import numpy as np

from lesson_builder.figures import Figure, P, angle_deg, dist, figure

S = '4.1-4.5 Progress Check A'


@figure(f"{S}_1")
def item1() -> Figure:
    """Right angle at the top left (top leg horizontal, vertical leg on the left); 55 degrees marked at the bottom
    vertex. From that angle the top leg is opposite and the vertical leg is adjacent, so "the vertical side is
    opposite" fails here as on the Retake (Nov 20 audit fix; was 35 degrees at the bottom right of an upright
    triangle, where the vertical leg was opposite). Key labels the three sides from the 55 degree angle."""
    v = 4 / np.tan(np.radians(55))           # vertical leg; top leg = 4
    R, T, B = P((0, v), (4, v), (0, 0))      # right angle, top right, bottom (marked)
    assert np.isclose(angle_deg(R, T, B), 90)
    assert np.isclose(angle_deg(B, R, T), 55)
    assert np.isclose(angle_deg(T, R, B), 35)
    assert np.isclose(dist(R, T) / dist(B, R), np.tan(np.radians(55)))   # opposite / adjacent from B
    tri = np.array([R, T, B])
    f = Figure(width_in=3.0, height_in=1.9)
    f.custom(lambda ax, color: None, extent=[(-2.4, -0.6), (5.4, v + 0.8)])
    f.poly(tri)
    f.right_angle(R, T, B, size=0.3)
    f.arc(B, R, T, r=0.7)
    f.angle_label(B, R, T, '$55^\\circ$', dist=1.25)
    f.side_label(R, T, 'opposite', center=B, layer="answer")
    # wide words: side_label centers them across the leg, so they sit beside it at computed spots (as before)
    f.text((-1.35, v / 2), 'adjacent', layer="answer", fixed=True)
    f.text((3.2, 0.75), 'hypotenuse', layer="answer", fixed=True)
    assert 0.75 + 0.25 < np.tan(np.radians(35)) * (3.2 - 1.2)   # 'hypotenuse' stays below the hypotenuse
    return f


@figure(f"{S}_3")
def item3() -> Figure:
    """Right triangle EDC, right angle at D; EC = 15, CD = 9, ED = x (= 12 on the key)."""
    E, D, C = P((0, 0), (12, 0), (12, 9))
    assert np.isclose(dist(E, C), 15)
    assert np.isclose(dist(C, D), 9)
    assert np.isclose(dist(E, D), 12)
    assert np.isclose(angle_deg(D, E, C), 90)
    tri = P((0, 0), (12, 0), (12, 9))
    f = Figure(width_in=2.8, height_in=2.2)
    f.poly(tri)
    f.right_angle(D, E, C, size=0.9)
    f.label_poly(tri, "EDC")
    f.side_label(E, C, '15', center=D)
    f.side_label(C, D, '9', center=E)
    f.side_label(E, D, '$x$', center=C)
    f.side_label(E, D, '$x = 12$', center=C, layer="answer", offset_pt=24)
    return f
