"""Phase 10 authorization gate. It never executes desktop actions."""
from ..action_planning.models import ActionPlan, ActionRisk, PlanStatus
from ..context_engine.models import ContextSnapshot
from .errors import SafetyInputError, SafetyStaleContextError, SafetyTargetError
from .models import PermissionDecision, PermissionDecisionResult, PolicyReason, SafetyConfig


class SafetyPermissionEngine:
    """Evaluate an ActionPlan before any future desktop automation."""

    def __init__(self, config: SafetyConfig | None = None) -> None:
        self.config = config or SafetyConfig()

    def evaluate(
        self,
        plan: ActionPlan,
        snapshot: ContextSnapshot,
    ) -> PermissionDecisionResult:
        if plan.context_id != snapshot.context.context_id:
            raise SafetyInputError("Action plan context does not match the supplied snapshot.")
        if plan.status != PlanStatus.READY:
            return PermissionDecisionResult(
                PermissionDecision.REQUIRE_CLARIFICATION,
                PolicyReason.AMBIGUOUS,
                plan.plan_id,
                plan.context_id,
                ActionRisk.MEDIUM,
                False,
                message="Only READY plans can reach authorization.",
            )
        if len(plan.steps) == 0 or len(plan.steps) > self.config.max_steps:
            raise SafetyInputError("Action plan step count is outside the safety boundary.")
        if not snapshot.is_fresh(max_age_seconds=self.config.max_context_age_seconds):
            raise SafetyStaleContextError("Context is stale; a fresh observation is required.")

        allowed_steps = []
        denied_steps = []
        highest = ActionRisk.LOW
        rank = {ActionRisk.LOW: 0, ActionRisk.MEDIUM: 1, ActionRisk.HIGH: 2, ActionRisk.CRITICAL: 3}
        for step in plan.steps:
            if self.config.allowed_action_types is not None and step.action_type.value not in self.config.allowed_action_types:
                denied_steps.append(step.step_id)
                continue
            if step.target is None:
                denied_steps.append(step.step_id)
                continue
            if step.risk.value not in {r.value for r in ActionRisk}:
                denied_steps.append(step.step_id)
                continue
            if rank[step.risk] > rank[highest]:
                highest = step.risk
            allowed_steps.append(step.step_id)

        if denied_steps:
            return PermissionDecisionResult(
                PermissionDecision.DENY,
                PolicyReason.POLICY_DENIED,
                plan.plan_id,
                plan.context_id,
                highest,
                plan.requires_confirmation,
                tuple(allowed_steps),
                tuple(denied_steps),
                "One or more plan steps failed the safety policy.",
            )

        needs_confirmation = plan.requires_confirmation
        if highest == ActionRisk.CRITICAL:
            return PermissionDecisionResult(
                PermissionDecision.DENY, PolicyReason.CRITICAL_RISK,
                plan.plan_id, plan.context_id, highest, True,
                tuple(allowed_steps), (), "Critical-risk actions are denied by the baseline policy."
            )
        if highest == ActionRisk.HIGH and not self.config.allow_high_risk_without_confirmation:
            return PermissionDecisionResult(
                PermissionDecision.REQUIRE_CONFIRMATION, PolicyReason.HIGH_RISK,
                plan.plan_id, plan.context_id, highest, True, tuple(allowed_steps), (),
                "High-risk actions require explicit user confirmation."
            )
        if highest == ActionRisk.MEDIUM and not self.config.allow_medium_risk_without_confirmation:
            return PermissionDecisionResult(
                PermissionDecision.REQUIRE_CONFIRMATION, PolicyReason.CONFIRMATION_REQUIRED,
                plan.plan_id, plan.context_id, highest, True, tuple(allowed_steps), (),
                "Medium-risk actions require explicit user confirmation."
            )
        if highest == ActionRisk.LOW and not self.config.allow_low_risk_without_confirmation:
            needs_confirmation = True

        if needs_confirmation:
            return PermissionDecisionResult(
                PermissionDecision.REQUIRE_CONFIRMATION, PolicyReason.CONFIRMATION_REQUIRED,
                plan.plan_id, plan.context_id, highest, True, tuple(allowed_steps), (),
                "Explicit user confirmation is required before execution."
            )

        return PermissionDecisionResult(
            PermissionDecision.ALLOW, PolicyReason.APPROVED,
            plan.plan_id, plan.context_id, highest, False, tuple(allowed_steps), (),
            "Plan passed the baseline safety policy; execution remains prohibited here."
        )
