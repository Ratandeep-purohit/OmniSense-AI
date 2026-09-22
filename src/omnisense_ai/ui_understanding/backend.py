"""Phase 5 UI understanding backend boundary and deterministic heuristics."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..ocr.models import OCRResult
from ..visual_processing.models import VisualFrame
from ..window_detection.models import WindowDetectionResult
from .models import UIBox, UIConfidenceLevel, UIElementType


@dataclass(frozen=True, slots=True)
class RawUIElement:
    element_type: UIElementType
    box: UIBox
    text: str = ""
    confidence: float = 0.0
    source: tuple[str, ...] = ("heuristic",)


class UIUnderstandingBackend(Protocol):
    name: str

    def analyze(
        self,
        frame: VisualFrame,
        ocr: OCRResult,
        window: WindowDetectionResult,
    ) -> tuple[RawUIElement, ...]:
        ...


class HeuristicUIUnderstandingBackend:
    """Deterministic baseline using OCR geometry and desktop context."""

    name = "heuristic"

    def analyze(
        self,
        frame: VisualFrame,
        ocr: OCRResult,
        window: WindowDetectionResult,
    ) -> tuple[RawUIElement, ...]:
        elements: list[RawUIElement] = []
        for line in ocr.lines:
            text = line.text.strip()
            lowered = text.lower()
            element_type = UIElementType.TEXT
            confidence = 0.55

            if any(marker in lowered for marker in (
                "submit", "save", "cancel", "close", "login", "sign in", "next", "back"
            )):
                element_type = UIElementType.BUTTON
                confidence = 0.72
            elif text.endswith(":"):
                element_type = UIElementType.LABEL
                confidence = 0.68
            elif any(marker in lowered for marker in ("http://", "https://", "www.")):
                element_type = UIElementType.LINK
                confidence = 0.78
            elif len(line.tokens) <= 2 and len(text) <= 40:
                element_type = UIElementType.LABEL
                confidence = 0.58

            width = min(line.box.width, frame.width - line.box.left)
            height = min(line.box.height, frame.height - line.box.top)
            if width <= 0 or height <= 0:
                continue

            elements.append(
                RawUIElement(
                    element_type=element_type,
                    box=UIBox(line.box.left, line.box.top, width, height),
                    text=text,
                    confidence=confidence,
                    source=("ocr", "geometry", "heuristic"),
                )
            )
        return tuple(elements)


def confidence_level(value: float) -> UIConfidenceLevel:
    if value >= 0.8:
        return UIConfidenceLevel.HIGH
    if value >= 0.6:
        return UIConfidenceLevel.MEDIUM
    return UIConfidenceLevel.LOW
