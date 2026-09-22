"""Concrete Windows desktop runtime for the OmniSense product UI."""

from __future__ import annotations

from datetime import datetime, timezone

from .action_verification.models import VerificationEvidence
from .config import CaptureConfig
from .context_engine.models import ContextSnapshot
from .context_engine.service import ContextEngine
from .desktop_automation.backend import WindowsDesktopBackend
from .desktop_automation.models import AutomationConfig, AutomationResult
from .desktop_automation.service import DesktopAutomationService
from .integration.models import PipelineResult
from .integration.service import OmniSensePipeline
from .ocr.models import OCRQuality, OCRResult
from .screen_capture.backend import MssScreenCaptureBackend
from .screen_capture.service import ScreenCaptureService
from .ui_understanding.models import UIUnderstandingResult
from .visual_processing.models import ProcessingConfig
from .visual_processing.processor import VisualProcessor
from .window_detection.models import WindowDetectionResult
from .window_detection.service import WindowDetectionService


class DesktopProductRuntime:
    """Connect real Windows observation and bounded execution to the UI."""

    def __init__(self) -> None:
        self.capture = ScreenCaptureService(
            MssScreenCaptureBackend(),
            CaptureConfig(
                is_enabled=True,
                monitor_id="primary",
                interval_ms=1000,
                max_fps=1,
                region=None,
            ),
        )
        self.visual = VisualProcessor(
            ProcessingConfig(target_width=1280, target_height=720)
        )
        self.windows = WindowDetectionService()
        self.context_engine = ContextEngine()
        self.automation = DesktopAutomationService(
            AutomationConfig(
                enabled=True,
                allowed_apps=frozenset(
                    {"word", "excel", "powerpoint", "notepad", "calculator"}
                ),
            ),
            WindowsDesktopBackend(),
        )
        self.pipeline = OmniSensePipeline(automation=self.automation)

    def snapshot(self) -> ContextSnapshot:
        self.capture.start()
        captured = self.capture.capture_selected_monitor()
        visual = self.visual.process(captured)
        window = self._safe_window()
        ocr = self._optional_ocr(visual)
        ui = UIUnderstandingResult(
            elements=(),
            relationships=(),
            window_id=window.window.hwnd if window.window else None,
            monitor_id=visual.source_monitor_id,
            source_sequence=visual.sequence,
            source_types=("visual_frame", "window_detection"),
        )
        return self.context_engine.build(
            visual,
            ocr,
            window,
            ui,
            now=datetime.now(timezone.utc),
        )

    def run(self, intent: str) -> PipelineResult:
        snapshot = self.snapshot()
        return self.pipeline.run(
            snapshot,
            intent,
            evidence_provider=self._evidence_after_execution,
        )

    def close(self) -> None:
        self.capture.close()
        self.windows.close()
        self.automation.close()

    def _evidence_after_execution(
        self, execution: AutomationResult
    ) -> VerificationEvidence:
        window = self._safe_window()
        info = window.window
        return VerificationEvidence(
            context_id=execution.context_id,
            captured_at=datetime.now(timezone.utc),
            visible_text="",
            window_id=info.hwnd if info else None,
            app_name=info.process_name if info else None,
            window_title=info.title if info else None,
            facts=(("execution.status", execution.status.value),),
            source="windows_window_detection",
        )

    def _safe_window(self) -> WindowDetectionResult:
        try:
            return self.windows.detect_active_window()
        except Exception:
            return WindowDetectionResult.empty("windows")

    @staticmethod
    def _optional_ocr(visual):
        try:
            from .ocr.service import OCRService

            return OCRService().recognize(visual)
        except Exception:
            return OCRResult(
                text="",
                tokens=(),
                lines=(),
                quality=OCRQuality.EMPTY,
                source_monitor_id=visual.source_monitor_id,
                source_sequence=visual.sequence,
                engine="unavailable",
                language="eng",
            )
