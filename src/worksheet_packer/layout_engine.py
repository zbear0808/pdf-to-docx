"""2D Bin Packing and Whitespace Optimization Engine for Worksheets.

Computes exact geometric footprints for problems with attached diagrams, chooses
side-by-side vs stacked layouts, respects strict vs flexible ordering constraints,
and packs items across pages and columns to minimize wasted whitespace.
"""

from __future__ import annotations
import math
import re
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

        # Clean common markup delimiters from full_text so line counting reflects actual visible text
        cleaned_text = re.sub(r"%.*", "", full_text)
        cleaned_text = re.sub(r"\\begin\{(?:lstlisting|enumerate|itemize)\}(?:\[.*?\])?", "", cleaned_text)
        cleaned_text = re.sub(r"\\end\{(?:lstlisting|enumerate|itemize)\}", "", cleaned_text)
        cleaned_text = re.sub(r"\\item\s*", "", cleaned_text)
        cleaned_text = re.sub(r"\\qnum\{\d+\}", "", cleaned_text)
        cleaned_text = re.sub(r"\\scriptsize", "", cleaned_text)
        cleaned_text = re.sub(r"\\(?:textbf|texttt|textit|color)\{([^}]*)\}", r"\1", cleaned_text)

        lines = 0
        paragraphs = cleaned_text.split("\n")
        for p in paragraphs:
            p_str = p.strip()
            if not p_str:
                lines += 0.3
            else:
                lines += max(1, math.ceil(len(p_str) / chars_per_line))

        # 2. Multiple choice options
        if problem.choices:
            all_short = all(len(ch.text.strip()) <= 15 for ch in problem.choices)
            if all_short and len(problem.choices) <= 4:
                lines += 1.5
            else:
                for ch in problem.choices:
                    c_text = ch.text.strip()
                    c_text = re.sub(r"%.*", "", c_text)
                    c_text = re.sub(r"\\[a-zA-Z]+(?:\{.*?\})?", "", c_text)
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
            curr_y += p.height_in + getattr(p, "spacing_after_in", 0.10)

    def _attempt_squeeze_batch(
        self,
        batch: List[Tuple[Problem, Tuple[LayoutDecision, float, float, float, float, float, float]]],
        avail_h: float,
        col_w: float,
        base_gap: float = 0.10,
    ) -> Optional[List[Tuple[Problem, Tuple[LayoutDecision, float, float, float, float, float, float]]]]:
        """Attempts to elastically compress diagrams in batch so total height + gaps <= avail_h."""
        total_curr_h = sum(fp[1] for _, fp in batch) + max(0, len(batch) - 1) * base_gap
        overflow_in = total_curr_h - avail_h
        if overflow_in <= 0.001:
            return batch
        if overflow_in > 1.80:
            return None

        shrink_capacities: List[float] = []
        min_fps = []
        for prob, fp in batch:
            if not prob.image or fp[4] <= 0:
                shrink_capacities.append(0.0)
                min_fps.append(fp)
                continue
            min_w = prob.effective_min_image_width_in
            curr_w = fp[4]
            if curr_w <= min_w:
                shrink_capacities.append(0.0)
                min_fps.append(fp)
                continue
            min_fp = self.calculate_problem_footprint(prob, col_w, target_img_width_in=min_w)
            min_fps.append(min_fp)
            elasticity = getattr(prob.image, "elasticity", 1.0)
            cap = max(0.0, (fp[1] - min_fp[1]) * elasticity)
            shrink_capacities.append(cap)

        total_cap = sum(shrink_capacities)
        if total_cap < overflow_in:
            return None

        squeeze_factor = min(1.0, overflow_in / total_cap)
        squeezed_batch = []
        for i, (prob, fp) in enumerate(batch):
            if shrink_capacities[i] > 0:
                min_w = prob.effective_min_image_width_in
                curr_w = fp[4]
                target_w = curr_w - squeeze_factor * (curr_w - min_w)
                new_fp = self.calculate_problem_footprint(prob, col_w, target_img_width_in=target_w)
                squeezed_batch.append((prob, new_fp))
            else:
                squeezed_batch.append((prob, fp))

        return squeezed_batch

    def _find_valid_splits_strict(
        self,
        batch: List[Tuple[Problem, Tuple[LayoutDecision, float, float, float, float, float, float]]],
        avail_0: float,
        avail_1: float,
        col_w: float,
        base_gap: float,
        cursor_0: float,
        cursor_1: float,
    ) -> List[Tuple[float, int, List[Tuple[Any, Any]], List[Tuple[Any, Any]]]]:
        """Evaluates all possible split points k in strict sequence for a subset of problems.
        
        Returns:
            List of (score, k, b0_sq, b1_sq) for splits that fit within (avail_0, avail_1).
        """
        m = len(batch)
        if m == 0:
            return []

        valid_splits = []
        for k in range(1, m + 1):
            b0 = batch[:k]
            b1 = batch[k:]

            h0 = sum(fp[1] for _, fp in b0) + max(0, len(b0) - 1) * base_gap
            h1 = sum(fp[1] for _, fp in b1) + max(0, len(b1) - 1) * base_gap if b1 else 0.0

            b0_sq = b0
            b1_sq = b1
            if h0 > avail_0 + 0.01:
                res0 = self._attempt_squeeze_batch(b0, avail_0, col_w, base_gap)
                if res0 is not None:
                    b0_sq = res0
                    h0 = sum(fp[1] for _, fp in b0_sq) + max(0, len(b0_sq) - 1) * base_gap
                else:
                    continue

            if h1 > avail_1 + 0.01:
                res1 = self._attempt_squeeze_batch(b1, avail_1, col_w, base_gap)
                if res1 is not None:
                    b1_sq = res1
                    h1 = sum(fp[1] for _, fp in b1_sq) + max(0, len(b1_sq) - 1) * base_gap
                else:
                    continue

            if h0 <= avail_0 + 0.01 and h1 <= avail_1 + 0.01:
                end0 = cursor_0 + h0
                end1 = cursor_1 + h1
                h_diff = abs(end0 - end1)
                count_diff = abs(len(b0) - len(b1))
                score = h_diff + 1.25 * count_diff
                if m % 2 == 1 and k == (m + 1) // 2:
                    score -= 0.05
                valid_splits.append((score, k, b0_sq, b1_sq))

        valid_splits.sort(key=lambda x: x[0])
        return valid_splits

    def _find_valid_flex(
        self,
        batch: List[Tuple[Problem, Tuple[LayoutDecision, float, float, float, float, float, float]]],
        avail_0: float,
        avail_1: float,
        col_w: float,
        base_gap: float,
        cursor_0: float,
        cursor_1: float,
    ) -> Optional[Tuple[float, List[Tuple[Any, Any]], List[Tuple[Any, Any]]]]:
        """Partitions batch items into two balanced columns in flexible order."""
        sorted_cand = sorted(batch, key=lambda x: x[1][1], reverse=True)
        c0 = []
        c1 = []
        h0 = 0.0
        h1 = 0.0

        for prob, fp in sorted_cand:
            h = fp[1]
            needed_0 = h if not c0 else (h + base_gap)
            needed_1 = h if not c1 else (h + base_gap)

            if cursor_0 + h0 + needed_0 <= avail_0 + 0.01 and (
                cursor_0 + h0 <= cursor_1 + h1 or cursor_1 + h1 + needed_1 > avail_1 + 0.01
            ):
                c0.append((prob, fp))
                h0 += needed_0
            elif cursor_1 + h1 + needed_1 <= avail_1 + 0.01:
                c1.append((prob, fp))
                h1 += needed_1
            elif cursor_0 + h0 + needed_0 <= avail_0 + 0.01:
                c0.append((prob, fp))
                h0 += needed_0
            else:
                return None

        # Rebalance counts if one column has significantly more items and heights allow
        if len(c0) >= len(c1) + 2:
            for i in reversed(range(len(c0))):
                p, fp = c0[i]
                needed_1 = fp[1] if not c1 else (fp[1] + base_gap)
                if cursor_1 + h1 + needed_1 <= avail_1 + 0.01:
                    c1.append(c0.pop(i))
                    h1 += needed_1
                    h0 -= (fp[1] + (base_gap if c0 else 0.0))
                    break
        elif len(c1) >= len(c0) + 2:
            for i in reversed(range(len(c1))):
                p, fp = c1[i]
                needed_0 = fp[1] if not c0 else (fp[1] + base_gap)
                if cursor_0 + h0 + needed_0 <= avail_0 + 0.01:
                    c0.append(c1.pop(i))
                    h0 += needed_0
                    h1 -= (fp[1] + (base_gap if c1 else 0.0))
                    break

        end0 = cursor_0 + h0
        end1 = cursor_1 + h1
        score = abs(end0 - end1) + 1.25 * abs(len(c0) - len(c1))
        return (score, c0, c1)

    def _estimate_pages_needed_strict(
        self,
        remaining_items: List[Tuple[Problem, Tuple[LayoutDecision, float, float, float, float, float, float]]],
        avail_0: float,
        avail_1: float,
        printable_h: float,
        col_w: float,
        base_gap: float,
    ) -> int:
        """Simulates strict forward packing to estimate minimum pages needed for remaining items."""
        pages = 0
        cur = list(remaining_items)
        first_page = True
        while cur:
            pages += 1
            cur_a0 = avail_0 if first_page else printable_h
            cur_a1 = avail_1 if first_page else printable_h
            first_page = False
            m_fit = 0
            for m in range(1, len(cur) + 1):
                s = self._find_valid_splits_strict(cur[:m], cur_a0, cur_a1, col_w, base_gap, 0.0, 0.0)
                if s:
                    m_fit = m
                else:
                    break
            if m_fit == 0:
                m_fit = 1
            cur = cur[m_fit:]
        return max(1, pages)

    def _distribute_column_spacing(
        self,
        batch_items: List[Tuple[Problem, Tuple[LayoutDecision, float, float, float, float, float, float]]],
        col_idx: int,
        avail_h: float,
        cursor_y: float,
        base_gap: float,
        col_w: float,
        col_gap: float,
        page_idx: int,
    ) -> Tuple[float, List[PlacedProblem]]:
        """Positions problems in a column, distributing vertical slack into gaps and workspaces."""
        n = len(batch_items)
        if n == 0:
            return cursor_y, []

        h_total = sum(fp[1] for _, fp in batch_items)
        slack = max(0.0, avail_h - h_total)

        if n > 1:
            base_gaps_total = (n - 1) * base_gap
            extra_slack = max(0.0, slack - base_gaps_total)
            extra_gap = extra_slack / (n - 1)
            gap = min(0.45, base_gap + extra_gap)
            gaps_total = (n - 1) * gap
        else:
            gap = base_gap
            gaps_total = 0.0

        # Space out problems evenly down the column
        x_pos = 0.0 if col_idx == 0 else (col_w + col_gap)
        curr_y = cursor_y
        placed_items = []

        for i, (prob, (decision, total_h, text_w, text_h, img_w, img_h, ws_h)) in enumerate(batch_items):
            placed = PlacedProblem(
                problem=prob,
                layout=decision,
                page_index=page_idx,
                col_index=col_idx,
                x_in=x_pos,
                y_in=curr_y,
                width_in=col_w,
                height_in=total_h,
                image_render_width_in=img_w,
                image_render_height_in=img_h,
                text_render_width_in=text_w,
                text_render_height_in=text_h,
                workspace_height_in=ws_h,
                spacing_after_in=gap,
            )
            placed_items.append(placed)
            curr_y += total_h + gap

        return curr_y, placed_items

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
            if section.column_mode:
                if str(section.column_mode).lower() in ("single", "1"):
                    col_count = 1
                elif str(section.column_mode).lower() in ("double", "2"):
                    col_count = 2
                else:
                    try:
                        col_count = int(section.column_mode)
                    except ValueError:
                        col_count = int(self.ws.default_columns)
            else:
                col_count = int(self.ws.default_columns)
            col_count = max(1, min(2, col_count))  # Support 1 or 2 columns

            if section.page_break_before or (col_count != len(col_cursors) and max(col_cursors) > 0.05):
                if max(col_cursors) > 0.05:
                    current_page_idx = len(pages) + 1
                    pages.append(PlacedPage(page_index=current_page_idx))
                    col_cursors = [0.0] * col_count
            elif len(col_cursors) != col_count:
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
                    current_page_idx = len(pages) + 1
                    pages.append(PlacedPage(page_index=current_page_idx))
                    col_cursors = [0.0] * col_count
                    curr_max_y = 0.0

                header_item = PlacedSectionHeader(
                    section_id=section.id,
                    title=section.title,
                    instructions=section.instructions,
                    page_index=pages[-1].page_index,
                    y_in=curr_max_y,
                    height_in=sec_header_h,
                    span_all_columns=True,
                )
                pages[-1].items.append(header_item)
                for c in range(col_count):
                    col_cursors[c] = curr_max_y + sec_header_h + 0.08

            base_gap = 0.10
            remaining = list(problem_footprints)

            if col_count == 1:
                while remaining:
                    avail_h = printable_h - col_cursors[0]
                    if avail_h < 1.0:
                        current_page_idx = len(pages) + 1
                        pages.append(PlacedPage(page_index=current_page_idx))
                        col_cursors = [0.0]
                        avail_h = printable_h

                    count = 0
                    curr_h = 0.0
                    for prob, fp in remaining:
                        needed = fp[1] if count == 0 else (fp[1] + base_gap)
                        if curr_h + needed <= avail_h + 0.01:
                            curr_h += needed
                            count += 1
                        else:
                            break

                    if count < len(remaining):
                        cand_squeeze = remaining[:count + 1]
                        sq_res = self._attempt_squeeze_batch(cand_squeeze, avail_h, col_w, base_gap)
                        if sq_res is not None:
                            count += 1
                            placed_batch = sq_res
                        else:
                            placed_batch = remaining[:count]
                    else:
                        placed_batch = remaining[:count]

                    if count == 0:
                        if col_cursors[0] > 0.05:
                            current_page_idx = len(pages) + 1
                            pages.append(PlacedPage(page_index=current_page_idx))
                            col_cursors = [0.0]
                            continue
                        else:
                            count = 1
                            placed_batch = remaining[:1]

                    remaining = remaining[count:]
                    col_cursors[0], placed = self._distribute_column_spacing(
                        placed_batch, 0, avail_h, col_cursors[0], base_gap, col_w, col_gap, pages[-1].page_index
                    )
                    pages[-1].items.extend(placed)

                    for p in placed:
                        total_problems += 1
                        if p.layout == LayoutDecision.SIDE_BY_SIDE:
                            side_by_side_count += 1
                        elif p.layout == LayoutDecision.STACKED:
                            stacked_count += 1
                        elif p.layout == LayoutDecision.TEXT_ONLY:
                            text_only_count += 1

                    if remaining:
                        current_page_idx = len(pages) + 1
                        pages.append(PlacedPage(page_index=current_page_idx))
                        col_cursors = [0.0]

            elif col_count == 2:
                while remaining:
                    avail_0 = printable_h - col_cursors[0]
                    avail_1 = printable_h - col_cursors[1]

                    if max(avail_0, avail_1) < 1.0:
                        current_page_idx = len(pages) + 1
                        pages.append(PlacedPage(page_index=current_page_idx))
                        col_cursors = [0.0, 0.0]
                        avail_0 = printable_h
                        avail_1 = printable_h

                    if section.ordering == SectionOrdering.STRICT:
                        valid_m_splits = {}
                        for m_cand in range(1, len(remaining) + 1):
                            splits = self._find_valid_splits_strict(
                                remaining[:m_cand], avail_0, avail_1, col_w, base_gap, col_cursors[0], col_cursors[1]
                            )
                            if splits:
                                valid_m_splits[m_cand] = splits[0]
                            else:
                                break

                        if not valid_m_splits:
                            if col_cursors[0] > 0.05 or col_cursors[1] > 0.05:
                                current_page_idx = len(pages) + 1
                                pages.append(PlacedPage(page_index=current_page_idx))
                                col_cursors = [0.0, 0.0]
                                continue
                            else:
                                col_0_items = [remaining[0]]
                                col_1_items = []
                                remaining = remaining[1:]
                        else:
                            max_m = max(valid_m_splits.keys())
                            if max_m == len(remaining):
                                best_m = max_m
                            else:
                                p_needed = self._estimate_pages_needed_strict(
                                    remaining, avail_0, avail_1, printable_h, col_w, base_gap
                                )
                                target_m = math.ceil(len(remaining) / max(1, p_needed))
                                candidate_ms = [m for m in valid_m_splits.keys() if m <= max_m]
                                best_m = min(candidate_ms, key=lambda m: (abs(m - target_m), valid_m_splits[m][0]))

                            best_split = valid_m_splits[best_m]
                            _, k_star, col_0_items, col_1_items = best_split
                            remaining = remaining[best_m:]

                    else:
                        best_m = 0
                        best_c0, best_c1 = [], []
                        for m_cand in range(1, len(remaining) + 1):
                            res = self._find_valid_flex(
                                remaining[:m_cand], avail_0, avail_1, col_w, base_gap, col_cursors[0], col_cursors[1]
                            )
                            if res is not None:
                                best_m = m_cand
                                _, best_c0, best_c1 = res
                            else:
                                break

                        if best_m == 0:
                            if col_cursors[0] > 0.05 or col_cursors[1] > 0.05:
                                current_page_idx = len(pages) + 1
                                pages.append(PlacedPage(page_index=current_page_idx))
                                col_cursors = [0.0, 0.0]
                                continue
                            else:
                                col_0_items = [remaining[0]]
                                col_1_items = []
                                remaining = remaining[1:]
                        else:
                            col_0_items = best_c0
                            col_1_items = best_c1
                            remaining = remaining[best_m:]

                    col_cursors[0], placed_0 = self._distribute_column_spacing(
                        col_0_items, 0, avail_0, col_cursors[0], base_gap, col_w, col_gap, pages[-1].page_index
                    )
                    pages[-1].items.extend(placed_0)

                    col_cursors[1], placed_1 = self._distribute_column_spacing(
                        col_1_items, 1, avail_1, col_cursors[1], base_gap, col_w, col_gap, pages[-1].page_index
                    )
                    pages[-1].items.extend(placed_1)

                    for p in placed_0 + placed_1:
                        total_problems += 1
                        if p.layout == LayoutDecision.SIDE_BY_SIDE:
                            side_by_side_count += 1
                        elif p.layout == LayoutDecision.STACKED:
                            stacked_count += 1
                        elif p.layout == LayoutDecision.TEXT_ONLY:
                            text_only_count += 1

                    if remaining:
                        current_page_idx = len(pages) + 1
                        pages.append(PlacedPage(page_index=current_page_idx))
                        col_cursors = [0.0, 0.0]

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

