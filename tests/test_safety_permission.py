from datetime import datetime, timedelta, timezone

import pytest

from omnisense_ai.action_planning.models import ActionPlan, ActionRisk, ActionStep, ActionTarget, ActionType, PlanStatus
from omnisense_ai.context_engine.models import ContextAge, ContextFreshness, ContextSnapshot, DesktopContext
from omnisense_ai.safety_permission.models import PermissionDecision, PolicyReason
from omnisense_ai.safety_permission.service import SafetyPermissionEngine
from omnisense_ai.safety_permission.errors import SafetyStaleContextError


def snapshot(age_seconds=0.0):
    captured = datetime.now(timezone.utc) - timedelta(seconds=age_seconds)
    age = ContextAge(captured, age_seconds, ContextFreshness.FRESH)
    desktop = DesktopContext("ctx-1", captured, "DISPLAY1", 1, ContextFreshness.FRESH, age, (), "", None, "Test", "Window", 1, 0, ("phase06",))
    return ContextSnapshot(desktop)


def plan(risk=ActionRisk.LOW, confirm=False):
    step = ActionStep("step-1", ActionType.SCROLL, ActionTarget("target-1", "Scroll target"), (), risk, "Page position changes", False)
    return ActionPlan("plan-1", "ctx-1", "scroll", PlanStatus.READY, (step,), "explicit intent", confirm)


def test_low_risk_can_be_allowed_without_confirmation():
    result = SafetyPermissionEngine().evaluate(plan(), snapshot())
    assert result.decision == PermissionDecision.ALLOW
    assert result.reason == PolicyReason.APPROVED


def test_medium_risk_requires_confirmation():
    result = SafetyPermissionEngine().evaluate(plan(ActionRisk.MEDIUM), snapshot())
    assert result.decision == PermissionDecision.REQUIRE_CONFIRMATION


def test_high_risk_requires_confirmation():
    result = SafetyPermissionEngine().evaluate(plan(ActionRisk.HIGH), snapshot())
    assert result.decision == PermissionDecision.REQUIRE_CONFIRMATION


def test_critical_risk_is_denied_by_baseline():
    result = SafetyPermissionEngine().evaluate(plan(ActionRisk.CRITICAL), snapshot())
    assert result.decision == PermissionDecision.DENY


def test_stale_context_is_rejected():
    with pytest.raises(SafetyStaleContextError):
        SafetyPermissionEngine().evaluate(plan(), snapshot(6))


def test_context_mismatch_is_rejected():
    other = snapshot()
    other_desktop = other.context
    other_snapshot = ContextSnapshot(DesktopContext("ctx-2", other_desktop.captured_at, other_desktop.monitor_id, other_desktop.frame_sequence, other_desktop.freshness, other_desktop.age, other_desktop.facts, other_desktop.visible_text, other_desktop.window_id, other_desktop.app_name, other_desktop.window_title, other_desktop.ui_element_count, other_desktop.ui_relationship_count, other_desktop.sources))
    with pytest.raises(Exception):
        SafetyPermissionEngine().evaluate(plan(), other_snapshot)


def test_non_ready_plan_requires_clarification():
    p = ActionPlan("plan-2", "ctx-1", "unknown", PlanStatus.NEEDS_CLARIFICATION, ())
    result = SafetyPermissionEngine().evaluate(p, snapshot())
    assert result.decision == PermissionDecision.REQUIRE_CLARIFICATION


def test_restricted_action_is_denied():
    config = __import__("omnisense_ai.safety_permission.models", fromlist=["SafetyConfig"]).SafetyConfig(allowed_action_types=frozenset({"wait"}))
    result = SafetyPermissionEngine(config).evaluate(plan(), snapshot())
    assert result.decision == PermissionDecision.DENY


def test_engine_has_no_execute_method():
    assert not hasattr(SafetyPermissionEngine, "execute")
