"""Typed errors for Phase 14 performance services."""
from __future__ import annotations
from ..errors import OmniSenseError, ResourceLimitError, ValidationError

class PerformanceError(OmniSenseError):
    """Base class for performance subsystem failures."""

class PerformanceInputError(PerformanceError, ValidationError):
    """Invalid performance input."""

class PerformanceResourceError(PerformanceError, ResourceLimitError):
    """Performance resource limit exceeded."""

class PerformanceDisabledError(PerformanceError):
    """Performance collection is disabled."""
