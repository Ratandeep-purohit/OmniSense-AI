"""Typed failures for Phase 6 context construction."""

class ContextEngineError(Exception):
    """Base error for bounded desktop-context construction."""


class ContextInputError(ContextEngineError):
    """Upstream evidence is missing, inconsistent, or invalid."""


class ContextResourceError(ContextEngineError):
    """A configured context bound was exceeded."""


class ContextValidationError(ContextEngineError):
    """A context fact failed validation."""


class ContextStaleError(ContextEngineError):
    """Context is too old for an operation that requires freshness."""
