"""2D Bin Packing and Whitespace Optimization Engine for Worksheets.

Computes exact geometric footprints for problems with attached diagrams, chooses
side-by-side vs stacked layouts, respects strict vs flexible ordering constraints,
and packs items across pages and columns to minimize wasted whitespace.
"""

from __future__ import annotations
import math
from typing import Any, Dict, List, Optional, Tuple

from .worksheet_ast import (
    LayoutDecision,
    LayoutHint,
    PlacedPage,
    PlacedProblem,
    PlacedSectionHeader,
    Problem,
    RenderPlan,
    SectionOrdering,
    WorkspaceType,
    WorksheetSection,
    WorksheetSpec,
)


class LayoutEngine:
    """Calculates spatial footprints and executes 2D bin packing for worksheets."""

    def __init__(self, worksheet: WorksheetSpec):
        self.ws = worksheet

    def estimate_text_height(
        self,
        problem: Problem,
        target_width_in: float,
        font_size_pt: Optional[float] = None,
    ) -> float:
        """Estimates vertical text height in inches for question prompt and multiple-choice options."""
        fs = font_size_pt or self.ws.default_font_size_pt
        line_height_in = (fs * 1.30) / 72.0  # Approx line pitch
        padding_in = 0.06

        # Average char width in inches for proportional fonts like Calibri/Arial
        char_width_in = (fs * 0.48) / 72.0
        chars_per_line = max(15, int(target_width_in / char_width_in))

        # 1. Main question prompt
        full_text = problem.prompt_text or ""
        if not full_text and problem.prompt_runs:
            full_text = "".join(r.text for r in problem.prompt_runs)

        label_prefix = problem.full_label
        if label_prefix and not full_text.startswith(label_prefix):
            full_text = f"{label_prefix} {full_text}"

        lines = 0
        paragraphs = full_text.split("\n")
        for p in paragraphs:
            p_str = p.strip()
            if not p_str:
                lines += 0.5
            else:
                lines += max(1, math.ceil(len(p_str) / chars_per_line))

        # 2. Multiple choice options
        if problem.choices:
            for ch in problem.choices:
                c_text = ch.text.strip()
                ch_line_chars = max(10, chars_per_line - 5)
                lines += max(1, math.ceil(len(c_text) / ch_line_chars))

        return max(line_height_in, lines * line_height_in + padding_in)

    def estimate_workspace_height(
        self,
        problem: Problem,
        col_width_in: Optional[float] = None,
    ) -> float:
        """Estimates vertical height in inches for the student work area.
        
        Prioritizes explicit approximate workspace heights/areas (approx_workspace_in,
        approx_height_in, approx_area_sq_in) or lines of empty whitespace.
        """
        ws_cfg = problem.workspace
        if ws_cfg.type == WorkspaceType.NONE:
            return 0.0

        cw = col_width_in
        if cw is None:
            cw = self.ws.printable_width_in / max(1, self.ws.default_columns)

        if problem.approx_workspace_in is not None and problem.approx_workspace_in > 0:
            return float(problem.approx_workspace_in)
        if problem.approx_workspace_area_sq_in is not None and problem.approx_workspace_area_sq_in > 0:
            return float(problem.approx_workspace_area_sq_in / max(0.5, cw))

        return ws_cfg.effective_height_in(cw)

    def calculate_problem_footprint(
        self,
        problem: Problem,
        col_width_in: float,
        target_img_width_in: Optional[float] = None,
    ) -> Tuple[LayoutDecision, float, float, float, float, float, float]:
        """Calculates layout decision and exact dimensions for a problem.

        Args:
            problem: The problem to evaluate.
            col_width_in: Target column width in inches.
            target_img_width_in: Explicit image width override (for elastic squeeze or slack expansion).

        Returns:
            Tuple of:
              - decision (LayoutDecision)
              - total_height_in
              - text_render_width_in
              - text_render_height_in
              - image_render_width_in
              - image_render_height_in
              - workspace_height_in
        """
        ws_height = self.estimate_workspace_height(problem, col_width_in)

        # Case 1: No image attached
        if not problem.image:
            text_w = col_width_in
            text_h = self.estimate_text_height(problem, text_w)
            total_h = text_h + ws_height + 0.08
            return (
                LayoutDecision.TEXT_ONLY,
                total_h,
                text_w,
                text_h,
                0.0,
                0.0,
                ws_height,
            )

        # Case 2: Image attached
        img = problem.image
        ar = img.aspect_ratio or 1.0
        prompt_len = len(problem.prompt_text or "")
        min_img_w = problem.effective_min_image_width_in
        pref_img_w = getattr(img, "preferred_width_in", 2.0)
        max_img_w = getattr(img, "max_width_in", 3.5)
        category = getattr(img, "category", "detailed_diagram")

        # Determine Layout Decision based on hints, category, & aspect ratio
        decision = LayoutDecision.STACKED
        if problem.layout_hint == LayoutHint.SIDE_BY_SIDE:
            decision = LayoutDecision.SIDE_BY_SIDE
        elif problem.layout_hint == LayoutHint.STACKED:
            decision = LayoutDecision.STACKED
        else:
            # Auto heuristic:
            # Wide grids and wide aspect ratios must be stacked
            # Formula icons (isolated radical/expression) are best centered stacked
            if category == "wide_grid" or ar < 0.52 or category == "formula_icon":
                decision = LayoutDecision.STACKED
            elif 0.55 <= ar <= 1.55 and prompt_len < 450:
                # Check if side-by-side fits legibility floor comfortably in column
                if min_img_w <= col_width_in * 0.46:
                    decision = LayoutDecision.SIDE_BY_SIDE
                else:
                    decision = LayoutDecision.STACKED
            else:
                decision = LayoutDecision.STACKED

        if decision == LayoutDecision.SIDE_BY_SIDE:
            if target_img_width_in is not None:
                img_w = max(min_img_w, min(target_img_width_in, col_width_in * 0.50))
            else:
                # Ideal width within side-by-side share (35% to 42% of column)
                ideal_w = min(pref_img_w, col_width_in * 0.40)
                img_w = max(min_img_w, min(ideal_w, max_img_w))

            text_w = col_width_in - img_w - 0.08
            img_h = img_w * ar
            text_h = self.estimate_text_height(problem, text_w)
            top_h = max(text_h, img_h)
            total_h = top_h + ws_height + 0.12
            return (
                LayoutDecision.SIDE_BY_SIDE,
                total_h,
                text_w,
                text_h,
                img_w,
                img_h,
                ws_height,
            )
        else:
            # STACKED
            text_w = col_width_in
            text_h = self.estimate_text_height(problem, text_w)

            if target_img_width_in is not None:
                img_w = max(min_img_w, min(target_img_width_in, col_width_in * 0.95))
            else:
                # Bound by pref_img_w and max_img_w (prevents formula icons from ballooning)
                cand_w = min(col_width_in * 0.90, pref_img_w)
                img_w = max(min_img_w, min(cand_w, max_img_w))

            max_stacked_h = 3.4
            img_h = img_w * ar
            if img_h > max_stacked_h:
                img_h = max_stacked_h
                img_w = img_h / ar if ar > 0 else img_w

            total_h = text_h + img_h + ws_height + 0.16
            return (
                LayoutDecision.STACKED,
                total_h,
                text_w,
                text_h,
                img_w,
                img_h,
                ws_height,
            )

    def _attempt_elastic_squeeze(
        self,
        placed_col_items: List[PlacedProblem],
        new_prob: Problem,
        new_fp: Tuple[LayoutDecision, float, float, float, float, float, float],
        overflow_in: float,
        col_width_in: float,
    ) -> Optional[Tuple[List[Tuple[float, float, float, float, float]], Tuple[LayoutDecision, float, float, float, float, float, float]]]:
        """Attempts to elastically compress images in this column to eliminate overflow_in.

        Returns:
            Tuple of (updated_placed_dimensions [(height, img_w, img_h, text_w, text_h)...], new_prob_updated_fp) or None.
        """
        all_candidates = placed_col_items + [PlacedProblem(
            problem=new_prob,
            layout=new_fp[0],
            page_index=0,
            col_index=0,
            x_in=0,
            y_in=0,
            width_in=col_width_in,
            height_in=new_fp[1],
            text_render_width_in=new_fp[2],
            text_render_height_in=new_fp[3],
            image_render_width_in=new_fp[4],
            image_render_height_in=new_fp[5],
            workspace_height_in=new_fp[6],
        )]

        shrink_capacities: List[float] = []
        for cand in all_candidates:
            if not cand.problem.image or cand.image_render_width_in <= 0:
                shrink_capacities.append(0.0)
                continue
            min_w = cand.problem.effective_min_image_width_in
            curr_w = cand.image_render_width_in
            if curr_w <= min_w:
                shrink_capacities.append(0.0)
                continue

            # Footprint at absolute minimum legible width
            _, min_h, _, _, _, _, _ = self.calculate_problem_footprint(
                cand.problem, col_width_in, target_img_width_in=min_w
            )
            elasticity = getattr(cand.problem.image, "elasticity", 1.0)
            cap = max(0.0, (cand.height_in - min_h) * elasticity)
            shrink_capacities.append(cap)

        total_capacity = sum(shrink_capacities)
        if total_capacity < overflow_in:
            return None  # Cannot squeeze enough to absorb the overflow

        squeeze_factor = min(1.0, overflow_in / total_capacity)

        # Apply compression to previously placed items
        updated_placed = []
        for i, cand in enumerate(placed_col_items):
            if shrink_capacities[i] > 0:
                min_w = cand.problem.effective_min_image_width_in
                curr_w = cand.image_render_width_in
                target_w = curr_w - squeeze_factor * (curr_w - min_w)
                fp = self.calculate_problem_footprint(cand.problem, col_width_in, target_img_width_in=target_w)
                updated_placed.append((fp[1], fp[4], fp[5], fp[2], fp[3]))
            else:
                updated_placed.append((cand.height_in, cand.image_render_width_in, cand.image_render_height_in, cand.text_render_width_in, cand.text_render_height_in))

        # Apply compression to the newly placed problem
        last_idx = len(all_candidates) - 1
        if shrink_capacities[last_idx] > 0:
            min_w = new_prob.effective_min_image_width_in
            curr_w = new_fp[4]
            target_w = curr_w - squeeze_factor * (curr_w - min_w)
            new_prob_fp = self.calculate_problem_footprint(new_prob, col_width_in, target_img_width_in=target_w)
        else:
            new_prob_fp = new_fp

        return updated_placed, new_prob_fp

    def _absorb_slack_expansion(
        self,
        page: PlacedPage,
        col_idx: int,
        printable_h: float,
        col_w: float,
    ) -> None:
        """Expands images up to max_width_in when there is excessive trailing whitespace."""
        col_problems = [
            item for item in page.items
            if isinstance(item, PlacedProblem) and item.col_index == col_idx
        ]
        if not col_problems:
            return

        last_prob = col_problems[-1]
        slack = printable_h - (last_prob.y_in + last_prob.height_in)
        if slack < 1.0:
            return

        exp_capacities = []
        for p in col_problems:
            if not p.problem.image or p.image_render_width_in <= 0:
                exp_capacities.append(0.0)
                continue
            max_w = getattr(p.problem.image, "max_width_in", 3.5)
            curr_w = p.image_render_width_in
            if curr_w >= max_w:
                exp_capacities.append(0.0)
                continue
            _, exp_h, _, _, _, _, _ = self.calculate_problem_footprint(
                p.problem, col_w, target_img_width_in=max_w
            )
            cap = max(0.0, exp_h - p.height_in)
            exp_capacities.append(cap)

        total_exp_cap = sum(exp_capacities)
        if total_exp_cap <= 0:
            return

        usable_slack = min(total_exp_cap, slack * 0.60)
        exp_factor = usable_slack / total_exp_cap

        curr_y = col_problems[0].y_in
        for i, p in enumerate(col_problems):
            if exp_capacities[i] > 0:
                max_w = getattr(p.problem.image, "max_width_in", 3.5)
                target_w = p.image_render_width_in + exp_factor * (max_w - p.image_render_width_in)
                fp = self.calculate_problem_footprint(p.problem, col_w, target_img_width_in=target_w)
                p.height_in = fp[1]
                p.text_render_width_in = fp[2]
                p.text_render_height_in = fp[3]
                p.image_render_width_in = fp[4]
                p.image_render_height_in = fp[5]
            p.y_in = curr_y
            curr_y += p.height_in + 0.10

    def pack(self) -> RenderPlan:
        """Executes full 2D layout bin-packing across all worksheet sections."""
        printable_w = self.ws.printable_width_in
        printable_h = self.ws.printable_height_in

        # Page 1 header reserve (title, student info line, etc.)
        p1_header_h = 0.75 if (self.ws.title or self.ws.header_right) else 0.0

        current_page_idx = 1
        pages: List[PlacedPage] = [PlacedPage(page_index=1)]
        default_col_count = max(1, min(2, int(self.ws.default_columns)))
        col_cursors = [p1_header_h] * default_col_count

        # Global statistics
        total_problems = 0
        side_by_side_count = 0
        stacked_count = 0
        text_only_count = 0

        for section in self.ws.sections:
            col_count = int(section.column_mode or self.ws.default_columns)
            col_count = max(1, min(2, col_count))  # Support 1 or 2 columns

            if len(col_cursors) != col_count:
                curr_max = max(col_cursors) if col_cursors else 0.0
                col_cursors = [curr_max] * col_count

            col_gap = self.ws.column_gap_in if col_count > 1 else 0.0
            col_w = (printable_w - (col_count - 1) * col_gap) / col_count

            # Section Header footprint
            sec_header_h = 0.0
            if section.title or section.instructions:
                sec_header_h = 0.35 + (0.20 if section.instructions else 0.0)

            # Problems to pack in this section
            prob_list = list(section.problems)
            if not prob_list:
                continue

            # Calculate footprints
            problem_footprints = []
            for prob in prob_list:
                fp = self.calculate_problem_footprint(prob, col_w)
                problem_footprints.append((prob, fp))

            # Ordering strategy:
            # If FLEXIBLE: sort by height descending (First-Fit Decreasing) for tightest 2D packing
            if section.ordering == SectionOrdering.FLEXIBLE:
                problem_footprints.sort(key=lambda item: item[1][1], reverse=True)

            # Insert section header if present
            if sec_header_h > 0:
                # Align both columns to the lowest available point for a cross-column section header
                curr_max_y = max(col_cursors)
                if curr_max_y + sec_header_h > printable_h - 1.2:
                    # Header doesn't fit with room for problems; start new page
                    current_page_idx += 1
                    pages.append(PlacedPage(page_index=current_page_idx))
                    col_cursors = [0.0] * col_count
                    curr_max_y = 0.0

                header_item = PlacedSectionHeader(
                    section_id=section.id,
                    title=section.title,
                    instructions=section.instructions,
                    page_index=current_page_idx,
                    y_in=curr_max_y,
                    height_in=sec_header_h,
                    span_all_columns=True,
                )
                pages[-1].items.append(header_item)
                for c in range(col_count):
                    col_cursors[c] = curr_max_y + sec_header_h + 0.08

            # Place each problem
            for prob, (decision, total_h, text_w, text_h, img_w, img_h, ws_h) in problem_footprints:
                total_problems += 1
                if decision == LayoutDecision.SIDE_BY_SIDE:
                    side_by_side_count += 1
                elif decision == LayoutDecision.STACKED:
                    stacked_count += 1
                elif decision == LayoutDecision.TEXT_ONLY:
                    text_only_count += 1

                # Select target column:
                # In Strict mode: fill column 0 first, then column 1 (standard reading column order)
                # In Flexible mode: choose column with lowest cursor (balanced packing)
                target_col = 0
                if col_count > 1:
                    if section.ordering == SectionOrdering.FLEXIBLE:
                        # Find column where it fits with minimum cursor
                        valid_cols = [c for c in range(col_count) if col_cursors[c] + total_h <= printable_h]
                        if valid_cols:
                            target_col = min(valid_cols, key=lambda c: col_cursors[c])
                        else:
                            target_col = min(range(col_count), key=lambda c: col_cursors[c])
                    else:
                        # Strict: fill col 0, when full fill col 1
                        if col_cursors[0] + total_h <= printable_h:
                            target_col = 0
                        elif col_cursors[1] + total_h <= printable_h:
                            target_col = 1
                        else:
                            target_col = 0

                # Check if it fits in target column on current page
                if col_cursors[target_col] + total_h > printable_h:
                    # Does it fit in another column on this page?
                    other_col = 1 if target_col == 0 and col_count > 1 else None
                    if other_col is not None and col_cursors[other_col] + total_h <= printable_h:
                        target_col = other_col
                    else:
                        # Attempt Elastic Squeeze before forcing a page break
                        squeezed = False
                        cand_placed = [
                            item for item in pages[-1].items
                            if isinstance(item, PlacedProblem) and item.col_index == target_col
                        ]
                        overflow = (col_cursors[target_col] + total_h) - printable_h
                        if 0 < overflow <= 1.40 and cand_placed:
                            res = self._attempt_elastic_squeeze(
                                cand_placed, prob, (decision, total_h, text_w, text_h, img_w, img_h, ws_h),
                                overflow, col_w
                            )
                            if res:
                                updated_placed, new_prob_fp = res
                                for idx, p_item in enumerate(cand_placed):
                                    p_item.height_in = updated_placed[idx][0]
                                    p_item.image_render_width_in = updated_placed[idx][1]
                                    p_item.image_render_height_in = updated_placed[idx][2]
                                    p_item.text_render_width_in = updated_placed[idx][3]
                                    p_item.text_render_height_in = updated_placed[idx][4]

                                # Re-anchor y positions
                                start_y = cand_placed[0].y_in if cand_placed else 0.0
                                curr_y = start_y
                                for p_item in cand_placed:
                                    p_item.y_in = curr_y
                                    curr_y += p_item.height_in + 0.10
                                col_cursors[target_col] = curr_y

                                decision, total_h, text_w, text_h, img_w, img_h, ws_h = new_prob_fp
                                squeezed = True

                        if not squeezed:
                            # Advance to new page
                            current_page_idx += 1
                            pages.append(PlacedPage(page_index=current_page_idx))
                            col_cursors = [0.0] * col_count
                            target_col = 0

                # Position coordinates
                x_pos = target_col * (col_w + col_gap)
                y_pos = col_cursors[target_col]

                placed = PlacedProblem(
                    problem=prob,
                    layout=decision,
                    page_index=current_page_idx,
                    col_index=target_col,
                    x_in=x_pos,
                    y_in=y_pos,
                    width_in=col_w,
                    height_in=total_h,
                    image_render_width_in=img_w,
                    image_render_height_in=img_h,
                    text_render_width_in=text_w,
                    text_render_height_in=text_h,
                    workspace_height_in=ws_h,
                )
                pages[-1].items.append(placed)

                # Advance column cursor
                col_cursors[target_col] += total_h + 0.10

        # Pass 3: Slack Absorption (Whitespace Filling across pages)
        default_gap = self.ws.column_gap_in if self.ws.default_columns > 1 else 0.0
        default_col_w = (printable_w - (self.ws.default_columns - 1) * default_gap) / max(1, self.ws.default_columns)
        for page in pages:
            for col_idx in range(self.ws.default_columns):
                self._absorb_slack_expansion(page, col_idx, printable_h, default_col_w)

        # Post-processing: Handle fill_remaining workspace
        for page in pages:
            # Find the bottom-most problem in each column
            for col_idx in range(self.ws.default_columns):
                col_problems = [
                    item for item in page.items
                    if isinstance(item, PlacedProblem) and item.col_index == col_idx
                ]
                if col_problems:
                    last_prob = col_problems[-1]
                    if last_prob.problem.workspace.fill_remaining:
                        remain_h = printable_h - (last_prob.y_in + last_prob.height_in)
                        if remain_h > 0.3:
                            last_prob.workspace_height_in += remain_h
                            last_prob.height_in += remain_h

        stats = {
            "total_problems": total_problems,
            "total_pages": len(pages),
            "side_by_side_count": side_by_side_count,
            "stacked_count": stacked_count,
            "text_only_count": text_only_count,
            "density_ratio": (
                float(side_by_side_count) / float(total_problems)
                if total_problems > 0 else 0.0
            ),
        }

        return RenderPlan(
            worksheet=self.ws,
            pages=pages,
            total_pages=len(pages),
            stats=stats,
        )

