"""Errors for Phase 17 full-pipeline integration."""

from ..errors import ValidationError


class IntegrationError(Exception):
    """Base error for the integration boundary."""


class IntegrationInputError(IntegrationError, ValidationError):
    """Raised when pipeline inputs are invalid."""


class IntegrationStageError(IntegrationError):
    """Raised when a pipeline stage fails unexpectedly."""
