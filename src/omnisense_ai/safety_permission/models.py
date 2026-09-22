"""Typed contracts for Phase 10 safety and permission decisions."""
from dataclasses import dataclass
from enum import StrEnum

from ..action_planning.models import ActionPlan, ActionRisk


class PermissionDecision(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_CONFIRMATION = "require_confirmation"
    REQUIRE_CLARIFICATION = "require_clarification"


class PolicyReason(StrEnum):
    APPROVED = "approved"
    PLAN_REJECTED = "plan_rejected"
    STALE_CONTEXT = "stale_context"
    UNSUPPORTED_ACTION = "unsupported_action"
    HIGH_RISK = "high_risk"
    CRITICAL_RISK = "critical_risk"
    CONFIRMATION_REQUIRED = "confirmation_required"
    INVALID_TARGET = "invalid_target"
    POLICY_DENIED = "policy_denied"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True, slots=True)
class SafetyConfig:
    allow_low_risk_without_confirmation: bool = True
    allow_medium_risk_without_confirmation: bool = False
    allow_high_risk_without_confirmation: bool = False
    allow_critical_risk_without_confirmation: bool = False
    max_context_age_seconds: float = 5.0
    max_steps: int = 10
    allowed_action_types: frozenset[str] | None = None

    def __post_init__(self) -> None:
        if self.max_context_age_seconds <= 0 or self.max_context_age_seconds > 3600:
            raise ValueError("max_context_age_seconds is out of bounds.")
        if not 1 <= self.max_steps <= 20:
            raise ValueError("max_steps is out of bounds.")


@dataclass(frozen=True, slots=True)
class PermissionDecisionResult:
    decision: PermissionDecision
    reason: PolicyReason
    plan_id: str
    context_id: str
    risk: ActionRisk
    requires_confirmation: bool
    approved_step_ids: tuple[str, ...] = ()
    denied_step_ids: tuple[str, ...] = ()
    message: str = ""

    @property
    def allowed(self) -> bool:
        return self.decision == PermissionDecision.ALLOW
