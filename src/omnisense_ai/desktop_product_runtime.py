"""Concrete Windows desktop runtime for the OmniSense product UI."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import time

from .action_verification.models import VerificationEvidence, VerificationConfig
from .action_verification.service import ActionVerificationService
from .capabilities import Capability, CapabilityManager
from .application_discovery import ApplicationCandidate, WindowsApplicationResolver
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
        self.application_resolver = WindowsApplicationResolver()
        self.automation_enabled = False
        self.capabilities = CapabilityManager(ttl_seconds=3600)
        self.automation = DesktopAutomationService(
            AutomationConfig(enabled=False),
            NullDesktopAutomationBackend(),
        )
        self.pipeline = OmniSensePipeline(automation=self.automation, capabilities=self.capabilities, require_execution_capability=True, verification=ActionVerificationService(VerificationConfig(require_temporal_transition=True)))

    def set_automation_enabled(self, enabled: bool) -> None:
        self.automation.close()
        self.automation_enabled = enabled
        if enabled:
            self.capabilities.grant(Capability.EXECUTE, "desktop-session")
        else:
            self.capabilities.revoke(Capability.EXECUTE)
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
            before_evidence_provider=self._evidence_before_execution,
            evidence_provider=self._evidence_after_execution,
        )

    def close(self) -> None:
        self.capture.close()
        self.windows.close()
        self.automation.close()

    def _evidence_before_execution(self, plan, snapshot: ContextSnapshot) -> VerificationEvidence:
        window = self._safe_window().window
        return VerificationEvidence(
            context_id=snapshot.context.context_id,
            captured_at=datetime.now(timezone.utc),
            window_id=window.hwnd if window else None,
            app_name=window.process_name if window else None,
            window_title=window.title if window else None,
            facts=(("phase", "before"), ("window_present", "true" if window else "false")),
            source="windows_pre_action_snapshot",
            executable_path=window.executable_path if window else None,
        )

    def _evidence_after_execution(self, plan, execution: AutomationResult) -> VerificationEvidence:
        """Collect fresh post-action Windows evidence for the exact app identity."""
        expected = plan.steps[0].expected_outcome if plan.steps else ""
        candidate = self._planned_application_candidate(plan)
        expected_apps = self._expected_apps(expected)
        expected_title = self._expected_title(expected)
        deadline = time.monotonic() + 5.0
        latest = self._safe_window()
        matched_window = None

        while time.monotonic() < deadline:
            foreground = self._safe_window()
            windows = self._safe_windows()
            candidates = tuple(
                w for w in windows
                if self._window_matches(w, candidate, expected_apps, expected_title)
            )
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
        application_id = candidate.application_id if candidate and verified_target else None

        return VerificationEvidence(
            context_id=execution.context_id,
            captured_at=datetime.now(timezone.utc),
            visible_text="",
            window_id=info.hwnd if info else None,
            app_name=observed_app if verified_target else None,
            application_id=application_id,
            window_title=info.title if info else None,
            facts=(
                ("execution.status", execution.status.value),
                ("expected.application", "|".join(sorted(expected_apps))),
                ("verification.window_match", "true" if verified_target else "false"),
                ("verification.foreground", "true" if info and info.is_foreground else "false"),
            ),
            source="windows_window_enumeration",
        )

    def _planned_application_candidate(self, plan) -> ApplicationCandidate | None:
        if not plan.steps:
            return None
        step = plan.steps[0]
        params = dict(step.parameters)
        application_id = params.get("application_id")
        query = params.get("app")
        if not application_id or not query:
            return None
        candidate = self.application_resolver.resolve(query)
        if candidate is None or candidate.application_id.casefold() != application_id.casefold():
            return None
        return candidate

    def _safe_windows(self):
        try:
            return self.windows.enumerate_visible_windows()
        except Exception:
            return ()

    @classmethod
    def _window_matches(
        cls,
        window,
        candidate: ApplicationCandidate | None,
        expected_apps: set[str],
        expected_title: str,
    ) -> bool:
        if not window.is_visible:
            return False

        process = (window.process_name or "").casefold()
        title = (window.title or "").casefold()

        if expected_apps and process not in expected_apps:
            return False
        if expected_title and expected_title not in title:
            return False

        if candidate is None:
            return bool(expected_apps or expected_title)

        if candidate.process_name:
            return process == candidate.process_name.casefold()

        display = cls._normalize_name(candidate.display_name)
        title_normalized = cls._normalize_name(window.title)
        process_normalized = cls._normalize_name(process.rsplit(".", 1)[0])
        if display and display in title_normalized:
            return True

        # A launcher can expose a shortened window title or a helper process.
        # Require meaningful token overlap rather than accepting any substring.
        display_tokens = set(display.split())
        observed_tokens = set((title_normalized + " " + process_normalized).split())
        return len(display_tokens & observed_tokens) >= min(2, len(display_tokens))

    @staticmethod
    def _normalize_name(value: str) -> str:
        import re
        return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()

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
