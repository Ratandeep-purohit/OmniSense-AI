"""Phase 9 planning boundary; never executes a plan."""

from __future__ import annotations

from uuid import uuid4

from ..context_engine.models import ContextSnapshot
from .errors import ActionPlanAmbiguityError, ActionPlanInputError, ActionPlanSecurityError
from .models import (
    ActionPlan,
    ActionPlanningConfig,
    ActionRisk,
    ActionStep,
    ActionTarget,
    ActionType,
    PlanStatus,
)


_APP_ALIASES = {
    "word": ("word", "WINWORD.EXE", "ms-word:"),
    "microsoft word": ("word", "WINWORD.EXE", "ms-word:"),
    "ms word": ("word", "WINWORD.EXE", "ms-word:"),
    "excel": ("excel", "EXCEL.EXE", "ms-excel:"),
    "microsoft excel": ("excel", "EXCEL.EXE", "ms-excel:"),
    "powerpoint": ("powerpoint", "POWERPNT.EXE", "ms-powerpoint:"),
    "microsoft powerpoint": ("powerpoint", "POWERPNT.EXE", "ms-powerpoint:"),
    "notepad": ("notepad", "notepad.exe", "notepad.exe"),
    "calculator": ("calculator", "CalculatorApp.exe|ApplicationFrameHost.exe", "calc.exe"),
    "calc": ("calculator", "CalculatorApp.exe|ApplicationFrameHost.exe", "calc.exe"),
    "steam": ("steam", "steam.exe", "steam://open/main"),
}


class ActionPlanner:
    """Turn explicit user intent into a bounded, inspectable action plan."""

    def __init__(self, config: ActionPlanningConfig | None = None) -> None:
        self.config = config or ActionPlanningConfig()

    def plan(self, snapshot: ContextSnapshot, intent: str) -> ActionPlan:
        intent = intent.strip()
        if not intent or len(intent) > self.config.max_intent_chars:
            raise ActionPlanInputError("Action intent is empty or too large.")

        low = intent.casefold()
        if any(x in low for x in ("maybe", "perhaps", "not sure", "do something")):
            raise ActionPlanAmbiguityError("Intent is ambiguous; clarification is required.")

        if any(x in low for x in ("delete", "purchase", "buy", "send money", "pay", "transfer")):
            raise ActionPlanSecurityError(
                "High-consequence intent requires the Phase 10 safety boundary."
            )

        app = self._resolve_app(low)
        if app is not None:
            key, executable, launch_target = app
            step = ActionStep(
                "step-1",
                ActionType.OPEN_APP,
                ActionTarget("application", f"Open {key}", expected_text=key),
                (("app", key), ("executable", executable), ("launch_target", launch_target)),
                ActionRisk.LOW,
                f"app_is_any:{executable}",
                True,
            )
            return ActionPlan(
                str(uuid4()),
                snapshot.context.context_id,
                intent,
                PlanStatus.READY,
                (step,),
                "Explicit request to open an allowlisted desktop application.",
                False,
            )

        if any(x in low for x in ("click", "press", "tap")):
            action_type = ActionType.CLICK
        elif any(x in low for x in ("type", "write", "enter")):
            action_type = ActionType.TYPE
        elif "scroll" in low:
            action_type = ActionType.SCROLL
        elif any(x in low for x in ("close", "exit")):
            action_type = ActionType.CLOSE_APP
        elif "wait" in low:
            action_type = ActionType.WAIT
        else:
            return ActionPlan(
                str(uuid4()),
                snapshot.context.context_id,
                intent,
                PlanStatus.NEEDS_CLARIFICATION,
                rationale="No safe action type could be derived from explicit intent.",
            )

        risk = ActionRisk.MEDIUM if action_type in (ActionType.TYPE, ActionType.CLICK) else ActionRisk.LOW
        requires_confirmation = risk != ActionRisk.LOW
        step = ActionStep(
            "step-1",
            action_type,
            ActionTarget("current-context-target", "Target described by explicit user intent."),
            (),
            risk,
            "Requested UI state should change as described.",
            action_type in (ActionType.WAIT, ActionType.SCROLL),
        )
        return ActionPlan(
            str(uuid4()),
            snapshot.context.context_id,
            intent,
            PlanStatus.READY,
            (step,),
            "Derived only from explicit user intent and current context.",
            requires_confirmation,
        )

    @staticmethod
    def _resolve_app(intent: str):
        # Match longer aliases first so "microsoft word" wins over "word".
        for alias in sorted(_APP_ALIASES, key=len, reverse=True):
            if f"open {alias}" in intent or f"launch {alias}" in intent or f"start {alias}" in intent:
                return _APP_ALIASES[alias]
        return None
