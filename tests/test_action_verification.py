from datetime import datetime, timedelta, timezone
from omnisense_ai.action_planning.models import ActionPlan, ActionRisk, ActionStep, ActionTarget, ActionType, PlanStatus
from omnisense_ai.desktop_automation.models import ActionExecution, AutomationResult, ExecutionStatus
from omnisense_ai.action_verification.errors import VerificationIdentityError, VerificationStaleEvidenceError
from omnisense_ai.action_verification.models import VerificationCheckStatus, VerificationConfig, VerificationEvidence, VerificationStatus
from omnisense_ai.action_verification.service import ActionVerificationService

def make_plan(expected="text_contains:Saved"):
    step=ActionStep("step-1",ActionType.CLICK,ActionTarget("t","save"),(),ActionRisk.MEDIUM,expected)
    return ActionPlan("plan-1","ctx-1","click save",PlanStatus.READY,(step,),"",True)

def make_execution(plan, status=ExecutionStatus.SUCCESS, finished=None):
    now=datetime.now(timezone.utc)
    finished=finished or now
    step=ActionExecution("step-1",ActionType.CLICK,status,finished-timedelta(milliseconds=10),finished,"ok")
    return AutomationResult("exec-1",plan.plan_id,plan.context_id,status,(step,),finished-timedelta(milliseconds=20),finished)

def test_verified_when_expected_text_is_present():
    p=make_plan()
    finished=datetime.now(timezone.utc)
    e=make_execution(p,finished=finished)
    evidence=VerificationEvidence("ctx-1",finished+timedelta(milliseconds=10),"Saved successfully",window_title="Editor",source="test")
    r=ActionVerificationService().verify(p,e,evidence,now=finished+timedelta(seconds=1))
    assert r.status is VerificationStatus.VERIFIED
    assert r.checks[0].status is VerificationCheckStatus.PASSED

def test_not_verified_when_expected_text_missing():
    p=make_plan()
    finished=datetime.now(timezone.utc)
    e=make_execution(p,finished=finished)
    evidence=VerificationEvidence("ctx-1",finished+timedelta(milliseconds=10),"Something else",source="test")
    r=ActionVerificationService().verify(p,e,evidence,now=finished+timedelta(seconds=1))
    assert r.status is VerificationStatus.NOT_VERIFIED

def test_indeterminate_for_legacy_free_text_expectation():
    p=make_plan("Requested UI state should change as described.")
    finished=datetime.now(timezone.utc)
    e=make_execution(p,finished=finished)
    evidence=VerificationEvidence("ctx-1",finished+timedelta(milliseconds=10),"anything",source="test")
    r=ActionVerificationService().verify(p,e,evidence,now=finished+timedelta(seconds=1))
    assert r.status is VerificationStatus.INDETERMINATE

def test_stale_evidence_rejected():
    p=make_plan()
    finished=datetime.now(timezone.utc)
    e=make_execution(p,finished=finished)
    evidence=VerificationEvidence("ctx-1",finished+timedelta(milliseconds=10),"Saved",source="test")
    try:
        ActionVerificationService(VerificationConfig(max_age_seconds=1)).verify(p,e,evidence,now=finished+timedelta(seconds=2))
        assert False
    except VerificationStaleEvidenceError:
        pass

def test_evidence_before_execution_rejected():
    p=make_plan()
    finished=datetime.now(timezone.utc)
    e=make_execution(p,finished=finished)
    evidence=VerificationEvidence("ctx-1",finished-timedelta(seconds=1),"Saved",source="test")
    try:
        ActionVerificationService().verify(p,e,evidence)
        assert False
    except VerificationStaleEvidenceError:
        pass

def test_identity_mismatch_rejected():
    p=make_plan()
    e=make_execution(p)
    evidence=VerificationEvidence("other",datetime.now(timezone.utc),"Saved",source="test")
    try:
        ActionVerificationService().verify(p,e,evidence)
        assert False
    except VerificationIdentityError:
        pass

def test_failed_execution_cannot_verify():
    p=make_plan()
    finished=datetime.now(timezone.utc)
    e=make_execution(p,ExecutionStatus.FAILED,finished)
    evidence=VerificationEvidence("ctx-1",finished+timedelta(milliseconds=10),"Saved",source="test")
    r=ActionVerificationService().verify(p,e,evidence)
    assert r.status is VerificationStatus.NOT_VERIFIED
    assert r.checks[0].status is VerificationCheckStatus.FAILED

def test_fact_expectation():
    p=make_plan("fact:save_state=saved")
    finished=datetime.now(timezone.utc)
    e=make_execution(p,finished=finished)
    evidence=VerificationEvidence("ctx-1",finished+timedelta(milliseconds=1),facts=(("save_state","saved"),),source="test")
    r=ActionVerificationService().verify(p,e,evidence)
    assert r.status is VerificationStatus.VERIFIED


def test_app_is_any_accepts_bounded_windows_host_identity():
    p=make_plan("app_is_any:CalculatorApp.exe|ApplicationFrameHost.exe")
    finished=datetime.now(timezone.utc)
    e=make_execution(p,finished=finished)
    evidence=VerificationEvidence(
        "ctx-1",
        finished+timedelta(milliseconds=10),
        app_name="ApplicationFrameHost.exe",
        window_title="Calculator",
        source="test",
    )
    r=ActionVerificationService().verify(p,e,evidence,now=finished+timedelta(seconds=1))
    assert r.status is VerificationStatus.VERIFIED

def test_application_identity_expectation():
    p = make_plan("application_id:startmenu:epic")
    finished = datetime.now(timezone.utc)
    e = make_execution(p, finished=finished)
    evidence = VerificationEvidence(
        "ctx-1",
        finished + timedelta(milliseconds=10),
        application_id="startmenu:epic",
        source="test",
    )
    r = ActionVerificationService().verify(p, e, evidence, now=finished + timedelta(seconds=1))
    assert r.status is VerificationStatus.VERIFIED
