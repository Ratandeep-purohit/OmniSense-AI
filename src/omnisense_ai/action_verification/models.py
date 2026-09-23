"""Typed contracts for Phase 12 post-action verification."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from ..action_planning.models import ActionType

class VerificationStatus(StrEnum):
    VERIFIED="verified"
    NOT_VERIFIED="not_verified"
    INDETERMINATE="indeterminate"
    REJECTED="rejected"

class VerificationCheckStatus(StrEnum):
    PASSED="passed"
    FAILED="failed"
    INDETERMINATE="indeterminate"

@dataclass(frozen=True, slots=True)
class VerificationConfig:
    max_age_seconds: float = 5.0
    max_evidence_text_length: int = 12000
    require_post_execution_evidence: bool = True
    allow_indeterminate: bool = True
    def __post_init__(self):
        if not 0.1 <= self.max_age_seconds <= 300: raise ValueError("max_age_seconds is out of bounds.")
        if not 1 <= self.max_evidence_text_length <= 100_000: raise ValueError("max_evidence_text_length is out of bounds.")

@dataclass(frozen=True, slots=True)
class VerificationEvidence:
    context_id: str
    captured_at: datetime
    visible_text: str = ""
    window_id: int | None = None
    app_name: str | None = None
    application_id: str | None = None
    window_title: str | None = None
    facts: tuple[tuple[str,str], ...] = ()
    source: str = "unknown"
    def __post_init__(self):
        if not self.context_id.strip(): raise ValueError("Evidence context_id is required.")
        if self.captured_at.tzinfo is None: raise ValueError("Evidence timestamp must be timezone-aware.")
        if len(self.visible_text) > 100_000: raise ValueError("Evidence text is too large.")
        if not self.source.strip(): raise ValueError("Evidence source is required.")
        if any(not k.strip() for k,_ in self.facts): raise ValueError("Evidence fact keys must not be empty.")

@dataclass(frozen=True, slots=True)
class VerificationCheck:
    step_id: str
    action_type: ActionType
    status: VerificationCheckStatus
    expectation: str
    message: str
    observed_at: datetime
    def __post_init__(self):
        if not self.step_id.strip() or not self.expectation.strip(): raise ValueError("Verification check identity is required.")
        if self.observed_at.tzinfo is None: raise ValueError("Verification timestamp must be timezone-aware.")

@dataclass(frozen=True, slots=True)
class VerificationResult:
    verification_id: str
    plan_id: str
    context_id: str
    status: VerificationStatus
    checks: tuple[VerificationCheck, ...]
    verified_at: datetime
    evidence_captured_at: datetime
    evidence_source: str
    def __post_init__(self):
        if not self.verification_id.strip() or not self.plan_id.strip() or not self.context_id.strip(): raise ValueError("Verification identifiers are required.")
        if self.verified_at.tzinfo is None or self.evidence_captured_at.tzinfo is None: raise ValueError("Verification timestamps must be timezone-aware.")
