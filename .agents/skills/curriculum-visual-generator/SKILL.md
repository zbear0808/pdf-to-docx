---
name: curriculum-visual-generator
description: Generates high-resolution mathematical diagrams, geometry figures, statistical charts, coordinate grids, and computer science visuals using Python (Matplotlib, NumPy, Pillow) and crops assets for the Worksheet AST.
---

# Curriculum Visual Generator Skill

This skill provides comprehensive instructions, standardized visual styling, and reusable Python templates for generating high-resolution, print-ready diagrams and figures for assessments, worksheets, and lesson plans.

All generated assets are saved directly to `_temp/assets/` and auto-cropped to guarantee accurate 2D bin-packing footprint calculations.

---

## 1. Visual Styling & Rendering Standards

Every generated figure must follow these strict publication standards:

| Parameter | Standard Value | Rationale |
| :--- | :--- | :--- |
| **Resolution / DPI** | `300` | Eliminates pixelation on both high-res screens and print |
| **Primary Theme Color** | `#1F4E79` (Deep Navy) | Professional, high-contrast, matches school and district palette |
| **Highlight Color** | `#C00000` (Crimson) | For lines of reflection, transversal cut lines, key angles |
| **Secondary Color** | `#D66011` (Amber/Orange) | For transformed images ($A'B'C'$), candidate choices |
| **Shape Fill Color** | `#EBF3FA` (Very soft blue) | Subtly shades polygons without obscuring grid lines |
| **Grid / Axes Color** | `#7F7F7F` or `#D9D9D9` | Low contrast so student drawings and problem shapes stand out |
| **Font Family** | `DejaVu Sans` / `Arial` | Clean, sans-serif, widely compatible |
| **Font Size** | `9 - 11 pt` | Scaled to match standard document body text |

---

## 2. Standard Workspace Script Structure

Store all diagram generation scripts in `_temp/build/generate_figures.py` and output all images to `_temp/assets/`:

```python
import os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

# 1. Output directory
ASSET_DIR = Path("_temp/assets")
ASSET_DIR.mkdir(parents=True, exist_ok=True)

# 2. Global styling
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 9.5
plt.rcParams['axes.edgecolor'] = '#595959'
plt.rcParams['axes.linewidth'] = 0.8

# 3. Always auto-crop after saving
from worksheet_packer.image_utils import auto_crop_image

def save_and_crop(fig, filename: str):
    path = ASSET_DIR / filename
    fig.savefig(path, dpi=300, bbox_inches='tight', transparent=False, facecolor='white')
    plt.close(fig)
    # Auto-trim border whitespace
    clean_path, w, h, ar = auto_crop_image(path)
    print(f"Generated: {clean_path.name} ({w}x{h} px, AR: {ar:.3f})")
    return clean_path
```

---

## 3. Reusable Educational Visual Templates

### A. Coordinate Grid with Polygon Transformation
Used for Geometry grid problems where students translate, reflect, or rotate shapes:

```python
from matplotlib.patches import Polygon

def make_coordinate_grid_problem():
    fig, ax = plt.subplots(figsize=(4.5, 4.5), dpi=300)
    
    # Grid configuration (-6 to 6)
    ax.set_xlim(-6.5, 6.5)
    ax.set_ylim(-6.5, 6.5)
    ax.set_xticks(range(-6, 7))
    ax.set_yticks(range(-6, 7))
    ax.grid(True, which='both', color='#D9D9D9', linestyle='-', linewidth=0.7)
    
    # Axes lines
    ax.axhline(0, color='#595959', linewidth=1.2)
    ax.axvline(0, color='#595959', linewidth=1.2)
    ax.set_aspect('equal')
    
    # Original Polygon ABCD
    pts = np.array([[-4, 2], [-2, 5], [-1, 3], [-3, 1]])
    poly = Polygon(pts, closed=True, facecolor='#EBF3FA', edgecolor='#1F4E79', linewidth=2.0)
    ax.add_patch(poly)
    
    # Label vertices
    labels = ['A', 'B', 'C', 'D']
    for (x, y), l in zip(pts, labels):
        ax.plot(x, y, 'o', color='#1F4E79', markersize=4.5)
        ax.text(x - 0.45, y + 0.25, l, fontweight='bold', fontsize=10, color='#1F4E79')
        
    # Translated point A'
    ax.plot(2, -1, 's', color='#C00000', markersize=5)
    ax.text(2.2, -1.2, "$A'$", fontweight='bold', fontsize=10, color='#C00000')
    
    return save_and_crop(fig, "fig_p4_quadrilateral_grid.png")
```

---

### B. Parallel Lines Cut by Transversal with Angle Arcs
Used for Geometry angle relationship and proof items:

```python
from matplotlib.patches import Arc

def make_parallel_transversal():
    fig, ax = plt.subplots(figsize=(4.5, 3.2), dpi=300)
    
    # Parallel lines x and y
    ax.plot([-3, 5], [2, 2], color='#1F4E79', linewidth=1.8)
    ax.plot([-3, 5], [-1, -1], color='#1F4E79', linewidth=1.8)
    ax.text(5.2, 1.9, "$\ell_1$", fontsize=10, color='#1F4E79', fontweight='bold')
    ax.text(5.2, -1.1, "$\ell_2$", fontsize=10, color='#1F4E79', fontweight='bold')
    
    # Transversal t
    ax.plot([-1.5, 3.5], [-2.5, 3.5], color='#C00000', linewidth=1.8)
    ax.text(3.6, 3.4, "$t$", fontsize=10, color='#C00000', fontweight='bold')
    
    # Intersection centers: (2.25, 2.0) and (-0.25, -1.0)
    # Add angle labels
    ax.text(1.7, 2.2, "$a^\\circ$", fontsize=9, fontweight='bold')
    ax.text(2.6, 2.2, "$b^\\circ$", fontsize=9, fontweight='bold')
    ax.text(1.7, 1.6, "$c^\\circ$", fontsize=9, fontweight='bold')
    ax.text(2.6, 1.6, "$d^\\circ$", fontsize=9, fontweight='bold')
    
    ax.text(-0.8, -0.8, "$e^\\circ$", fontsize=9, fontweight='bold')
    ax.text(0.1, -0.8, "$f^\\circ$", fontsize=9, fontweight='bold')
    ax.text(-0.8, -1.4, "$g^\\circ$", fontsize=9, fontweight='bold')
    ax.text(0.1, -1.4, "$h^\\circ$", fontsize=9, fontweight='bold')
    
    ax.set_xlim(-3, 6)
    ax.set_ylim(-3, 4)
    ax.axis('off')
    
    return save_and_crop(fig, "fig_p8_parallel_transversal.png")
```

---

### C. AP Statistics: Comparative Boxplots
Used for AP Statistics data display and comparison questions:

```python
def make_comparative_boxplots():
    fig, ax = plt.subplots(figsize=(5.0, 2.2), dpi=300)
    
    # Synthetic clean data for two treatments
    np.random.seed(42)
    group_a = np.random.normal(loc=72, scale=8, size=40)
    group_b = np.random.normal(loc=84, scale=6, size=40)
    
    bp = ax.boxplot([group_a, group_b], vert=False, patch_artist=True,
                    labels=['Control Group', 'Treatment Group'],
                    widths=0.45)
    
    # Styling colors
    colors = ['#EBF3FA', '#FFF2CC']
    border_colors = ['#1F4E79', '#D66011']
    for patch, c, bc in zip(bp['boxes'], colors, border_colors):
        patch.set_facecolor(c)
        patch.set_edgecolor(bc)
        patch.set_linewidth(1.5)
        
    for median in bp['medians']:
        median.set_color('#C00000')
        median.set_linewidth(1.8)
        
    ax.set_xlabel("Exam Score (Points)", fontsize=9.5)
    ax.grid(axis='x', color='#E0E0E0', linestyle='--', linewidth=0.7)
    
    return save_and_crop(fig, "fig_p2_comparative_boxplots.png")
```

---

### D. Geometry Inscribed Polygons & Symmetries
Used for rotational and line symmetry problems:

```python
from matplotlib.patches import Circle, RegularPolygon

def make_regular_hexagon():
    fig, ax = plt.subplots(figsize=(3.5, 3.5), dpi=300)
    
    # Bounding circle
    circle = Circle((0, 0), radius=1.0, facecolor='none', edgecolor='#7F7F7F', linestyle='--', linewidth=1.0)
    ax.add_patch(circle)
    
    # Inscribed regular hexagon
    hex_patch = RegularPolygon((0, 0), numVertices=6, radius=1.0, orientation=0,
                               facecolor='#EBF3FA', edgecolor='#1F4E79', linewidth=2.0)
    ax.add_patch(hex_patch)
    
    # Center H
    ax.plot(0, 0, 'o', color='#C00000', markersize=5)
    ax.text(0.08, -0.05, "$H$", fontsize=10, fontweight='bold', color='#C00000')
    
    # Vertex labels A-F
    labels = ['A', 'B', 'C', 'D', 'E', 'F']
    angles = np.linspace(np.pi/6, 2*np.pi + np.pi/6, 7)[:-1]
    for ang, l in zip(angles, labels):
        x = 1.18 * np.cos(ang)
        y = 1.18 * np.sin(ang)
        ax.text(x - 0.06, y - 0.06, l, fontsize=10, fontweight='bold', color='#1F4E79')
        # Center radii
        ax.plot([0, np.cos(ang)], [0, np.sin(ang)], color='#7F7F7F', linestyle=':', linewidth=0.9)
        
    ax.set_xlim(-1.4, 1.4)
    ax.set_ylim(-1.4, 1.4)
    ax.set_aspect('equal')
    ax.axis('off')
    
    return save_and_crop(fig, "fig_p5_hexagon_symmetry.png")
```

---

## 4. Cropping & Asset Metadata Integration

When figures are generated or harvested:
1. Every file must be auto-cropped with `auto_crop_image(path)`.
2. Record its width, height, and aspect ratio ($H / W$).
3. In `worksheet_spec.json`, configure the problem's `image` object:
   - For square/portrait figures ($0.6 \le AR \le 1.4$): `category = "detailed_diagram"`, `min_width_in = 1.6`, `preferred_width_in = 2.4`, `layout_hint = "side_by_side"`.
   - For wide figures ($AR < 0.6$): `category = "wide_grid"`, `min_width_in = 2.8`, `preferred_width_in = 3.4`, `layout_hint = "stacked"`.

