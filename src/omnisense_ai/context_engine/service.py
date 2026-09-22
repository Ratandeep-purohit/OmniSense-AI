"""Phase 6 bounded desktop-context construction."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from ..ocr.models import OCRResult
from ..ui_understanding.models import UIUnderstandingResult
from ..visual_processing.models import VisualFrame
from ..window_detection.models import WindowDetectionResult
from .errors import ContextInputError, ContextResourceError
from .models import (
    ContextAge,
    ContextConfig,
    ContextFact,
    ContextFreshness,
    ContextSnapshot,
    ContextSource,
    DesktopContext,
    Sensitivity,
)


class ContextEngine:
    """Fuse current upstream observations without adding authority."""

    def __init__(self, config: ContextConfig | None = None) -> None:
        self.config = config or ContextConfig()

    def build(
        self,
        frame: VisualFrame,
        ocr: OCRResult,
        window: WindowDetectionResult,
        ui: UIUnderstandingResult,
        *,
        user_context: str | None = None,
        now: datetime | None = None,
    ) -> ContextSnapshot:
        current = now or datetime.now(timezone.utc)
        self._validate_inputs(frame, ocr, window, ui)
        self._validate_user_context(user_context)

        age_seconds = max(0.0, (current - self._timestamp(current)).total_seconds())
        # Phase 2/3/5 do not currently expose capture time, so a newly-built
        # context is treated as fresh at construction time. Future upstream
        # timestamps can replace this without changing the public contract.
        age_seconds = 0.0
        freshness = ContextFreshness.FRESH

        facts = self._facts(frame, ocr, window, ui)
        if len(facts) > self.config.max_facts:
            raise ContextResourceError("Context fact count exceeded configured limit.")

        visible_text = ocr.text[: self.config.max_visible_text_length]
        truncated = len(ocr.text) > self.config.max_visible_text_length

        context = DesktopContext(
            context_id=f"ctx-{uuid4().hex}",
            captured_at=current,
            monitor_id=frame.source_monitor_id,
            frame_sequence=frame.sequence,
            freshness=freshness,
            age=ContextAge(current, age_seconds, freshness),
            facts=tuple(facts),
            visible_text=visible_text,
            window_id=window.window.hwnd if window.window else None,
            app_name=window.window.process_name if window.window else None,
            window_title=window.window.title if window.window else None,
            ui_element_count=len(ui.elements),
            ui_relationship_count=len(ui.relationships),
            sources=("visual_frame", "ocr", "window", "ui_understanding"),
            truncated=truncated or ui.truncated,
        )
        return ContextSnapshot(context=context, user_context=user_context)

    def _validate_inputs(self, frame, ocr, window, ui) -> None:
        if not frame.data or frame.sequence < 1:
            raise ContextInputError("Visual frame is invalid.")
        if ocr.source_sequence != frame.sequence or ocr.source_monitor_id != frame.source_monitor_id:
            raise ContextInputError("OCR evidence does not belong to the supplied frame.")
        if ui.source_sequence != frame.sequence or ui.monitor_id != frame.source_monitor_id:
            raise ContextInputError("UI evidence does not belong to the supplied frame.")
        if window.window and window.window.monitor_id and window.window.monitor_id != frame.source_monitor_id:
            raise ContextInputError("Window evidence does not match the supplied frame monitor.")

    def _validate_user_context(self, user_context: str | None) -> None:
        if user_context is not None and len(user_context) > self.config.max_user_context_length:
            raise ContextResourceError("User context exceeds configured limit.")

    def _facts(self, frame, ocr, window, ui) -> list[ContextFact]:
        facts = [
            ContextFact("desktop.monitor_id", frame.source_monitor_id, ContextSource.OBSERVED, 1.0,
                        provenance=("screen_capture", "visual_processing")),
            ContextFact("desktop.frame_sequence", str(frame.sequence), ContextSource.OBSERVED, 1.0,
                        provenance=("visual_processing",)),
            ContextFact("desktop.visible_text_available", str(bool(ocr.text.strip())).lower(),
                        ContextSource.OBSERVED, 1.0, provenance=("ocr",)),
            ContextFact("desktop.ui_element_count", str(len(ui.elements)), ContextSource.OBSERVED, 1.0,
                        provenance=("ui_understanding",)),
        ]
        if window.window:
            facts.extend([
                ContextFact("window.hwnd", str(window.window.hwnd), ContextSource.OBSERVED, 1.0,
                            provenance=("window_detection",)),
                ContextFact("window.process", window.window.process_name or "unknown", ContextSource.OBSERVED,
                            0.8, provenance=("window_detection",)),
                ContextFact("window.title", window.window.title, ContextSource.OBSERVED, 0.8,
                            sensitivity=Sensitivity.SENSITIVE, provenance=("window_detection",)),
            ])
        return facts

    @staticmethod
    def _timestamp(current: datetime) -> datetime:
        return current
