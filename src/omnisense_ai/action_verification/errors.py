"""Typed failures for Phase 12 verification."""
from ..errors import OmniSenseError, SecurityError, ValidationError
class ActionVerificationError(OmniSenseError): pass
class VerificationInputError(ActionVerificationError, ValidationError): pass
class VerificationSecurityError(ActionVerificationError, SecurityError): pass
class VerificationStaleEvidenceError(ActionVerificationError, ValidationError): pass
class VerificationIdentityError(ActionVerificationError, ValidationError): pass
