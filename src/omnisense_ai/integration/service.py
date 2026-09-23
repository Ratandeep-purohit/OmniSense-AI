"""Controlled production orchestration across OmniSense boundaries."""
from __future__ import annotations
from datetime import datetime,timezone
from typing import Callable
from ..action_planning.models import ActionPlan
from ..action_planning.service import ActionPlanner
from ..action_verification.models import VerificationEvidence
from ..action_verification.service import ActionVerificationService
from ..context_engine.models import ContextSnapshot
from ..desktop_automation.backend import NullDesktopAutomationBackend
from ..desktop_automation.models import AutomationConfig,AutomationRequest,AutomationResult
from ..desktop_automation.service import DesktopAutomationService
from ..safety_permission.service import SafetyPermissionEngine
from ..security.service import SecurityService
from ..action_graph.service import ActionGraphBuilder
from ..preconditions import PreconditionEngine
from ..capabilities import Capability,CapabilityManager
from ..observability import EventLog
from .errors import IntegrationInputError
from .models import PipelineResult,PipelineStatus,PipelineTrace

class OmniSensePipeline:
    """AI proposes; policy authorizes; capability grants authority; automation executes; verification proves."""
    def __init__(self,*,planner=None,security=None,safety=None,automation=None,verification=None,
                 graph_builder=None,preconditions=None,capabilities=None,observability=None,
                 require_execution_capability=False):
        self.security=security or SecurityService()
        self.planner=planner or ActionPlanner()
        self.safety=safety or SafetyPermissionEngine()
        self.automation=automation or DesktopAutomationService(AutomationConfig(enabled=False),NullDesktopAutomationBackend())
        self.verification=verification or ActionVerificationService()
        self.graph_builder=graph_builder or ActionGraphBuilder()
        self.preconditions=preconditions or PreconditionEngine()
        self.capabilities=capabilities or CapabilityManager()
        self.observability=observability or EventLog()
        self.require_execution_capability=require_execution_capability

    def run(self,snapshot:ContextSnapshot,intent:str,*,evidence=None,evidence_provider:Callable|None=None,
            before_evidence_provider:Callable|None=None,now=None)->PipelineResult:
        current=now or datetime.now(timezone.utc)
        if current.tzinfo is None: raise IntegrationInputError("now must be timezone-aware.")
        if not intent or not intent.strip(): raise IntegrationInputError("Pipeline intent is required.")
        if evidence is not None and evidence_provider is not None: raise IntegrationInputError("Provide evidence or evidence_provider, not both.")
        trace_id=snapshot.context.context_id; stages=["context"]
        self.observability.emit("pipeline.start",trace_id,intent_chars=len(intent))
        sanitized=self.security.inspect_text(intent).sanitized_text; stages.append("security")
        try: plan=self.planner.plan(snapshot,sanitized)
        except Exception as exc: return self._result(PipelineStatus.BLOCKED,snapshot,sanitized,None,None,None,None,stages,"action_planning",exc)
        stages.append("action_planning")
        graph=self.graph_builder.build(plan); stages.append("action_graph")
        pre=self.preconditions.evaluate(plan,snapshot,max_age_seconds=self.safety.config.max_context_age_seconds)
        if not pre.allowed:
            return PipelineResult(PipelineStatus.BLOCKED,snapshot.context.context_id,sanitized,plan,None,None,None,PipelineTrace(tuple(stages),"preconditions"),"; ".join(pre.failures))
        stages.append("preconditions")
        if self.require_execution_capability and not self.capabilities.has(Capability.EXECUTE,current):
            return PipelineResult(PipelineStatus.BLOCKED,snapshot.context.context_id,sanitized,plan,None,None,None,PipelineTrace(tuple(stages),"capability"),"Desktop execution capability is not granted for this session.")
        try: decision=self.safety.evaluate(plan,snapshot)
        except Exception as exc: return self._result(PipelineStatus.BLOCKED,snapshot,sanitized,plan,None,None,None,stages+["safety"],"safety",exc)
        stages.append("safety")
        if not decision.allowed:
            return PipelineResult(PipelineStatus.BLOCKED,snapshot.context.context_id,sanitized,plan,decision,None,None,PipelineTrace(tuple(stages),"safety"),decision.message)
        before_evidence=before_evidence_provider(plan,snapshot) if before_evidence_provider else None
        try:
            execution=self.automation.execute(plan,AutomationRequest(plan.plan_id,plan.context_id,decision))
        except Exception as exc: return self._result(PipelineStatus.FAILED,snapshot,sanitized,plan,decision,None,None,stages+["desktop_automation"],"desktop_automation",exc)
        stages.append("desktop_automation")
        if evidence_provider:
            try: evidence=evidence_provider(plan,execution)
            except Exception as exc: return self._result(PipelineStatus.NOT_VERIFIED,snapshot,sanitized,plan,decision,execution,None,stages+["verification"],"verification",exc)
            if not isinstance(evidence,VerificationEvidence): return self._result(PipelineStatus.NOT_VERIFIED,snapshot,sanitized,plan,decision,execution,None,stages+["verification"],"verification",IntegrationInputError("evidence_provider must return VerificationEvidence."))
        if evidence is None:
            return PipelineResult(PipelineStatus.NOT_VERIFIED,snapshot.context.context_id,sanitized,plan,decision,execution,None,PipelineTrace(tuple(stages),"verification"),"Post-execution evidence is required for verification.")
        try: verification=self.verification.verify(plan,execution,evidence,before_evidence=before_evidence,now=current)
        except Exception as exc: return self._result(PipelineStatus.NOT_VERIFIED,snapshot,sanitized,plan,decision,execution,None,stages+["verification"],"verification",exc)
        stages.append("verification")
        status=PipelineStatus.COMPLETED if verification.status.value=="verified" else PipelineStatus.NOT_VERIFIED
        self.observability.emit("pipeline.finish",trace_id,status.value,plan_id=plan.plan_id,verification=verification.status.value)
        return PipelineResult(status,snapshot.context.context_id,sanitized,plan,decision,execution,verification,PipelineTrace(tuple(stages)), "Action completed and was verified." if status is PipelineStatus.COMPLETED else "Action executed, but OmniSense could not verify the expected result.")

    @staticmethod
    def _result(status,snapshot,intent,plan,decision,execution,verification,stages,blocked_at,exc):
        return PipelineResult(status,snapshot.context.context_id,intent,plan,decision,execution,verification,PipelineTrace(tuple(stages),blocked_at),f"{type(exc).__name__}: {exc}")
