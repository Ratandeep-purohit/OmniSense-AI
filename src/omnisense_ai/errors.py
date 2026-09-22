"""Typed error model for the OmniSense AI foundation.

The error hierarchy is intentionally small and stable. Downstream phases should
catch OmniSenseError (or a documented subclass) instead of depending on
third-party exception types.
"""

from __future__ import annotations

from enum import StrEnum


class ErrorCode(StrEnum):
    CONFIGURATION = "configuration_error"
    LIFECYCLE = "lifecycle_error"
    DEPENDENCY = "dependency_error"
    VALIDATION = "validation_error"
    SECURITY = "security_error"
    RESOURCE = "resource_error"
    INTERNAL = "internal_error"


class OmniSenseError(Exception):
    """Base exception for expected application-level failures."""

    code: ErrorCode = ErrorCode.INTERNAL
    retryable: bool = False

    def __init__(self, message: str, *, details: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.details = dict(details or {})


class ConfigurationError(OmniSenseError, ValueError):
    """Raised when application configuration is invalid."""

    code = ErrorCode.CONFIGURATION


class LifecycleError(OmniSenseError, RuntimeError):
    """Raised when a lifecycle transition is invalid."""

    code = ErrorCode.LIFECYCLE


class DependencyError(OmniSenseError, RuntimeError):
    """Raised when a required dependency cannot be initialized or used."""

    code = ErrorCode.DEPENDENCY
    retryable = True


class ValidationError(OmniSenseError, ValueError):
    """Raised when an input or output violates a contract."""

    code = ErrorCode.VALIDATION


class SecurityError(OmniSenseError, PermissionError):
    """Raised when a security boundary rejects an operation."""

    code = ErrorCode.SECURITY


class ResourceLimitError(OmniSenseError, RuntimeError):
    """Raised when a bounded resource limit is exceeded."""

    code = ErrorCode.RESOURCE
    retryable = True
