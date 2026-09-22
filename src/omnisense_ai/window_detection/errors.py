"""Typed Phase 04 window detection errors."""
from __future__ import annotations


class WindowDetectionError(RuntimeError):
    """Base class for controlled window detection failures."""


class WindowDetectionUnavailableError(WindowDetectionError):
    """Raised when the platform backend cannot be used."""


class WindowDetectionPermissionError(WindowDetectionError):
    """Raised when required operating-system metadata is inaccessible."""


class WindowDetectionBackendError(WindowDetectionError):
    """Raised when an operating-system query fails."""


class WindowDetectionValidationError(WindowDetectionError):
    """Raised when backend data violates the Phase 04 contract."""
