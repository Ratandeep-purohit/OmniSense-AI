"""Errors for the Phase 10 authorization boundary."""
from ..errors import SecurityError, ValidationError


class SafetyPermissionError(SecurityError):
    """Base Phase 10 security error."""


class SafetyInputError(SafetyPermissionError, ValidationError):
    """The plan or policy input is invalid."""


class SafetyPolicyError(SafetyPermissionError):
    """A policy rule denies the requested operation."""


class SafetyStaleContextError(SafetyPermissionError):
    """The plan was created from context that is no longer fresh."""


class SafetyTargetError(SafetyPermissionError):
    """The plan target cannot be accepted by the safety boundary."""
