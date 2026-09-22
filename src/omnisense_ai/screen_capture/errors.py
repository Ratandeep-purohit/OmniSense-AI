"""Screen capture error types."""

class CaptureError(RuntimeError):
    """Base class for controlled screen capture failures."""
class CapturePermissionError(CaptureError): pass
class CaptureNotActiveError(CaptureError): pass
class MonitorNotFoundError(CaptureError): pass
class InvalidCaptureRegionError(CaptureError): pass
class CaptureBackendError(CaptureError): pass
class CaptureRateLimitError(CaptureError): pass
