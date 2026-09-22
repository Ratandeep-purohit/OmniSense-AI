"""Typed errors for Phase 5 UI understanding."""
from ..errors import OmniSenseError


class UIUnderstandingError(OmniSenseError):
    """Base error for Phase 5."""


class UIInputError(UIUnderstandingError):
    """Input contracts are invalid or inconsistent."""


class UIResourceError(UIUnderstandingError):
    """Configured UI-understanding limits were exceeded."""


class UIBackendError(UIUnderstandingError):
    """A UI-understanding backend failed."""


class UIValidationError(UIUnderstandingError):
    """Produced UI structure failed validation."""
