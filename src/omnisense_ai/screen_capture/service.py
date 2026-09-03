"""Controlled screen capture service."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from ..config import CaptureConfig
from .backend import ScreenCaptureBackend
from .errors import (
    CaptureBackendError,
    CaptureNotActiveError,
    CapturePermissionError,
    InvalidCaptureRegionError,
    MonitorNotFoundError,
)
from .models import CaptureRegion, CaptureState, MonitorInfo, ScreenFrame


class ScreenCaptureService:
    """Coordinate screen capture state, validation, and backend access."""

    def __init__(
        self,
        backend: ScreenCaptureBackend,
        config: CaptureConfig,
        logger: logging.Logger | None = None,
    ) -> None:
        self._backend = backend
        self._config = config
        self._logger = logger or logging.getLogger("omnisense_ai")
        self._state = CaptureState.STOPPED

    @property
    def state(self) -> CaptureState:
        """Return the current capture lifecycle state."""

        return self._state

    def enumerate_monitors(self) -> Sequence[MonitorInfo]:
        """Return monitor metadata without capturing screen content."""

        return self._backend.enumerate_monitors()

    def start(self) -> None:
        """Enable capture operations when configuration explicitly allows capture."""

        if not self._config.is_enabled:
            raise CapturePermissionError("Screen capture is disabled by configuration.")
        self._state = CaptureState.RUNNING
        self._logger.info("Screen capture started.")

    def stop(self) -> None:
        """Stop capture operations and release backend resources."""

        self._state = CaptureState.STOPPED
        self._backend.close()
        self._logger.info("Screen capture stopped.")

    def pause(self) -> None:
        """Pause active capture operations."""

        self._ensure_running()
        self._state = CaptureState.PAUSED
        self._logger.info("Screen capture paused.")

    def resume(self) -> None:
        """Resume paused capture operations."""

        if self._state is not CaptureState.PAUSED:
            raise CaptureNotActiveError("Screen capture is not paused.")
        self._state = CaptureState.RUNNING
        self._logger.info("Screen capture resumed.")

    def capture_selected_monitor(self) -> ScreenFrame:
        """Capture the configured monitor."""

        self._ensure_running()
        monitor = self._select_monitor(self._config.monitor_id)
        try:
            return self._backend.capture_monitor(monitor)
        except CaptureBackendError:
            raise
        except Exception as exc:
            raise CaptureBackendError("Screen capture backend failed.") from exc

    def capture_region(self, region: CaptureRegion, monitor_id: str | None = None) -> ScreenFrame:
        """Capture a validated region on the selected or configured monitor."""

        self._ensure_running()
        monitor = self._select_monitor(monitor_id or self._config.monitor_id)
        self._validate_region(monitor, region)
        try:
            return self._backend.capture_region(monitor, region)
        except CaptureBackendError:
            raise
        except Exception as exc:
            raise CaptureBackendError("Screen capture backend failed.") from exc

    def capture_configured_region_or_monitor(self) -> ScreenFrame:
        """Capture the configured region when present, otherwise the configured monitor."""

        if self._config.region is None:
            return self.capture_selected_monitor()
        return self.capture_region(CaptureRegion(*self._config.region))

    def close(self) -> None:
        """Release backend resources without changing public behavior."""

        self._backend.close()

    def _ensure_running(self) -> None:
        if self._state is CaptureState.STOPPED:
            raise CaptureNotActiveError("Screen capture is not started.")
        if self._state is CaptureState.PAUSED:
            raise CaptureNotActiveError("Screen capture is paused.")

    def _select_monitor(self, monitor_id: str) -> MonitorInfo:
        monitors = list(self.enumerate_monitors())
        if monitor_id == "primary":
            for monitor in monitors:
                if monitor.is_primary:
                    return monitor
            if monitors:
                return monitors[0]

        for monitor in monitors:
            if monitor.id == monitor_id:
                return monitor

        raise MonitorNotFoundError(f"Monitor '{monitor_id}' was not found.")

    @staticmethod
    def _validate_region(monitor: MonitorInfo, region: CaptureRegion) -> None:
        if not monitor.contains_region(region):
            raise InvalidCaptureRegionError("Capture region must be inside the selected monitor.")
