"""Precondition evaluation before authorization/execution."""
from dataclasses import dataclass
from ..action_planning.models import ActionPlan,PlanStatus
from ..context_engine.models import ContextSnapshot
@dataclass(frozen=True,slots=True)
class PreconditionResult:
    allowed: bool
    checks: tuple[str,...]
    failures: tuple[str,...]=()
class PreconditionEngine:
    def evaluate(self,plan:ActionPlan,snapshot:ContextSnapshot,*,max_age_seconds:float=5.0)->PreconditionResult:
        checks=["plan.ready","context.identity","context.fresh","steps.bounded"]
        failures=[]
        if plan.status is not PlanStatus.READY: failures.append("plan is not READY")
        if plan.context_id!=snapshot.context.context_id: failures.append("plan/context identity mismatch")
        if not snapshot.is_fresh(max_age_seconds=max_age_seconds): failures.append("context is stale")
        if not plan.steps or len(plan.steps)>10: failures.append("step count outside bounded execution limit")
        return PreconditionResult(not failures,tuple(checks),tuple(failures))
