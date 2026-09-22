"""OmniSense AI Phase 0 foundation public API."""

from .app import HealthStatus, bootstrap, health_check
from .config import AppConfig, CaptureConfig, load_config
from .errors import (
    ConfigurationError,
    DependencyError,
    ErrorCode,
    LifecycleError,
    OmniSenseError,
    ResourceLimitError,
    SecurityError,
    ValidationError,
)
from .runtime import ApplicationRuntime, RuntimeSnapshot, RuntimeState
from .telemetry import OperationContext, TelemetryEvent, new_operation

__all__ = [
    "AppConfig",
    "ApplicationRuntime",
    "CaptureConfig",
    "ConfigurationError",
    "DependencyError",
    "ErrorCode",
    "HealthStatus",
    "LifecycleError",
    "OmniSenseError",
    "OperationContext",
    "ResourceLimitError",
    "RuntimeSnapshot",
    "RuntimeState",
    "SecurityError",
    "TelemetryEvent",
    "ValidationError",
    "bootstrap",
    "health_check",
    "load_config",
    "new_operation",
]
