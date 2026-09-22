"""Typed failures for Phase 9."""
from ..errors import SecurityError,ValidationError
class ActionPlanningError(Exception): pass
class ActionPlanInputError(ActionPlanningError,ValidationError): pass
class ActionPlanSecurityError(ActionPlanningError,SecurityError): pass
class ActionPlanAmbiguityError(ActionPlanningError,ValidationError): pass
