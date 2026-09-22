"""Phase 11 execution service. It executes only explicitly approved, bounded plans."""
from __future__ import annotations
from datetime import datetime, timezone
from threading import RLock, Event
from uuid import uuid4
from ..action_planning.models import ActionPlan, ActionType
from ..safety_permission.models import PermissionDecision, PermissionDecisionResult
from .backend import DesktopAutomationBackend, NullDesktopAutomationBackend, ResolvedTarget
from .errors import AutomationAuthorizationError, AutomationBackendError, AutomationCancelledError, AutomationDisabledError, AutomationInputError, AutomationTargetError
from .models import ActionExecution, AutomationConfig, AutomationRequest, AutomationResult, ExecutionStatus


class DesktopAutomationService:
    def __init__(self, config: AutomationConfig | None = None, backend: DesktopAutomationBackend | None = None) -> None:
        self.config = config or AutomationConfig()
        self._backend = backend or NullDesktopAutomationBackend()
        self._lock = RLock()

    def execute(self, plan: ActionPlan, request: AutomationRequest, *, cancel_event: Event | None = None) -> AutomationResult:
        with self._lock:
            if not self.config.enabled: raise AutomationDisabledError("Desktop automation is disabled.")
            if request.plan_id != plan.plan_id or request.context_id != plan.context_id: raise AutomationInputError("Execution identity does not match the plan.")
            decision = request.decision
            if decision.plan_id != plan.plan_id or decision.context_id != plan.context_id: raise AutomationAuthorizationError("Permission decision is bound to a different plan or context.")
            if decision.decision != PermissionDecision.ALLOW: raise AutomationAuthorizationError("Only an ALLOW decision can reach execution.")
            if len(plan.steps) == 0 or len(plan.steps) > self.config.max_steps: raise AutomationInputError("Plan step count is outside execution limits.")
            allowed = set(decision.approved_step_ids)
            if any(step.step_id not in allowed for step in plan.steps): raise AutomationAuthorizationError("Every plan step must be explicitly approved.")

            started = datetime.now(timezone.utc)
            results=[]
            for step in plan.steps:
                if cancel_event and cancel_event.is_set(): raise AutomationCancelledError("Execution cancelled before the next step.")
                step_started=datetime.now(timezone.utc)
                try:
                    target=self._resolve_target(step)
                    message=self._backend.execute(step,target)
                    status=ExecutionStatus.SUCCESS
                except (ValueError, KeyError) as exc:
                    raise AutomationTargetError(str(exc)) from exc
                except AutomationTargetError:
                    raise
                except Exception as exc:
                    raise AutomationBackendError(f"Desktop backend failed for {step.step_id}: {type(exc).__name__}") from exc
                results.append(ActionExecution(step.step_id,step.action_type,status,step_started,datetime.now(timezone.utc),message))
            return AutomationResult(str(uuid4()),plan.plan_id,plan.context_id,ExecutionStatus.SUCCESS,tuple(results),started,datetime.now(timezone.utc))

    def _resolve_target(self, step):
        params=dict(step.parameters)
        target=step.target
        if target is None: raise AutomationTargetError("Execution target is required.")
        x = params.get("x"); y = params.get("y")
        if step.action_type in (ActionType.CLICK, ActionType.MOVE):
            try: x=int(x); y=int(y)
            except (TypeError,ValueError) as exc: raise AutomationTargetError("CLICK/MOVE requires integer x/y parameters.") from exc
            if not 0 <= x <= 10000 or not 0 <= y <= 10000: raise AutomationTargetError("Target coordinates are outside safety bounds.")
        return ResolvedTarget(x=x,y=y,app_key=target.window_id)

    def close(self) -> None:
        with self._lock:
            self._backend.close()
