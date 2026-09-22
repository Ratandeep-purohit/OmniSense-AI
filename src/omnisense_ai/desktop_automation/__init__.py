"""Public Phase 11 desktop automation API."""
from .backend import DesktopAutomationBackend, NullDesktopAutomationBackend, PyAutoGUIDesktopBackend, ResolvedTarget
from .errors import *
from .models import ActionExecution, AutomationConfig, AutomationRequest, AutomationResult, ExecutionStatus
from .service import DesktopAutomationService

__all__ = [
    "DesktopAutomationBackend","NullDesktopAutomationBackend","PyAutoGUIDesktopBackend","ResolvedTarget",
    "ActionExecution","AutomationConfig","AutomationRequest","AutomationResult","ExecutionStatus",
    "DesktopAutomationService",
]
