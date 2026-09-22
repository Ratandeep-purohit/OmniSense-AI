from datetime import datetime, timezone
from threading import Event
import pytest

from omnisense_ai.action_planning.models import ActionPlan, ActionRisk, ActionStep, ActionTarget, ActionType, PlanStatus
from omnisense_ai.safety_permission.models import PermissionDecision, PermissionDecisionResult, PolicyReason
from omnisense_ai.desktop_automation.models import AutomationConfig, AutomationRequest, ExecutionStatus
from omnisense_ai.desktop_automation.service import DesktopAutomationService
from omnisense_ai.desktop_automation.errors import AutomationAuthorizationError, AutomationDisabledError, AutomationTargetError

class FakeBackend:
    def __init__(self): self.calls=[]
    def execute(self, step, target): self.calls.append((step.step_id, step.action_type, target)); return "ok"
    def close(self): pass

def make_plan(action=ActionType.SCROLL, params=()):
    step=ActionStep("step-1",action,ActionTarget("target-1","test"),tuple(params),ActionRisk.LOW,"done",False)
    return ActionPlan("plan-1","ctx-1","explicit",PlanStatus.READY,(step,),"test",False)

def decision(plan, allowed=True):
    return PermissionDecisionResult(PermissionDecision.ALLOW if allowed else PermissionDecision.DENY, PolicyReason.APPROVED, plan.plan_id, plan.context_id, ActionRisk.LOW, False, (plan.steps[0].step_id,) if allowed else ())

def test_disabled_by_default():
    p=make_plan()
    with pytest.raises(AutomationDisabledError): DesktopAutomationService(backend=FakeBackend()).execute(p,AutomationRequest(p.plan_id,p.context_id,decision(p)))

def test_only_allow_reaches_backend():
    p=make_plan()
    service=DesktopAutomationService(AutomationConfig(enabled=True),FakeBackend())
    with pytest.raises(AutomationAuthorizationError): service.execute(p,AutomationRequest(p.plan_id,p.context_id,decision(p,False)))
    assert service._backend.calls == []

def test_approved_action_executes():
    p=make_plan(params=(("amount","2"),))
    backend=FakeBackend(); result=DesktopAutomationService(AutomationConfig(enabled=True),backend).execute(p,AutomationRequest(p.plan_id,p.context_id,decision(p)))
    assert result.status==ExecutionStatus.SUCCESS and backend.calls[0][0]=="step-1"

def test_click_requires_coordinates():
    p=make_plan(ActionType.CLICK)
    with pytest.raises(AutomationTargetError): DesktopAutomationService(AutomationConfig(enabled=True),FakeBackend()).execute(p,AutomationRequest(p.plan_id,p.context_id,decision(p)))

def test_identity_mismatch_rejected():
    p=make_plan()
    req=AutomationRequest("other",p.context_id,decision(p))
    with pytest.raises(Exception): DesktopAutomationService(AutomationConfig(enabled=True),FakeBackend()).execute(p,req)

def test_cancel_before_step():
    p=make_plan()
    event=Event(); event.set()
    with pytest.raises(Exception): DesktopAutomationService(AutomationConfig(enabled=True),FakeBackend()).execute(p,AutomationRequest(p.plan_id,p.context_id,decision(p)),cancel_event=event)
