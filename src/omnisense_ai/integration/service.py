"""Phase 17 controlled orchestration across the existing OmniSense boundaries."""

from __future__ import annotations

from datetime import datetime, timezone

from ..action_planning.service import ActionPlanner
from ..action_verification.models import VerificationEvidence
from ..action_verification.service import ActionVerificationService
from ..context_engine.models import ContextSnapshot
from ..desktop_automation.backend import NullDesktopAutomationBackend
from ..desktop_automation.models import AutomationConfig, AutomationRequest
from ..desktop_automation.service import DesktopAutomationService
from ..safety_permission.service import SafetyPermissionEngine
from ..security.service import SecurityService
from .errors import IntegrationInputError
from .models import PipelineResult, PipelineStatus, PipelineTrace


class OmniSensePipeline:
    """Connect existing phase boundaries without creating a new authority layer."""

    def __init__(
        self,
        *,
        planner: ActionPlanner | None = None,
        security: SecurityService | None = None,
        safety: SafetyPermissionEngine | None = None,
        automation: DesktopAutomationService | None = None,
        verification: ActionVerificationService | None = None,
    ) -> None:
        self.security = security or SecurityService()
        self.planner = planner or ActionPlanner()
        self.safety = safety or SafetyPermissionEngine()
        self.automation = automation or DesktopAutomationService(
            AutomationConfig(enabled=False),
            NullDesktopAutomationBackend(),
        )
        self.verification = verification or ActionVerificationService()

    def run(
        self,
        snapshot: ContextSnapshot,
        intent: str,
        *,
        evidence: VerificationEvidence | None = None,
        now: datetime | None = None,
    ) -> PipelineResult:
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            raise IntegrationInputError("now must be timezone-aware.")
        if not intent or not intent.strip():
            raise IntegrationInputError("Pipeline intent is required.")

        stages = ["context"]
        sanitized_intent = self.security.inspect_text(intent).sanitized_text
        stages.append("security")

        try:
            plan = self.planner.plan(snapshot, sanitized_intent)
        except Exception as exc:
            return self._result(
                PipelineStatus.BLOCKED, snapshot, sanitized_intent, None, None, None, None,
                stages, "action_planning", exc,
            )
        stages.append("action_planning")

        try:
            decision = self.safety.evaluate(plan, snapshot)
        except Exception as exc:
            return self._result(
                PipelineStatus.BLOCKED, snapshot, sanitized_intent, plan, None, None, None,
                stages + ["safety"], "safety", exc,
            )
        stages.append("safety")

        if not decision.allowed:
            return PipelineResult(
                PipelineStatus.BLOCKED, snapshot.context.context_id, sanitized_intent,
                plan, decision, None, None,
                PipelineTrace(tuple(stages), "safety"), decision.message,
            )

        try:
            execution = self.automation.execute(
                plan,
                AutomationRequest(plan.plan_id, plan.context_id, decision),
            )
        except Exception as exc:
            return self._result(
                PipelineStatus.FAILED, snapshot, sanitized_intent, plan, decision, None, None,
                stages + ["desktop_automation"], "desktop_automation", exc,
            )
        stages.append("desktop_automation")

        if evidence is None:
            return PipelineResult(
                PipelineStatus.NOT_VERIFIED, snapshot.context.context_id, sanitized_intent,
                plan, decision, execution, None,
                PipelineTrace(tuple(stages), "verification"),
                "Post-execution evidence is required for verification.",
            )

        try:
            verification = self.verification.verify(plan, execution, evidence, now=current)
        except Exception as exc:
            return self._result(
                PipelineStatus.NOT_VERIFIED, snapshot, sanitized_intent, plan, decision,
                execution, None, stages + ["verification"], "verification", exc,
            )
        stages.append("verification")

        status = (
            PipelineStatus.COMPLETED
            if verification.status.value == "verified"
            else PipelineStatus.NOT_VERIFIED
        )
        return PipelineResult(
            status, snapshot.context.context_id, sanitized_intent,
            plan, decision, execution, verification,
            PipelineTrace(tuple(stages)),
            "Pipeline completed and verification was evaluated.",
        )

    @staticmethod
    def _result(
        status: PipelineStatus,
        snapshot: ContextSnapshot,
        intent: str,
        plan,
        decision,
        execution,
        verification,
        stages: list[str],
        blocked_at: str,
        exc: Exception,
    ) -> PipelineResult:
        return PipelineResult(
            status,
            snapshot.context.context_id,
            intent,
            plan,
            decision,
            execution,
            verification,
            PipelineTrace(tuple(stages), blocked_at),
            f"{type(exc).__name__}: {exc}",
        )
