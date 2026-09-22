"""Phase 5 UI understanding orchestration."""
from __future__ import annotations

import logging
from math import hypot

from ..ocr.models import OCRResult
from ..visual_processing.models import QualityLevel, VisualFrame
from ..window_detection.models import WindowDetectionResult
from .backend import HeuristicUIUnderstandingBackend, UIUnderstandingBackend, confidence_level
from .errors import UIBackendError, UIInputError, UIResourceError, UIValidationError
from .models import (
    UIElement,
    UIElementState,
    UIElementType,
    UIRelationship,
    UIUnderstandingConfig,
    UIUnderstandingResult,
)


class UIUnderstandingService:
    """Build bounded, provenance-aware UI structure from prior-phase evidence."""

    def __init__(
        self,
        config: UIUnderstandingConfig | None = None,
        backend: UIUnderstandingBackend | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.config = config or UIUnderstandingConfig()
        self.backend = backend or HeuristicUIUnderstandingBackend()
        self._logger = logger or logging.getLogger("omnisense_ai")

    def understand(
        self,
        frame: VisualFrame,
        ocr: OCRResult,
        window: WindowDetectionResult,
    ) -> UIUnderstandingResult:
        self._validate_inputs(frame, ocr, window)

        try:
            raw_elements = self.backend.analyze(frame, ocr, window)
        except (UIBackendError, UIInputError, UIResourceError):
            raise
        except Exception as exc:
            raise UIBackendError("UI understanding backend failed.") from exc

        if len(raw_elements) > self.config.max_elements:
            raise UIResourceError("UI element count exceeded configured limit.")

        elements: list[UIElement] = []
        truncated = False
        for index, raw in enumerate(raw_elements):
            if raw.confidence < self.config.min_element_confidence:
                continue
            if len(elements) >= self.config.max_elements:
                truncated = True
                break
            if raw.box.right > frame.width or raw.box.bottom > frame.height:
                raise UIValidationError("UI element lies outside the source frame.")

            element_id = f"ui-{index + 1:05d}"
            elements.append(
                UIElement(
                    element_id=element_id,
                    element_type=raw.element_type,
                    box=raw.box,
                    text=raw.text[: self.config.max_text_length],
                    confidence=raw.confidence,
                    confidence_level=confidence_level(raw.confidence),
                    state=UIElementState.UNKNOWN,
                    source=raw.source,
                    interactable_observation=raw.element_type in {
                        UIElementType.BUTTON,
                        UIElementType.INPUT,
                        UIElementType.CHECKBOX,
                        UIElementType.RADIO,
                        UIElementType.LINK,
                        UIElementType.MENU,
                        UIElementType.TAB,
                    },
                )
            )

        relationships = self._build_relationships(elements)
        if len(relationships) > self.config.max_relationships:
            raise UIResourceError("UI relationship count exceeded configured limit.")

        result = UIUnderstandingResult(
            elements=tuple(elements),
            relationships=tuple(relationships),
            window_id=window.window.hwnd if window.window else None,
            monitor_id=frame.source_monitor_id,
            source_sequence=frame.sequence,
            source_types=("visual_frame", "ocr", "window"),
            truncated=truncated,
        )
        self._logger.debug(
            "UI understanding completed: backend=%s elements=%d relationships=%d sequence=%d",
            self.backend.name,
            len(result.elements),
            len(result.relationships),
            result.source_sequence,
        )
        return result

    @staticmethod
    def _validate_inputs(frame, ocr, window) -> None:
        if not frame.data or frame.pixel_format.value != "RGB24":
            raise UIInputError("Phase 5 requires a valid RGB24 VisualFrame.")
        if frame.quality.level is QualityLevel.REJECT or not frame.quality.usable:
            raise UIInputError("Visual frame quality is insufficient.")
        if ocr.source_sequence != frame.sequence:
            raise UIInputError("OCR result does not belong to the supplied visual frame.")
        if ocr.source_monitor_id != frame.source_monitor_id:
            raise UIInputError("OCR monitor identity does not match the visual frame.")
        if window.window and window.window.monitor_id and window.window.monitor_id != frame.source_monitor_id:
            raise UIInputError("Window monitor identity does not match the visual frame.")

    def _build_relationships(self, elements: list[UIElement]) -> list[UIRelationship]:
        relationships: list[UIRelationship] = []
        for index, source in enumerate(elements):
            for target in elements[index + 1 :]:
                relation, confidence = self._relation(source, target)
                if relation is not None:
                    relationships.append(
                        UIRelationship(source.element_id, target.element_id, relation, confidence)
                    )
        return relationships

    def _relation(self, source: UIElement, target: UIElement) -> tuple[str | None, float]:
        vertical_gap = max(target.box.top - source.box.bottom, source.box.top - target.box.bottom, 0)
        horizontal_gap = max(target.box.left - source.box.right, source.box.left - target.box.right, 0)
        center_distance = hypot(
            (source.box.left + source.box.width / 2) - (target.box.left + target.box.width / 2),
            (source.box.top + source.box.height / 2) - (target.box.top + target.box.height / 2),
        )

        if source.box.iou(target.box) > 0.5:
            return None, 0.0
        if source.element_type is UIElementType.LABEL and target.element_type in {
            UIElementType.INPUT, UIElementType.CHECKBOX, UIElementType.RADIO
        } and vertical_gap <= self.config.association_distance_px:
            return "labels", 0.82
        if source.element_type is UIElementType.BUTTON and target.element_type is UIElementType.LABEL:
            if horizontal_gap <= self.config.association_distance_px:
                return "contains_text", 0.62
        if center_distance <= self.config.association_distance_px and vertical_gap <= self.config.association_distance_px:
            return "near", 0.5
        return None, 0.0
