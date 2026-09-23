"""Phase 12 proves post-action state and optional temporal transition."""
from __future__ import annotations
from datetime import datetime,timezone
from uuid import uuid4
from ..action_planning.models import ActionPlan
from ..desktop_automation.models import AutomationResult,ExecutionStatus
from .errors import VerificationIdentityError,VerificationInputError,VerificationStaleEvidenceError
from .models import VerificationCheck,VerificationCheckStatus,VerificationConfig,VerificationEvidence,VerificationResult,VerificationStatus
class ActionVerificationService:
    def __init__(self,config=None): self.config=config or VerificationConfig()
    def verify(self,plan,execution,evidence,*,before_evidence=None,now=None):
        current=now or datetime.now(timezone.utc)
        if current.tzinfo is None: raise VerificationInputError("now must be timezone-aware.")
        if execution.plan_id!=plan.plan_id or execution.context_id!=plan.context_id: raise VerificationIdentityError("Execution result is bound to a different plan or context.")
        if evidence.context_id!=plan.context_id: raise VerificationIdentityError("Verification evidence is bound to a different context.")
        if self.config.require_post_execution_evidence and evidence.captured_at<execution.finished_at: raise VerificationStaleEvidenceError("Evidence was captured before execution finished.")
        age=max(0,(current-evidence.captured_at).total_seconds())
        if age>self.config.max_age_seconds: raise VerificationStaleEvidenceError("Verification evidence is too old.")
        if len(evidence.visible_text)>self.config.max_evidence_text_length: raise VerificationInputError("Verification evidence text exceeds configured limits.")
        checks=[]; by_step={x.step_id:x for x in execution.steps}
        for step in plan.steps:
            observed=by_step.get(step.step_id)
            if observed is None: checks.append(self._check(step,"No execution record exists for this plan step.",VerificationCheckStatus.FAILED,evidence)); continue
            if observed.status is not ExecutionStatus.SUCCESS: checks.append(self._check(step,f"Step execution status was {observed.status.value}.",VerificationCheckStatus.FAILED,evidence)); continue
            checks.append(self._check_expectation(step.step_id,step.action_type,step.expected_outcome,evidence))
        transition=self._transition_proven(before_evidence,evidence,plan) if before_evidence else not self.config.require_temporal_transition
        if self.config.require_temporal_transition and not transition:
            checks.append(VerificationCheck(plan.steps[0].step_id,plan.steps[0].action_type,VerificationCheckStatus.FAILED,"temporal_transition","No meaningful before/after state transition was proven.",evidence.captured_at))
        statuses={c.status for c in checks}
        overall=VerificationStatus.NOT_VERIFIED if VerificationCheckStatus.FAILED in statuses else (VerificationStatus.INDETERMINATE if VerificationCheckStatus.INDETERMINATE in statuses else VerificationStatus.VERIFIED)
        return VerificationResult(str(uuid4()),plan.plan_id,plan.context_id,overall,tuple(checks),current,evidence.captured_at,evidence.source,transition)
    @staticmethod
    def _check(step,message,status,evidence): return VerificationCheck(step.step_id,step.action_type,status,step.expected_outcome,message,evidence.captured_at)
    @staticmethod
    def _transition_proven(before,after,plan):
        if before.context_id!=after.context_id or after.captured_at<=before.captured_at:return False
        if before.application_id!=after.application_id:return True
        if before.window_id!=after.window_id:return True
        if before.window_title!=after.window_title:return True
        before_state=dict(before.facts); after_state=dict(after.facts)
        return before_state!=after_state
    def _check_expectation(self,step_id,action_type,expectation,evidence):
        raw=expectation.strip(); prefix,sep,value=raw.partition(":"); normalized=evidence.visible_text.casefold()
        if sep and prefix=="text_contains" and value.strip():
            ok=value.strip().casefold() in normalized; return VerificationCheck(step_id,action_type,VerificationCheckStatus.PASSED if ok else VerificationCheckStatus.FAILED,raw,"Expected text was found." if ok else "Expected text was not found.",evidence.captured_at)
        if sep and prefix=="text_not_contains" and value.strip():
            ok=value.strip().casefold() not in normalized; return VerificationCheck(step_id,action_type,VerificationCheckStatus.PASSED if ok else VerificationCheckStatus.FAILED,raw,"Unexpected text was absent." if ok else "Unexpected text was present.",evidence.captured_at)
        if sep and prefix=="window_title_contains" and value.strip():
            ok=value.strip().casefold() in (evidence.window_title or "").casefold(); return VerificationCheck(step_id,action_type,VerificationCheckStatus.PASSED if ok else VerificationCheckStatus.FAILED,raw,"Window title matched." if ok else "Window title did not match.",evidence.captured_at)
        if sep and prefix=="application_id" and value.strip():
            ok=(evidence.application_id or "").casefold()==value.strip().casefold(); return VerificationCheck(step_id,action_type,VerificationCheckStatus.PASSED if ok else VerificationCheckStatus.FAILED,raw,"Application identity matched." if ok else "Application identity did not match.",evidence.captured_at)
        if sep and prefix in ("app_is","app_is_any") and value.strip():
            expected=tuple(x.strip().casefold() for x in value.split("|") if x.strip()); ok=(evidence.app_name or "").casefold() in expected
            return VerificationCheck(step_id,action_type,VerificationCheckStatus.PASSED if ok else VerificationCheckStatus.FAILED,raw,"Application matched." if ok else "Application did not match.",evidence.captured_at)
        if sep and prefix=="window_id_is" and value.strip():
            ok=value.strip()==str(evidence.window_id); return VerificationCheck(step_id,action_type,VerificationCheckStatus.PASSED if ok else VerificationCheckStatus.FAILED,raw,"Window ID matched." if ok else "Window ID did not match.",evidence.captured_at)
        if sep and prefix=="fact" and "=" in value:
            key,expected=value.split("=",1); ok=dict(evidence.facts).get(key)==expected
            return VerificationCheck(step_id,action_type,VerificationCheckStatus.PASSED if ok else VerificationCheckStatus.FAILED,raw,"Fact matched." if ok else "Fact did not match.",evidence.captured_at)
        return VerificationCheck(step_id,action_type,VerificationCheckStatus.INDETERMINATE,raw,"Expectation is not expressed in the verification DSL.",evidence.captured_at)
