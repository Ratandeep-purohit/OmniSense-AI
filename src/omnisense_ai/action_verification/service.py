"""Phase 12 verifies post-action state; it never performs desktop actions."""
from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
from ..action_planning.models import ActionPlan
from ..desktop_automation.models import AutomationResult, ExecutionStatus
from .errors import VerificationIdentityError, VerificationInputError, VerificationStaleEvidenceError
from .models import VerificationCheck, VerificationCheckStatus, VerificationConfig, VerificationEvidence, VerificationResult, VerificationStatus

class ActionVerificationService:
    def __init__(self, config: VerificationConfig | None = None) -> None:
        self.config = config or VerificationConfig()

    def verify(self, plan: ActionPlan, execution: AutomationResult, evidence: VerificationEvidence, *, now: datetime | None = None) -> VerificationResult:
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None: raise VerificationInputError("now must be timezone-aware.")
        if execution.plan_id != plan.plan_id or execution.context_id != plan.context_id:
            raise VerificationIdentityError("Execution result is bound to a different plan or context.")
        if evidence.context_id != plan.context_id:
            raise VerificationIdentityError("Verification evidence is bound to a different context.")
        if self.config.require_post_execution_evidence and evidence.captured_at < execution.finished_at:
            raise VerificationStaleEvidenceError("Evidence was captured before execution finished.")
        age=max(0.0,(current-evidence.captured_at).total_seconds())
        if age > self.config.max_age_seconds:
            raise VerificationStaleEvidenceError("Verification evidence is too old.")
        if len(evidence.visible_text)>self.config.max_evidence_text_length:
            raise VerificationInputError("Verification evidence text exceeds configured limits.")
        checks=[]
        execution_by_step={item.step_id:item for item in execution.steps}
        for step in plan.steps:
            observed=execution_by_step.get(step.step_id)
            if observed is None:
                checks.append(VerificationCheck(step.step_id,step.action_type,VerificationCheckStatus.FAILED,step.expected_outcome,"No execution record exists for this plan step.",evidence.captured_at))
                continue
            if observed.status is not ExecutionStatus.SUCCESS:
                checks.append(VerificationCheck(step.step_id,step.action_type,VerificationCheckStatus.FAILED,step.expected_outcome,f"Step execution status was {observed.status.value}.",evidence.captured_at))
                continue
            checks.append(self._check_expectation(step.step_id,step.action_type,step.expected_outcome,evidence))
        statuses={c.status for c in checks}
        if VerificationCheckStatus.FAILED in statuses: overall=VerificationStatus.NOT_VERIFIED
        elif VerificationCheckStatus.INDETERMINATE in statuses: overall=VerificationStatus.INDETERMINATE
        else: overall=VerificationStatus.VERIFIED
        return VerificationResult(str(uuid4()),plan.plan_id,plan.context_id,overall,tuple(checks),current,evidence.captured_at,evidence.source)

    def _check_expectation(self, step_id, action_type, expectation, evidence):
        raw=expectation.strip()
        prefix,sep,value=raw.partition(":")
        normalized=evidence.visible_text.casefold()
        if sep and prefix=="text_contains" and value.strip():
            ok=value.strip().casefold() in normalized
            return VerificationCheck(step_id,action_type,VerificationCheckStatus.PASSED if ok else VerificationCheckStatus.FAILED,raw,"Expected text was found." if ok else "Expected text was not found.",evidence.captured_at)
        if sep and prefix=="text_not_contains" and value.strip():
            ok=value.strip().casefold() not in normalized
            return VerificationCheck(step_id,action_type,VerificationCheckStatus.PASSED if ok else VerificationCheckStatus.FAILED,raw,"Unexpected text was absent." if ok else "Unexpected text was present.",evidence.captured_at)
        if sep and prefix=="window_title_contains" and value.strip():
            ok=value.strip().casefold() in (evidence.window_title or "").casefold()
            return VerificationCheck(step_id,action_type,VerificationCheckStatus.PASSED if ok else VerificationCheckStatus.FAILED,raw,"Window title matched." if ok else "Window title did not match.",evidence.captured_at)
        if sep and prefix in ("app_is", "app_is_any") and value.strip():
            expected_apps = (
                tuple(item.strip().casefold() for item in value.split("|") if item.strip())
                if prefix == "app_is_any"
                else (value.strip().casefold(),)
            )
            observed_app = (evidence.app_name or "").casefold()
            ok = observed_app in expected_apps
            return VerificationCheck(
                step_id,
                action_type,
                VerificationCheckStatus.PASSED if ok else VerificationCheckStatus.FAILED,
                raw,
                "Application matched." if ok else "Application did not match.",
                evidence.captured_at,
            )
        if sep and prefix=="window_id_is" and value.strip():
            ok=value.strip()==str(evidence.window_id)
            return VerificationCheck(step_id,action_type,VerificationCheckStatus.PASSED if ok else VerificationCheckStatus.FAILED,raw,"Window ID matched." if ok else "Window ID did not match.",evidence.captured_at)
        if sep and prefix=="fact" and "=" in value:
            key,expected=value.split("=",1)
            facts=dict(evidence.facts)
            ok=facts.get(key)==expected
            return VerificationCheck(step_id,action_type,VerificationCheckStatus.PASSED if ok else VerificationCheckStatus.FAILED,raw,"Fact matched." if ok else "Fact did not match.",evidence.captured_at)
        return VerificationCheck(step_id,action_type,VerificationCheckStatus.INDETERMINATE,raw,"Expected outcome is not expressed in the Phase 12 verification DSL; semantic verification requires a structured expectation.",evidence.captured_at)
