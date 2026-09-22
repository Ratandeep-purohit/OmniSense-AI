"""Errors for Phase 16 testing and evaluation."""

from ..errors import ResourceLimitError, ValidationError


class EvaluationError(Exception):
    """Base error for evaluation infrastructure."""


class EvaluationInputError(EvaluationError, ValidationError):
    """Raised when an evaluation contract is invalid."""


class EvaluationResourceError(EvaluationError, ResourceLimitError):
    """Raised when an evaluation bound is exceeded."""


class EvaluationDisabledError(EvaluationError):
    """Raised when evaluation is explicitly disabled."""
