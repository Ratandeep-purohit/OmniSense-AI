"""Screen capture backend interfaces and the mss implementation."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Protocol

from .errors import CaptureBackendError
from .models import CaptureRegion, FrameSource, MonitorInfo, ScreenFrame


class ScreenCaptureBackend(Protocol):
    """Backend interface used by the capture service."""

    def enumerate_monitors(self) -> Sequence[MonitorInfo]:
        """Return available monitors."""

    def capture_monitor(self, monitor: MonitorInfo) -> ScreenFrame:
        """Capture the supplied monitor."""

    def capture_region(self, monitor: MonitorInfo, region: CaptureRegion) -> ScreenFrame:
        """Capture a validated region from the supplied monitor."""

    def close(self) -> None:
        """Release backend resources."""


class MssScreenCaptureBackend:
    """Screen capture backend implemented with mss."""

    def __init__(self) -> None:
        try:
            import mss
        except ImportError as exc:
            raise CaptureBackendError("mss is required for real screen capture.") from exc

        self._mss_module = mss
        self._capture = mss.mss()

    def enumerate_monitors(self) -> Sequence[MonitorInfo]:
        monitors = []
        for index, raw_monitor in enumerate(self._capture.monitors[1:], start=1):
            monitors.append(
                MonitorInfo(
                    id=str(index),
                    x=int(raw_monitor["left"]),
                    y=int(raw_monitor["top"]),
                    width=int(raw_monitor["width"]),
                    height=int(raw_monitor["height"]),
                    is_primary=index == 1,
                    name=f"Monitor {index}",
                )
            )
        return monitors

    def capture_monitor(self, monitor: MonitorInfo) -> ScreenFrame:
        return self.capture_region(monitor, monitor.region)

    def capture_region(self, monitor: MonitorInfo, region: CaptureRegion) -> ScreenFrame:
        raw_region = {
            "left": region.x,
            "top": region.y,
            "width": region.width,
            "height": region.height,
        }
        try:
            screenshot = self._capture.grab(raw_region)
        except Exception as exc:
            raise CaptureBackendError("Screen capture backend failed.") from exc

        return ScreenFrame(
            data=bytes(screenshot.raw),
            width=int(screenshot.width),
            height=int(screenshot.height),
            pixel_format="BGRA",
            monitor_id=monitor.id,
            source=FrameSource.REGION if region != monitor.region else FrameSource.MONITOR,
            captured_at=datetime.now(timezone.utc),
            region=region,
        )

    def close(self) -> None:
        close = getattr(self._capture, "close", None)
        if close is not None:
            close()
