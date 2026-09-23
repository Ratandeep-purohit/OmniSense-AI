"""Concrete Windows desktop runtime for the OmniSense product UI."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import time

from .action_verification.models import VerificationEvidence
from .config import CaptureConfig
from .context_engine.models import ContextSnapshot
from .context_engine.service import ContextEngine
from .desktop_automation.backend import NullDesktopAutomationBackend, WindowsDesktopBackend
from .desktop_automation.models import AutomationConfig, AutomationResult
from .desktop_automation.service import DesktopAutomationService
from .integration.models import PipelineResult
from .integration.service import OmniSensePipeline
from .ocr.models import OCRQuality, OCRResult
from .screen_capture.backend import MssScreenCaptureBackend
from .screen_capture.models import MonitorInfo
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
        self.automation_enabled = False
        self.automation = DesktopAutomationService(
            AutomationConfig(enabled=False),
            NullDesktopAutomationBackend(),
        )
        self.pipeline = OmniSensePipeline(automation=self.automation)

    def set_automation_enabled(self, enabled: bool) -> None:
        self.automation.close()
        self.automation_enabled = enabled
        backend = WindowsDesktopBackend() if enabled else NullDesktopAutomationBackend()
        self.automation = DesktopAutomationService(
            AutomationConfig(enabled=enabled),
            backend,
        )
        self.pipeline = OmniSensePipeline(automation=self.automation)

    def snapshot(self) -> ContextSnapshot:
        self.capture.start()

        # MSS monitor IDs are stable within the capture service (for example
        # "1"), while Win32 window detection currently exposes an HMONITOR
        # handle. Those identifiers are different namespaces. Resolve the
        # active window to the capture monitor using virtual-screen geometry
        # before building the context so Phase 6 receives consistent evidence.
        window = self._safe_window()
        monitor = self._monitor_for_window(window)
        captured = self.capture.capture_region(monitor.region, monitor.id)
        visual = self.visual.process(captured)

        # Rebind the observed window to the capture service's monitor ID.
        # The WindowInfo contract is frozen, so replace() creates a validated
        # copy without mutating the Phase 4 observation.
        window = self._align_window_monitor(window, monitor.id)

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

    def _evidence_after_execution(self, plan, execution: AutomationResult) -> VerificationEvidence:
        """Collect fresh post-action Windows evidence.

        Verification is not restricted to the foreground window. Applications
        can launch in the background, hand off from a bootstrapper, or briefly
        change foreground ownership while their real top-level window becomes
        available. We therefore observe the complete visible top-level window
        set and prefer a foreground match when one exists.
        """
        expected = plan.steps[0].expected_outcome if plan.steps else ""
        expected_apps = self._expected_apps(expected)
        expected_title = self._expected_title(expected)
        deadline = time.monotonic() + 5.0
        latest = self._safe_window()
        matched_window = None

        while time.monotonic() < deadline:
            foreground = self._safe_window()
            windows = self._safe_windows()
            candidates = tuple(w for w in windows if self._window_matches(w, expected_apps, expected_title))

            if candidates:
                matched_window = next(
                    (w for w in candidates if w.is_foreground),
                    candidates[0],
                )
                latest = foreground
                break

            latest = foreground
            time.sleep(0.2)

        info = matched_window or latest.window
        verified_target = matched_window is not None
        observed_app = info.process_name if info else None

        if (expected_apps or expected_title) and not verified_target:
            observed_app = None

        return VerificationEvidence(
            context_id=execution.context_id,
            captured_at=datetime.now(timezone.utc),
            visible_text="",
            window_id=info.hwnd if info else None,
            app_name=observed_app,
            window_title=info.title if info else None,
            facts=(
                ("execution.status", execution.status.value),
                ("expected.application", "|".join(sorted(expected_apps))),
                ("verification.window_match", "true" if verified_target else "false"),
                ("verification.foreground", "true" if info and info.is_foreground else "false"),
            ),
            source="windows_window_enumeration",
        )

    def _safe_windows(self):
        try:
            return self.windows.enumerate_visible_windows()
        except Exception:
            return ()

    @staticmethod
    def _window_matches(window, expected_apps: set[str], expected_title: str) -> bool:
        process = (window.process_name or "").casefold()
        title = (window.title or "").casefold()
        process_ok = not expected_apps or process in expected_apps
        title_ok = not expected_title or expected_title in title
        return bool(window.is_visible and process_ok and title_ok)

    @staticmethod
    def _expected_apps(expectation: str) -> set[str]:
        prefix, sep, value = expectation.partition(":")
        if not sep or prefix != "app_is_any":
            return set()
        return {item.strip().casefold() for item in value.split("|") if item.strip()}

    @staticmethod
    def _expected_title(expectation: str) -> str:
        # Calculator may be hosted by ApplicationFrameHost.exe. Its title is
        # therefore an additional bounded signal when that process is used.
        if "calculatorapp.exe" in expectation.casefold() and "applicationframehost.exe" in expectation.casefold():
            return "calculator"
        return ""

    def _safe_window(self) -> WindowDetectionResult:
        try:
            return self.windows.detect_active_window()
        except Exception:
            return WindowDetectionResult.empty("windows")

    def _monitor_for_window(self, window: WindowDetectionResult) -> MonitorInfo:
        monitors = tuple(self.capture.enumerate_monitors())
        if not monitors:
            raise RuntimeError("No display monitors are available.")

        if window.window is None:
            return next((m for m in monitors if m.is_primary), monitors[0])

        rect = window.window.rect

        # Windows chooses a window's monitor using the largest intersection
        # with the window rectangle. Match that behavior rather than relying
        # on the HMONITOR handle string exposed by Phase 4.
        best_monitor = None
        best_area = 0
        for monitor in monitors:
            left = max(rect.left, monitor.x)
            top = max(rect.top, monitor.y)
            right = min(rect.right, monitor.x + monitor.width)
            bottom = min(rect.bottom, monitor.y + monitor.height)
            area = max(0, right - left) * max(0, bottom - top)
            if area > best_area:
                best_area = area
                best_monitor = monitor

        if best_monitor is not None:
            return best_monitor
        return next((m for m in monitors if m.is_primary), monitors[0])

    @staticmethod
    def _align_window_monitor(
        window: WindowDetectionResult, monitor_id: str
    ) -> WindowDetectionResult:
        if window.window is None or window.window.monitor_id == monitor_id:
            return window

        return WindowDetectionResult(
            window=replace(window.window, monitor_id=monitor_id),
            detected_at=window.detected_at,
            backend=window.backend,
        )

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
