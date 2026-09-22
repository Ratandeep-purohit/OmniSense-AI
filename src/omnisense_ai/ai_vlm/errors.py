"""Typed failures for the Phase 7 AI/VLM boundary."""
from __future__ import annotations
from ..errors import DependencyError, ResourceLimitError, SecurityError, ValidationError
class AIVLMError(Exception): pass
class AIProviderError(AIVLMError, DependencyError): pass
class AIValidationError(AIVLMError, ValidationError): pass
class AITimeoutError(AIVLMError, ResourceLimitError): pass
class AISecurityError(AIVLMError, SecurityError): pass
class AIOutputLimitError(AIVLMError, ResourceLimitError): pass
