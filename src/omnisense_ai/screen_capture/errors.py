"""Screen capture error types."""


class CaptureError(RuntimeError):
    """Base class for controlled screen capture failures."""


class CapturePermissionError(CaptureError):
    """Raised when capture is requested while capture is disabled."""


class CaptureNotActiveError(CaptureError):
    """Raised when capture is requested while the service is stopped or paused."""


class MonitorNotFoundError(CaptureError):
    """Raised when a requested monitor cannot be found."""


class InvalidCaptureRegionError(CaptureError):
    """Raised when a capture region is empty or outside the selected monitor."""


class CaptureBackendError(CaptureError):
    """Raised when the underlying capture backend fails."""
