"""Phase 9 planning boundary; never executes a plan."""

from __future__ import annotations

from uuid import uuid4

from ..application_discovery import WindowsApplicationResolver
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


class ActionPlanner:
    """Turn explicit user intent into a bounded, inspectable action plan.

    Application opening uses OS-backed discovery. There is no developer
    maintained per-application execution allowlist.
    """

    def __init__(
        self,
        config: ActionPlanningConfig | None = None,
        *,
        application_resolver: WindowsApplicationResolver | None = None,
    ) -> None:
        self.config = config or ActionPlanningConfig()
        self.application_resolver = application_resolver or WindowsApplicationResolver()

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
            query, candidate = app
            process_name = candidate.process_name
            if process_name:
                executable = process_name
                expected = f"app_is_any:{process_name}"
            else:
                executable = candidate.display_name
                expected = f"window_title_contains:{candidate.display_name}"

            step = ActionStep(
                "step-1",
                ActionType.OPEN_APP,
                ActionTarget(
                    "application",
                    f"Open {candidate.display_name}",
                    expected_text=candidate.display_name,
                ),
                (
                    ("app", query),
                    ("display_name", candidate.display_name),
                    ("launch_target", candidate.launch_target),
                    ("source", candidate.source),
                    ("application_id", candidate.application_id),
                ),
                ActionRisk.LOW,
                expected,
                True,
            )
            return ActionPlan(
                str(uuid4()),
                snapshot.context.context_id,
                intent,
                PlanStatus.READY,
                (step,),
                "Explicit request resolved to a Windows-discovered application entry point.",
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

    def _resolve_app(self, intent: str):
        for verb in ("open ", "launch ", "start "):
            if intent.startswith(verb):
                query = intent[len(verb):].strip()
                if not query:
                    return None
                candidate = self.application_resolver.resolve(query)
                if candidate is not None:
                    return query, candidate
                return None
        return None
