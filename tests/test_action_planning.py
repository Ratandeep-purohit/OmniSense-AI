from datetime import datetime, timezone

import pytest

from omnisense_ai.application_discovery import ApplicationCandidate
from omnisense_ai.context_engine import ContextAge, ContextFreshness, ContextSnapshot, DesktopContext
from omnisense_ai.action_planning import ActionPlanner, ActionPlanAmbiguityError, ActionPlanSecurityError, PlanStatus


class FakeResolver:
    candidates = {
        "microsoft word": ApplicationCandidate(
            "test:word", "Microsoft Word", r"C:\Apps\Word.lnk", "start_menu", "WINWORD.EXE"
        ),
        "calculator": ApplicationCandidate(
            "test:calculator", "Calculator", r"C:\Apps\Calculator.lnk", "start_menu", None
        ),
        "steam": ApplicationCandidate(
            "test:steam", "Steam", r"C:\Apps\Steam.lnk", "start_menu", "steam.exe"
        ),
    }

    def resolve(self, query):
        return self.candidates.get(query)

    def is_trusted_target(self, target):
        return target in {candidate.launch_target for candidate in self.candidates.values()}


def snapshot():
    now = datetime.now(timezone.utc)
    c = DesktopContext(
        "ctx-plan", now, "primary", 1, ContextFreshness.FRESH,
        ContextAge(now, 0, ContextFreshness.FRESH), (), "Open Settings",
        None, "test-app", "Settings", 0, 0, ("test",)
    )
    return ContextSnapshot(context=c)


def planner():
    return ActionPlanner(application_resolver=FakeResolver())


def test_click_plan_is_ready():
    p = planner().plan(snapshot(), "Click the Save button")
    assert p.status is PlanStatus.READY and len(p.steps) == 1 and p.requires_confirmation


def test_ambiguous_intent_requires_clarification():
    with pytest.raises(ActionPlanAmbiguityError):
        planner().plan(snapshot(), "Maybe do something")


def test_high_consequence_intent_is_blocked():
    with pytest.raises(ActionPlanSecurityError):
        planner().plan(snapshot(), "Delete this file")


def test_unknown_intent_does_not_create_action():
    p = planner().plan(snapshot(), "Tell me what time it is")
    assert p.status is PlanStatus.NEEDS_CLARIFICATION and not p.steps


def test_plan_never_executes():
    assert not hasattr(ActionPlanner(), "execute")


def test_open_word_uses_discovered_application():
    plan = planner().plan(snapshot(), "open Microsoft Word")
    assert plan.status is PlanStatus.READY
    assert plan.requires_confirmation is False
    step = plan.steps[0]
    assert step.action_type.value == "open_app"
    params = dict(step.parameters)
    assert params["display_name"] == "Microsoft Word"
    assert params["launch_target"].endswith("Word.lnk")
    assert step.expected_outcome.startswith("application_id:")


def test_open_calculator_can_use_title_when_process_identity_is_unavailable():
    plan = planner().plan(snapshot(), "open calculator")
    assert plan.status is PlanStatus.READY
    assert plan.steps[0].expected_outcome.startswith("application_id:")


def test_open_steam_uses_discovered_application():
    plan = planner().plan(snapshot(), "open steam")
    assert plan.status is PlanStatus.READY
    params = dict(plan.steps[0].parameters)
    assert params["display_name"] == "Steam"
    assert params["launch_target"].endswith("Steam.lnk")


def test_unresolved_application_does_not_create_execution_plan():
    plan = planner().plan(snapshot(), "open an application that is not installed")
    assert plan.status is PlanStatus.NEEDS_CLARIFICATION
    assert not plan.steps
