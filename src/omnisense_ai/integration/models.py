"""Typed contracts for Phase 17 full-pipeline integration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ..action_planning.models import ActionPlan
from ..action_verification.models import VerificationResult
from ..desktop_automation.models import AutomationResult
from ..safety_permission.models import PermissionDecisionResult


class PipelineStatus(StrEnum):
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    NOT_VERIFIED = "not_verified"


@dataclass(frozen=True, slots=True)
class PipelineTrace:
    stages: tuple[str, ...]
    blocked_at: str | None = None

    def __post_init__(self) -> None:
        if any(not stage.strip() for stage in self.stages):
            raise ValueError("Pipeline stages must not be empty.")


@dataclass(frozen=True, slots=True)
class PipelineResult:
    status: PipelineStatus
    context_id: str
    intent: str
    plan: ActionPlan | None
    decision: PermissionDecisionResult | None
    execution: AutomationResult | None
    verification: VerificationResult | None
    trace: PipelineTrace
    message: str = ""
