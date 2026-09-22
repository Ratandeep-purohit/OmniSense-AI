"""Typed contracts for Phase 11 bounded desktop automation."""
from dataclasses import dataclass
from enum import StrEnum
from datetime import datetime, timezone
from ..action_planning.models import ActionType
from ..safety_permission.models import PermissionDecisionResult


class ExecutionStatus(StrEnum):
    SUCCESS="success"; FAILED="failed"; REJECTED="rejected"; CANCELLED="cancelled"; TIMEOUT="timeout"; PARTIAL="partial"


@dataclass(frozen=True, slots=True)
class AutomationConfig:
    enabled: bool = False
    max_steps: int = 10
    action_timeout_seconds: float = 10.0
    max_text_length: int = 4000
    max_scroll_amount: int = 10
    allowed_apps: frozenset[str] = frozenset()

    def __post_init__(self):
        if not 1 <= self.max_steps <= 20: raise ValueError("max_steps is out of bounds.")
        if not 0.1 <= self.action_timeout_seconds <= 120: raise ValueError("action_timeout_seconds is out of bounds.")
        if not 1 <= self.max_text_length <= 100_000: raise ValueError("max_text_length is out of bounds.")
        if not 1 <= self.max_scroll_amount <= 100: raise ValueError("max_scroll_amount is out of bounds.")


@dataclass(frozen=True, slots=True)
class AutomationRequest:
    plan_id: str
    context_id: str
    decision: PermissionDecisionResult

    def __post_init__(self):
        if not self.plan_id.strip() or not self.context_id.strip(): raise ValueError("Execution identity is required.")


@dataclass(frozen=True, slots=True)
class ActionExecution:
    step_id: str
    action_type: ActionType
    status: ExecutionStatus
    started_at: datetime
    finished_at: datetime
    message: str

    def __post_init__(self):
        if self.started_at.tzinfo is None or self.finished_at.tzinfo is None: raise ValueError("Execution timestamps must be timezone-aware.")


@dataclass(frozen=True, slots=True)
class AutomationResult:
    execution_id: str
    plan_id: str
    context_id: str
    status: ExecutionStatus
    steps: tuple[ActionExecution, ...]
    started_at: datetime
    finished_at: datetime

    def __post_init__(self):
        if not self.execution_id.strip() or not self.plan_id.strip() or not self.context_id.strip(): raise ValueError("Execution identifiers are required.")
        if self.started_at.tzinfo is None or self.finished_at.tzinfo is None: raise ValueError("Automation timestamps must be timezone-aware.")
