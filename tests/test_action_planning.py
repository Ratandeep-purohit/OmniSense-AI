from datetime import datetime,timezone
import pytest
from omnisense_ai.context_engine import ContextAge,ContextFreshness,ContextSnapshot,DesktopContext
from omnisense_ai.action_planning import ActionPlanner,ActionPlanAmbiguityError,ActionPlanSecurityError,PlanStatus
def snapshot():
    now=datetime.now(timezone.utc); c=DesktopContext("ctx-plan",now,"primary",1,ContextFreshness.FRESH,ContextAge(now,0,ContextFreshness.FRESH),(),"Open Settings",None,"test-app","Settings",0,0,("test",)); return ContextSnapshot(context=c)
def test_click_plan_is_ready():
    p=ActionPlanner().plan(snapshot(),"Click the Save button"); assert p.status is PlanStatus.READY and len(p.steps)==1 and p.requires_confirmation
def test_ambiguous_intent_requires_clarification():
    with pytest.raises(ActionPlanAmbiguityError): ActionPlanner().plan(snapshot(),"Maybe do something")
def test_high_consequence_intent_is_blocked():
    with pytest.raises(ActionPlanSecurityError): ActionPlanner().plan(snapshot(),"Delete this file")
def test_unknown_intent_does_not_create_action():
    p=ActionPlanner().plan(snapshot(),"Tell me what time it is"); assert p.status is PlanStatus.NEEDS_CLARIFICATION and not p.steps
def test_plan_never_executes(): assert not hasattr(ActionPlanner(),"execute")


def test_open_word_is_allowlisted_low_risk_plan():
    plan = ActionPlanner().plan(snapshot(), "open Microsoft Word")
    assert plan.status is PlanStatus.READY
    assert plan.requires_confirmation is False
    step = plan.steps[0]
    assert step.action_type.value == "open_app"
    params = dict(step.parameters)
    assert params["app"] == "word"
    assert step.expected_outcome == "app_is_any:WINWORD.EXE"


def test_open_calculator_uses_bounded_host_identities():
    plan = ActionPlanner().plan(snapshot(), "open calculator")
    assert plan.status is PlanStatus.READY
    assert plan.steps[0].expected_outcome == "app_is_any:CalculatorApp.exe|ApplicationFrameHost.exe"


def test_open_steam_is_allowlisted():
    plan = ActionPlanner().plan(snapshot(), "open steam")
    assert plan.status is PlanStatus.READY
    params = dict(plan.steps[0].parameters)
    assert params["app"] == "steam"
    assert params["launch_target"] == "steam://open/main"
