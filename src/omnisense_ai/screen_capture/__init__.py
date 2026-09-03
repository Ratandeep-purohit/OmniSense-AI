"""Screen capture abstractions for OmniSense AI Phase 1."""

from .backend import MssScreenCaptureBackend, ScreenCaptureBackend
from .errors import (
    CaptureBackendError,
    CaptureError,
    CaptureNotActiveError,
    CapturePermissionError,
    InvalidCaptureRegionError,
    MonitorNotFoundError,
)
from .models import CaptureRegion, CaptureState, FrameSource, MonitorInfo, ScreenFrame
from .service import ScreenCaptureService

__all__ = [
    "CaptureBackendError",
    "CaptureError",
    "CaptureNotActiveError",
    "CapturePermissionError",
    "CaptureRegion",
    "CaptureState",
    "FrameSource",
    "InvalidCaptureRegionError",
    "MonitorInfo",
    "MonitorNotFoundError",
    "MssScreenCaptureBackend",
    "ScreenCaptureBackend",
    "ScreenCaptureService",
    "ScreenFrame",
]
