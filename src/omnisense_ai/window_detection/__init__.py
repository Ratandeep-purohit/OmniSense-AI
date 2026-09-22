"""Public Phase 04 window and application detection API."""
from .backend import WindowDetectionBackend, WindowsWindowDetectionBackend
from .errors import (
    WindowDetectionBackendError,
    WindowDetectionError,
    WindowDetectionPermissionError,
    WindowDetectionUnavailableError,
    WindowDetectionValidationError,
)
from .models import WindowDetectionResult, WindowInfo, WindowRect, WindowState
from .service import WindowDetectionService

__all__ = [
    "WindowDetectionBackend",
    "WindowsWindowDetectionBackend",
    "WindowDetectionBackendError",
    "WindowDetectionError",
    "WindowDetectionPermissionError",
    "WindowDetectionResult",
    "WindowDetectionService",
    "WindowDetectionUnavailableError",
    "WindowDetectionValidationError",
    "WindowInfo",
    "WindowRect",
    "WindowState",
]
