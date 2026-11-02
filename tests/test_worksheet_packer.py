"""Comprehensive Unit & Integration Tests for Worksheet Packer.

Verifies:
1. AST schema serialization, validation, and ordering constraints.
2. Image auto-cropping, white border trimming, and aspect ratio calculation.
3. Layout engine: side-by-side vs stacked decision heuristics and 2D bin packing.
4. Strict vs flexible section ordering behavior.
5. Deterministic DOCX rendering with invisible tables and w:cantSplit.
6. Deterministic LaTeX rendering with minipage side-by-side and multicols.
"""

from __future__ import annotations
import json
import os
from pathlib import Path
import tempfile
import unittest
from PIL import Image, ImageDraw

from worksheet_packer.worksheet_ast import (
    LayoutDecision,
    LayoutHint,
    PlacedProblem,
    Problem,
    ProblemImage,
    QuestionChoice,
    RenderPlan,
    SectionOrdering,
    TextRun,
    WorkspaceConfig,
    WorkspaceType,
    WorksheetSection,
    WorksheetSpec,
)
from worksheet_packer.image_utils import auto_crop_image, inspect_diagram_dimensions, estimate_image_scale_bounds
from worksheet_packer.layout_engine import LayoutEngine
from worksheet_packer.docx_renderer import DocxWorksheetRenderer
from worksheet_packer.latex_renderer import LatexWorksheetRenderer
from worksheet_packer.docx_extractor import extract_docx_media, render_docx_pages


class TestWorksheetPacker(unittest.TestCase):

    def setUp(self):
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.temp_dir = Path(self.temp_dir_obj.name)

        # Create a sample diagram image with artificial 60px white borders
        self.sample_diagram = self.temp_dir / "triangle_with_margins.png"
        img = Image.new("RGBA", (400, 300), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        # Content box: (100, 60) to (300, 240) -> 200x180, AR ~ 0.90
        draw.polygon([(100, 240), (300, 240), (100, 60)], fill=(31, 78, 121, 255), outline=(0, 0, 0, 255))
        draw.text((180, 210), "θ", fill=(255, 255, 255, 255))
        img.save(str(self.sample_diagram))

    def tearDown(self):
        self.temp_dir_obj.cleanup()

    def test_auto_crop_image(self):
        """Verifies that auto_crop_image trims white margins and recalculates true dimensions and AR."""
        cropped_path, w_px, h_px, ar = auto_crop_image(
            self.sample_diagram,
            output_path=self.temp_dir / "triangle_clean.png",
            tolerance=15,
            padding_px=4,
        )

        self.assertTrue(cropped_path.exists())
        self.assertTrue(190 <= w_px <= 220)
        self.assertTrue(170 <= h_px <= 200)
        self.assertTrue(0.80 <= ar <= 1.05)

        orig_w, orig_h, orig_ar = inspect_diagram_dimensions(self.sample_diagram)
        self.assertEqual(orig_w, 400)
        self.assertEqual(orig_h, 300)

    def test_ast_schema_and_serialization(self):
        """Verifies WorksheetSpec AST creation, validation, and JSON round-trip."""
        spec = WorksheetSpec(
            title="AP Calculus Worksheet 3.1",
            subtitle="Related Rates & Geometric Optimization",
            default_columns=2,
            sections=[
                WorksheetSection(
                    id="sec_1",
                    title="Part A: Geometric Applications",
                    ordering=SectionOrdering.STRICT,
                    problems=[
                        Problem(
                            id="q1",
                            number=1,
                            prompt_text="A ladder 10 ft long rests against a vertical wall.",
                            workspace=WorkspaceConfig(type=WorkspaceType.LINES, lines=4),
                        ),
                        Problem(
                            id="q2",
                            number=2,
                            part="a",
                            prompt_text="Find the rate at which the angle θ between ladder and ground changes.",
                            choices=[
                                QuestionChoice(label="(A)", text="-0.25 rad/s"),
                                QuestionChoice(label="(B)", text="-0.50 rad/s"),
                                QuestionChoice(label="(C)", text="-1.20 rad/s"),
                            ],
                            workspace=WorkspaceConfig(type=WorkspaceType.NONE),
                        ),
                    ],
                )
            ],
        )

        json_str = spec.model_dump_json(indent=2)
        reloaded = WorksheetSpec.model_validate_json(json_str)

        self.assertEqual(reloaded.title, "AP Calculus Worksheet 3.1")
        self.assertEqual(len(reloaded.sections), 1)
        self.assertEqual(len(reloaded.sections[0].problems), 2)
        self.assertEqual(reloaded.sections[0].problems[1].full_label, "2.(a)")
        self.assertEqual(len(reloaded.sections[0].problems[1].choices), 3)

    def test_layout_engine_decisions(self):
        """Verifies that the packing engine correctly assigns SIDE_BY_SIDE vs STACKED layouts."""
        cropped_path, w, h, ar = auto_crop_image(self.sample_diagram)

        prob_square = Problem(
            id="q_square",
            number=1,
            prompt_text="In the right triangle below, find the angle θ.",
            image=ProblemImage(
                media_path=str(cropped_path),
                native_width_px=w,
                native_height_px=h,
                aspect_ratio=ar,  # ~0.90 -> Square-ish
            ),
            min_rendered_width_in=1.2,
            workspace=WorkspaceConfig(type=WorkspaceType.LINES, lines=3),
        )

        prob_wide = Problem(
            id="q_wide",
            number=2,
            prompt_text="Inspect the wide coordinate plane diagram below.",
            image=ProblemImage(
                media_path=str(cropped_path),
                native_width_px=800,
                native_height_px=200,
                aspect_ratio=0.25,  # Very wide -> Stacked
            ),
            workspace=WorkspaceConfig(type=WorkspaceType.BOX, height_pt=50),
        )

        prob_text_only = Problem(
            id="q_text",
            number=3,
            prompt_text="State the Fundamental Theorem of Calculus.",
            workspace=WorkspaceConfig(type=WorkspaceType.LINES, lines=5),
        )

        ws = WorksheetSpec(
            title="Test Layout Decisions",
            default_columns=1,
            sections=[
                WorksheetSection(
                    id="sec_main",
                    problems=[prob_square, prob_wide, prob_text_only],
                )
            ],
        )

        engine = LayoutEngine(ws)
        col_w = ws.printable_width_in

        dec1, total_h1, text_w1, text_h1, img_w1, img_h1, ws_h1 = engine.calculate_problem_footprint(prob_square, col_w)
        self.assertEqual(dec1, LayoutDecision.SIDE_BY_SIDE)
        self.assertGreater(img_w1, 0)
        self.assertGreater(text_w1, 0)

        dec2, total_h2, text_w2, text_h2, img_w2, img_h2, ws_h2 = engine.calculate_problem_footprint(prob_wide, col_w)
        self.assertEqual(dec2, LayoutDecision.STACKED)

        dec3, total_h3, text_w3, text_h3, img_w3, img_h3, ws_h3 = engine.calculate_problem_footprint(prob_text_only, col_w)
        self.assertEqual(dec3, LayoutDecision.TEXT_ONLY)
        self.assertEqual(img_w3, 0.0)

    def test_flexible_vs_strict_ordering(self):
        """Verifies that flexible ordering sorts problems by footprint height for tighter packing."""
        probs = [
            Problem(id="short_1", number=1, prompt_text="Short Q1", workspace=WorkspaceConfig(lines=1)),
            Problem(id="tall_1", number=2, prompt_text="Tall Q2 with lots of lines", workspace=WorkspaceConfig(lines=10)),
            Problem(id="short_2", number=3, prompt_text="Short Q3", workspace=WorkspaceConfig(lines=1)),
            Problem(id="tall_2", number=4, prompt_text="Tall Q4 with lots of lines", workspace=WorkspaceConfig(lines=12)),
        ]

        ws_strict = WorksheetSpec(
            title="Strict Ordering",
            sections=[WorksheetSection(id="s1", ordering=SectionOrdering.STRICT, problems=list(probs))],
        )
        plan_strict = LayoutEngine(ws_strict).pack()
        strict_order = [item.problem.id for item in plan_strict.pages[0].items if isinstance(item, PlacedProblem)]
        self.assertEqual(strict_order, ["short_1", "tall_1", "short_2", "tall_2"])

        ws_flex = WorksheetSpec(
            title="Flexible Ordering",
            sections=[WorksheetSection(id="s1", ordering=SectionOrdering.FLEXIBLE, problems=list(probs))],
        )
        plan_flex = LayoutEngine(ws_flex).pack()
        flex_order = [item.problem.id for item in plan_flex.pages[0].items if isinstance(item, PlacedProblem)]
        self.assertIn(flex_order[0], ("tall_2", "tall_1"))

    def test_docx_rendering_with_invisible_tables(self):
        """Verifies that DocxWorksheetRenderer compiles into a valid .docx with atomic invisible tables."""
        cropped_path, w, h, ar = auto_crop_image(self.sample_diagram)

        spec = WorksheetSpec(
            title="Geometry & Trig Quiz",
            subtitle="Period 4",
            header_right="Name: ________________ Date: ______",
            default_columns=2,
            sections=[
                WorksheetSection(
                    id="sec_1",
                    title="Section I: Triangle Trigonometry",
                    instructions="Answer all questions. Show complete work.",
                    ordering=SectionOrdering.STRICT,
                    problems=[
                        Problem(
                            id="q1",
                            number=1,
                            prompt_text="Find angle θ in the right triangle shown below.",
                            image=ProblemImage(
                                media_path=str(cropped_path),
                                native_width_px=w,
                                native_height_px=h,
                                aspect_ratio=ar,
                            ),
                            min_rendered_width_in=1.0,
                            workspace=WorkspaceConfig(type=WorkspaceType.LINES, lines=3),
                        ),
                        Problem(
                            id="q2",
                            number=2,
                            prompt_text="Which of the following is equal to sin(60°)?",
                            choices=[
                                QuestionChoice(label="(A)", text="1/2"),
                                QuestionChoice(label="(B)", text="√2 / 2"),
                                QuestionChoice(label="(C)", text="√3 / 2"),
                                QuestionChoice(label="(D)", text="1"),
                            ],
                            workspace=WorkspaceConfig(type=WorkspaceType.NONE),
                        ),
                        Problem(
                            id="q3",
                            number=3,
                            prompt_text="Plot the function f(x) = sin(x) on [-π, π].",
                            workspace=WorkspaceConfig(type=WorkspaceType.GRID, height_pt=80),
                        ),
                    ],
                )
            ],
        )

        plan = LayoutEngine(spec).pack()
        self.assertGreaterEqual(plan.total_pages, 1)

        docx_out = self.temp_dir / "test_worksheet.docx"
        renderer = DocxWorksheetRenderer(plan)
        saved_path = renderer.render(docx_out)

        self.assertTrue(saved_path.exists())
        self.assertGreater(saved_path.stat().st_size, 5000)

        from docx import Document
        doc = Document(str(saved_path))
        self.assertGreaterEqual(len(doc.tables), 4)

        for tbl in doc.tables[1:]:
            for row in tbl.rows:
                trPr = row._tr.get_or_add_trPr()
                cant_split = trPr.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}cantSplit")
                self.assertIsNotNone(cant_split, "Every problem table row must enforce w:cantSplit!")

    def test_latex_rendering_with_minipage(self):
        """Verifies that LatexWorksheetRenderer generates valid LaTeX with minipage and multicols."""
        cropped_path, w, h, ar = auto_crop_image(self.sample_diagram)

        spec = WorksheetSpec(
            title="Geometry & Trig Quiz",
            header_right="Name: \\underline{\\hspace{2in}}",
            default_columns=2,
            sections=[
                WorksheetSection(
                    id="sec_1",
                    title="Part A: Trigonometry",
                    problems=[
                        Problem(
                            id="q1",
                            number=1,
                            prompt_text="Find angle $\\theta$ if $\\sin(\\theta) = \\frac{1}{2}$.",
                            image=ProblemImage(
                                media_path=str(cropped_path),
                                native_width_px=w,
                                native_height_px=h,
                                aspect_ratio=ar,
                            ),
                            min_rendered_width_in=1.0,
                            workspace=WorkspaceConfig(type=WorkspaceType.LINES, lines=2),
                        ),
                        Problem(
                            id="q2",
                            number=2,
                            prompt_text="Which choice represents $\\cos(0)$?",
                            choices=[
                                QuestionChoice(label="(A)", text="0"),
                                QuestionChoice(label="(B)", text="1"),
                            ],
                            workspace=WorkspaceConfig(type=WorkspaceType.NONE),
                        ),
                    ],
                )
            ],
        )

        plan = LayoutEngine(spec).pack()
        tex_out = self.temp_dir / "test_worksheet.tex"
        renderer = LatexWorksheetRenderer(plan)
        saved_tex = renderer.render(tex_out, compile_pdf=False)

        self.assertTrue(saved_tex.exists())
        tex_content = saved_tex.read_text(encoding="utf-8")

        self.assertIn("\\documentclass", tex_content)
        self.assertIn("\\usepackage{multicol}", tex_content)
        self.assertIn("{tcolorbox}", tex_content)
        self.assertIn("\\begin{multicols*}{2}", tex_content)
        self.assertIn("minipage", tex_content)
        self.assertTrue("\\sin(\\theta) = \\frac{1}{2}" in tex_content or "sin(\\theta)" in tex_content)

    def test_docx_media_extraction_and_rendering(self):
        """Verifies extracting embedded images from DOCX and rendering DOCX pages to PNGs."""
        # Compile a sample docx first
        cropped_path, w, h, ar = auto_crop_image(self.sample_diagram)
        spec = WorksheetSpec(
            title="DOCX Extraction Test",
            sections=[
                WorksheetSection(
                    id="s1",
                    problems=[
                        Problem(
                            id="p1",
                            number=1,
                            prompt_text="Inspect triangle.",
                            image=ProblemImage(
                                media_path=str(cropped_path),
                                native_width_px=w,
                                native_height_px=h,
                                aspect_ratio=ar,
                            ),
                        )
                    ],
                )
            ],
        )
        plan = LayoutEngine(spec).pack()
        docx_file = self.temp_dir / "extracted_test.docx"
        DocxWorksheetRenderer(plan).render(docx_file)

        # 1. Test zip-based media extraction
        media_out = self.temp_dir / "media_extracted"
        extracted = extract_docx_media(docx_file, media_out)
        self.assertGreaterEqual(len(extracted), 1)
        for name, p in extracted.items():
            self.assertTrue(p.exists())
            self.assertGreater(p.stat().st_size, 0)

        # 2. Test headless page rendering (if Word COM or LibreOffice available)
        try:
            rendered_dir = self.temp_dir / "pages_rendered"
            pages = render_docx_pages(docx_file, rendered_dir, dpi=150)
            self.assertGreaterEqual(len(pages), 1)
            self.assertTrue(pages[0].exists())
        except RuntimeError as e:
            # If neither Word nor LibreOffice is present in the test environment, skip gracefully
            pass

    def test_dynamic_scale_bounds_estimation(self):
        """Verifies that estimate_image_scale_bounds correctly bounds formula icons and geometry diagrams."""
        # 1. Formula Icon (e.g. sqrt[5]{x^7}) - small native dimensions, source width ~0.44 in
        formula_bounds = estimate_image_scale_bounds(
            image_path=self.sample_diagram,
            native_width_px=119,
            native_height_px=83,
            aspect_ratio=0.70,
            bbox=[500, 100, 530, 152],  # width ratio 52/1000 -> 0.44 in
            page_width_in=8.5,
            col_width_in=3.5,
        )
        self.assertEqual(formula_bounds.category, "formula_icon")
        self.assertLessEqual(formula_bounds.max_width_in, 1.40)
        self.assertGreaterEqual(formula_bounds.min_width_in, 0.35)

        # 2. Detailed Geometric Diagram (fine angle text, source width ~2.2 in)
        geom_bounds = estimate_image_scale_bounds(
            image_path=self.sample_diagram,
            native_width_px=450,
            native_height_px=400,
            aspect_ratio=0.88,
            bbox=[200, 100, 450, 360],  # width ratio 260/1000 -> 2.21 in
            page_width_in=8.5,
            col_width_in=3.5,
        )
        self.assertIn(geom_bounds.category, ("detailed_diagram", "compact_shape"))
        self.assertGreaterEqual(geom_bounds.min_width_in, 1.10)
        self.assertGreaterEqual(geom_bounds.preferred_width_in, 1.50)

    def test_elastic_squeeze_overflow_prevention(self):
        """Verifies that the packing engine elastically compresses diagrams to absorb slight overflows and prevent extra pages."""
        cropped_path, w, h, ar = auto_crop_image(self.sample_diagram)

        # Create two problems in a single-column layout whose preferred heights together
        # slightly overflow printable page height (10.0 in), but can fit if squeezed.
        p1 = Problem(
            id="p1",
            number=1,
            prompt_text="Solve the triangle problem below with all detailed steps.",
            image=ProblemImage(
                media_path=str(cropped_path),
                native_width_px=w,
                native_height_px=h,
                aspect_ratio=1.0,
                preferred_width_in=3.0,
                min_width_in=1.8,
                max_width_in=3.5,
                elasticity=1.0,
            ),
            workspace=WorkspaceConfig(type=WorkspaceType.LINES, lines=3),  # ~0.9 in
        )

        p2 = Problem(
            id="p2",
            number=2,
            prompt_text="Solve the second geometry proof below.",
            image=ProblemImage(
                media_path=str(cropped_path),
                native_width_px=w,
                native_height_px=h,
                aspect_ratio=1.0,
                preferred_width_in=3.0,
                min_width_in=1.8,
                max_width_in=3.5,
                elasticity=1.0,
            ),
            workspace=WorkspaceConfig(type=WorkspaceType.LINES, lines=3),
        )

        ws = WorksheetSpec(
            title="Single Page Elastic Squeeze Test",
            default_columns=1,
            sections=[
                WorksheetSection(
                    id="sec_squeeze",
                    problems=[p1, p2],
                )
            ],
        )

        # Total preferred stacked height for each is ~ text (0.4) + img (3.0) + ws (0.9) + pad (0.16) = ~4.46 in
        # Header on page 1 is 0.75 in.
        # Two problems = 0.75 + 4.46 + 0.10 + 4.46 + 0.10 = 9.87 in (just on edge)
        # Let's adjust workspace lines slightly to induce an overflow of 0.4 in
        p1.workspace.lines = 6  # ~1.8 in -> total footprint ~5.36 in
        p2.workspace.lines = 6  # ~1.8 in -> total footprint ~5.36 in
        # Without squeeze: 0.75 + 5.36 + 0.1 + 5.36 = 11.57 in > 10.0 in printable height!
        # With image squeeze from 3.0 in down towards 1.8 in:
        # Can save up to 2 * (3.0 - 1.8) = 2.4 in!
        # Overflow is ~1.57 in, so squeezing both images to ~2.2 in will allow both to fit on 1 page!

        plan = LayoutEngine(ws).pack()

        # Both problems must be packed onto page 1!
        self.assertEqual(plan.total_pages, 1)
        self.assertEqual(len(plan.pages[0].items), 2)
        # Verify both images were compressed within valid bounds
        item1: PlacedProblem = plan.pages[0].items[0]
        item2: PlacedProblem = plan.pages[0].items[1]
        self.assertLess(item1.image_render_width_in, 3.0)
        self.assertGreaterEqual(item1.image_render_width_in, 1.8)
        self.assertLess(item2.image_render_width_in, 3.0)
        self.assertGreaterEqual(item2.image_render_width_in, 1.8)

    def test_empty_workspace_budgeting_and_no_underlines(self):
        """Verifies approx workspace budgeting and confirms no underline rules are rendered."""
        # 1. Test AST syncing & area scaling
        p1 = Problem(id="q1", number=1, prompt_text="Solve for x.", approx_workspace_in=1.5)
        self.assertEqual(p1.workspace.approx_height_in, 1.5)
        self.assertEqual(p1.workspace.effective_height_in(col_width_in=3.5), 1.5)

        p2 = Problem(id="q2", number=2, prompt_text="Explain reasoning.", approx_workspace_area_sq_in=7.0)
        self.assertEqual(p2.workspace.approx_area_sq_in, 7.0)
        self.assertAlmostEqual(p2.workspace.effective_height_in(col_width_in=3.5), 2.0, places=2)

        p3 = Problem(id="q3", number=3, prompt_text="Legacy lines question.", workspace=WorkspaceConfig(type=WorkspaceType.LINES, lines=3))

        ws = WorksheetSpec(
            title="Clean Workspace Test",
            default_columns=1,
            sections=[
                WorksheetSection(
                    id="sec_clean",
                    problems=[p1, p2, p3],
                )
            ],
        )

        plan = LayoutEngine(ws).pack()
        self.assertGreaterEqual(plan.total_pages, 1)

        # Footprint of p1 must reflect 1.5 in workspace
        placed_p1: PlacedProblem = plan.pages[0].items[0]
        self.assertAlmostEqual(placed_p1.workspace_height_in, 1.5, places=2)

        # 2. DOCX Rendering Verification: must NOT contain underscore lines
        docx_file = self.temp_dir / "clean_workspace.docx"
        DocxWorksheetRenderer(plan).render(docx_file)
        self.assertTrue(docx_file.exists())

        from docx import Document
        doc = Document(str(docx_file))
        # Ensure problem tables (tbl 1 onwards) contain no underscore strings
        self.assertGreater(len(doc.tables), 1)
        for tbl in doc.tables[1:]:
            for row in tbl.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        self.assertNotIn("____", p.text)

        # 3. LaTeX Rendering Verification: must contain \vspace and NO workspace \hrule rules
        tex_file = self.temp_dir / "clean_workspace.tex"
        LatexWorksheetRenderer(plan).render(tex_file, compile_pdf=False)
        self.assertTrue(tex_file.exists())
        tex_str = tex_file.read_text(encoding="utf-8")
        self.assertIn("\\vspace*{1.50in}", tex_str)
        self.assertNotIn("height 0.3pt", tex_str)  # Legacy workspace rules must not be generated


if __name__ == "__main__":
    unittest.main()
