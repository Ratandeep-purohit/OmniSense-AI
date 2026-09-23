"""Controlled Phase 04 window detection service."""
from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone

from .backend import WindowDetectionBackend
from .errors import WindowDetectionBackendError, WindowDetectionUnavailableError
from .models import WindowDetectionResult


class WindowDetectionService:
    """Thread-safe, read-only facade over the window detection backend."""

    def __init__(
        self,
        backend: WindowDetectionBackend | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._logger = logger or logging.getLogger("omnisense_ai")
        self._lock = threading.RLock()
        if backend is None:
            from .backend import WindowsWindowDetectionBackend
            backend = WindowsWindowDetectionBackend()
        self._backend = backend
        self._closed = False

    @property
    def backend_name(self) -> str:
        return self._backend.name

    def detect_active_window(self) -> WindowDetectionResult:
        with self._lock:
            if self._closed:
                raise WindowDetectionBackendError("Window detection service is closed.")
            try:
                window = self._backend.detect_active_window()
            except WindowDetectionUnavailableError:
                raise
            except WindowDetectionBackendError:
                raise
            except PermissionError as exc:
                raise WindowDetectionBackendError("Windows denied window metadata access.") from exc
            except Exception as exc:
                raise WindowDetectionBackendError("Window detection backend failed.") from exc

            result = WindowDetectionResult(
                window=window,
                detected_at=datetime.now(timezone.utc),
                backend=self._backend.name,
            )
            self._logger.debug(
                "Window detection completed: backend=%s hwnd=%s pid=%s",
                self._backend.name,
                window.hwnd if window else None,
                window.process_id if window else None,
            )
            return result

    def enumerate_visible_windows(self):
        """Return a fresh read-only snapshot of visible top-level windows."""
        with self._lock:
            if self._closed:
                raise WindowDetectionBackendError("Window detection service is closed.")
            try:
                return self._backend.enumerate_visible_windows()
            except WindowDetectionUnavailableError:
                raise
            except WindowDetectionBackendError:
                raise
            except PermissionError as exc:
                raise WindowDetectionBackendError("Windows denied window enumeration access.") from exc
            except Exception as exc:
                raise WindowDetectionBackendError("Window enumeration backend failed.") from exc

    def close(self) -> None:
        with self._lock:
            self._closed = True
