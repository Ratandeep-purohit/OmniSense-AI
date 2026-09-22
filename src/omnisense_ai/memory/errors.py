"""Typed errors for Phase 13 memory."""
from __future__ import annotations

from ..errors import ResourceLimitError, SecurityError, ValidationError


class MemoryError(Exception):
    """Base error for memory operations."""


class MemoryDisabledError(MemoryError, SecurityError):
    """Raised when memory is intentionally disabled."""


class MemoryInputError(MemoryError, ValidationError):
    """Raised when memory input violates a contract."""


class MemoryResourceError(MemoryError, ResourceLimitError):
    """Raised when a memory resource limit is exceeded."""


class MemorySecurityError(MemoryError, SecurityError):
    """Raised when a memory security policy rejects an operation."""


class MemoryNotFoundError(MemoryError, KeyError):
    """Raised when a requested memory entry does not exist."""
