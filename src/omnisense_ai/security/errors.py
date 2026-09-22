"""Typed security errors for Phase 15."""

from __future__ import annotations

from ..errors import SecurityError, ValidationError


class SecurityPolicyError(SecurityError):
    """Raised when a security policy rejects an operation."""


class SecurityInputError(ValidationError):
    """Raised when security inspection receives invalid input."""


class SecurityDisabledError(SecurityError):
    """Raised when the security service is explicitly disabled."""
