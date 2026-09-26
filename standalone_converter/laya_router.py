"""Laya Local Triage Layer for Document Structure Classification.

Implements Layer 1 of the Asymmetric Cascade:
- Uses Laya (System-1 local non-autoregressive decision engine)
- Fast local evaluation (~40-80ms per block) on GPU (CUDA) or CPU
- Strips artifacts (headers, footers, page numbers) with 'noul' question
- Classifies typography (Heading 1, Heading 2, List Bullet, Normal) with 'choice'
- Flags complex blocks (tables, diagrams, figures) for escalation to Gemini Flash Lite
- Includes fallback heuristics if Laya weights are unavailable
"""

from __future__ import annotations
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Laya decision schema for document triage
DECISION_SCHEMA: Dict[str, Any] = {
    "is_artifact": {
        "type": "noul",
        "instructions": "Is this a running header, footer, page number, footnote marker, or watermark artifact?",
    },
    "block_type": {
        "type": "choice",
        "instructions": "What structural role does this document text block represent?",
        "criteria": {
            "heading_1": "Top-level major section or chapter header, large title",
            "heading_2": "Subsection or subclause header, topic heading",
            "list_item": "Numbered or bulleted list entry, itemized point",
            "table_or_grid": "Tabular data, matrix, rows and columns, schedule, financial table",
            "figure_or_image": "Diagram, photo, chart, graphic visualization, caption-only reference",
            "paragraph": "Standard continuous narrative body text or multi-sentence paragraph",
        },
    },
}


@dataclass
class TriageResult:
    """Result of evaluating a block through the Laya triage router."""
    is_artifact: bool
    artifact_probability: float
    block_type: str
    confidence: float
    should_escalate: bool
    raw_decision: Optional[Dict[str, Any]] = None


class LayaTriageRouter:
    """Fast local classifier for PDF blocks using Laya."""

    def __init__(
        self,
        device: Optional[str] = None,
        confidence_threshold: float = 0.85,
        artifact_threshold: float = 0.85,
        preload: bool = False,
    ):
        self.confidence_threshold = confidence_threshold
        self.artifact_threshold = artifact_threshold
        self.device = device
        self._router = None
        self._initialized = False

        if preload:
            self._init_router()

    def _init_router(self):
        """Initializes the Laya Router."""
        if self._initialized:
            return

        try:
            import torch
            from laya import Router

            # Auto-detect CUDA if device not specified
            dev = self.device or ("cuda" if torch.cuda.is_available() else "cpu")
            logger.info(f"Initializing Laya Router on device: {dev}")
            self._router = Router(device=dev)
            self._initialized = True
            logger.info("Laya Router ready.")
        except Exception as e:
            logger.warning(
                f"Could not initialize Laya Router ({e}). "
                "Will use rule-based triage heuristic fallback."
            )
            self._router = None
            self._initialized = True

    def predict(self, text: str, bbox: Optional[Any] = None) -> TriageResult:
        """Classify a text block using Laya, with fallback heuristics.

        Args:
            text: The text content of the block.
            bbox: Optional bounding box [ymin, xmin, ymax, xmax] (0-1000 scale)

        Returns:
            TriageResult with classification, confidence, and escalation flag.
        """
        self._init_router()

        clean_text = text.strip()
        if not clean_text:
            return TriageResult(
                is_artifact=True,
                artifact_probability=1.0,
                block_type="paragraph",
                confidence=1.0,
                should_escalate=False,
            )

        # Pre-filter: catch obvious page numbers and running artifact patterns
        is_page_num = bool(re.match(r"^(?:page\s+)?\d+(?:\s*(?:of|/)\s*\d+)?$", clean_text, re.IGNORECASE))
        if is_page_num:
            return TriageResult(
                is_artifact=True,
                artifact_probability=1.0,
                block_type="paragraph",
                confidence=1.0,
                should_escalate=False,
            )

        if self._router is not None:
            try:
                decision = self._router.predict(clean_text, DECISION_SCHEMA)
                return self._parse_laya_decision(decision, clean_text)
            except Exception as e:
                logger.warning(f"Laya predict failed on block ({e}), falling back to heuristic: {clean_text[:40]}...")


        # Fallback heuristic
        return self._heuristic_triage(clean_text, bbox)

    def _parse_laya_decision(self, decision: Dict[str, Any], text: str) -> TriageResult:
        """Extracts typed TriageResult from Laya's raw dictionary response."""
        # Unpack 'answers' container if present
        answers = decision.get("answers", decision)

        # 1. Artifact check (noul question)
        art_info = answers.get("is_artifact", {})
        if isinstance(art_info, dict):
            # noul key represents yes/no probability; answer_confidence is calibrated confidence
            art_prob = float(art_info.get("noul", art_info.get("probability", art_info.get("prob", 0.0))))
            is_artifact = art_prob > self.artifact_threshold
        elif isinstance(art_info, (bool, int, float)):
            art_prob = float(art_info)
            is_artifact = art_prob > self.artifact_threshold
        else:
            is_artifact = False
            art_prob = 0.0

        # 2. Block type check (choice question)
        choice_info = answers.get("block_type", {})
        if isinstance(choice_info, dict):
            selected = choice_info.get("choice", choice_info.get("selected", "paragraph"))
            confidence = float(choice_info.get("answer_confidence", choice_info.get("confidence", 0.5)))
        else:
            selected = str(choice_info)
            confidence = 0.5

        # Normalize selected choice
        selected = selected.lower().replace(" ", "_")
        if selected not in {"heading_1", "heading_2", "list_item", "table_or_grid", "figure_or_image", "paragraph"}:
            selected = "paragraph"

        # 3. Determine escalation:
        # Tables and figures ALWAYS escalate to Gemini Flash Lite
        # Also escalate if confidence is below threshold.
        is_complex = selected in {"table_or_grid", "figure_or_image"}
        low_confidence = confidence < self.confidence_threshold
        should_escalate = is_complex or low_confidence

        return TriageResult(
            is_artifact=is_artifact,
            artifact_probability=art_prob,
            block_type=selected,
            confidence=confidence,
            should_escalate=should_escalate,
            raw_decision=decision,
        )


    def _heuristic_triage(self, text: str, bbox: Optional[Any] = None) -> TriageResult:
        """Fast rule-based triage when Laya model weights are not loaded."""
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        total_len = len(text)

        # Artifact heuristics:
        # Running header/footer patterns (e.g. single number, page X of Y, short URL, copyright)
        is_page_num = bool(re.match(r"^(?:page\s+)?\d+(?:\s*(?:of|/)\s*\d+)?$", text, re.IGNORECASE))
        is_tiny_footer = total_len < 30 and ("copyright" in text.lower() or "all rights reserved" in text.lower())

        if is_page_num or is_tiny_footer:
            return TriageResult(
                is_artifact=True,
                artifact_probability=0.95,
                block_type="paragraph",
                confidence=0.95,
                should_escalate=False,
            )

        # Table detection heuristics:
        # Multiple lines with tab separated or vertical bar characters, or matrix-like alignment
        has_table_delimiters = any("|" in l or "\t" in l for l in lines)
        has_numeric_columns = len(lines) >= 2 and all(len(re.findall(r"\b\d+(?:\.\d+)?\b", l)) >= 2 for l in lines[:3])
        if has_table_delimiters or has_numeric_columns:
            return TriageResult(
                is_artifact=False,
                artifact_probability=0.05,
                block_type="table_or_grid",
                confidence=0.90,
                should_escalate=True,  # Tables always escalate to Gemini
            )

        # List item heuristic:
        # Starts with bullet character or "1.", "a)", etc.
        first_line = lines[0] if lines else ""
        is_bullet = bool(re.match(r"^[\u2022\u25cf\u25cb\u25aa\u25ab\-*]\s+", first_line))
        is_numbered = bool(re.match(r"^\d+[\.\)]\s+", first_line))
        if is_bullet or is_numbered:
            return TriageResult(
                is_artifact=False,
                artifact_probability=0.05,
                block_type="list_item",
                confidence=0.92,
                should_escalate=False,
            )

        # Heading heuristic:
        # Short text (<80 chars), single line, no ending period, title case or all caps
        if len(lines) == 1 and total_len < 100:
            if not text.endswith(".") and (text.isupper() or text.istitle() or len(text) < 45):
                level = "heading_1" if len(text) < 35 or text.isupper() else "heading_2"
                return TriageResult(
                    is_artifact=False,
                    artifact_probability=0.05,
                    block_type=level,
                    confidence=0.88,
                    should_escalate=False,
                )

        # Standard paragraph
        return TriageResult(
            is_artifact=False,
            artifact_probability=0.05,
            block_type="paragraph",
            confidence=0.90,
            should_escalate=False,
        )
