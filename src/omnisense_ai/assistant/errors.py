"""Phase 8 typed failures."""
from ..errors import ResourceLimitError, SecurityError, ValidationError
class AssistantError(Exception): pass
class AssistantInputError(AssistantError,ValidationError): pass
class AssistantSecurityError(AssistantError,SecurityError): pass
class AssistantOutputLimitError(AssistantError,ResourceLimitError): pass
