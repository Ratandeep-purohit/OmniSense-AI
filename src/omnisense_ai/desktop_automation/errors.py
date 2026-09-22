"""Typed failures for Phase 11 desktop automation."""
from ..errors import ResourceLimitError, SecurityError, ValidationError


class DesktopAutomationError(Exception):
    """Base execution error."""


class AutomationDisabledError(DesktopAutomationError, SecurityError):
    """Execution is disabled by configuration."""


class AutomationAuthorizationError(DesktopAutomationError, SecurityError):
    """The Phase 10 decision is not executable."""


class AutomationInputError(DesktopAutomationError, ValidationError):
    """The execution request is malformed."""


class AutomationTargetError(DesktopAutomationError, ValidationError):
    """A target cannot be resolved safely."""


class AutomationBackendError(DesktopAutomationError):
    """The platform adapter failed."""


class AutomationTimeoutError(DesktopAutomationError, ResourceLimitError):
    """An action exceeded its bounded execution time."""


class AutomationCancelledError(DesktopAutomationError):
    """Execution was cancelled before or during an action."""
