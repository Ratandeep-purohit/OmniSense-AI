"""Typed contracts for Phase 16 testing and evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Callable


class EvaluationStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class EvaluationOutcome(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class EvaluationConfig:
    enabled: bool = True
    max_cases: int = 500
    max_case_name_length: int = 120
    max_message_length: int = 1000
    fail_fast: bool = False

    def __post_init__(self) -> None:
        if not 1 <= self.max_cases <= 10_000:
            raise ValueError("max_cases is out of bounds.")
        if not 1 <= self.max_case_name_length <= 512:
            raise ValueError("max_case_name_length is out of bounds.")
        if not 1 <= self.max_message_length <= 10_000:
            raise ValueError("max_message_length is out of bounds.")


@dataclass(frozen=True, slots=True)
class EvaluationCase:
    case_id: str
    name: str
    check: Callable[[], None]
    tags: tuple[str, ...] = ()
    critical: bool = False

    def __post_init__(self) -> None:
        if not self.case_id.strip() or not self.name.strip():
            raise ValueError("Evaluation case identity is required.")
        if not callable(self.check):
            raise ValueError("Evaluation case check must be callable.")
        if any(not tag.strip() for tag in self.tags):
            raise ValueError("Evaluation case tags must not be empty.")


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    case_id: str
    name: str
    outcome: EvaluationOutcome
    duration_ms: float
    message: str = ""
    tags: tuple[str, ...] = ()
    critical: bool = False
    completed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.case_id.strip() or not self.name.strip():
            raise ValueError("Evaluation result identity is required.")
        if self.duration_ms < 0:
            raise ValueError("duration_ms cannot be negative.")
        if self.completed_at.tzinfo is None:
            raise ValueError("completed_at must be timezone-aware.")


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    suite_name: str
    generated_at: datetime
    status: EvaluationStatus
    results: tuple[EvaluationResult, ...]
    passed: int
    failed: int
    errored: int
    skipped: int

    def __post_init__(self) -> None:
        if not self.suite_name.strip():
            raise ValueError("suite_name is required.")
        if self.generated_at.tzinfo is None:
            raise ValueError("generated_at must be timezone-aware.")
        if min(self.passed, self.failed, self.errored, self.skipped) < 0:
            raise ValueError("Evaluation counts cannot be negative.")
        if self.passed + self.failed + self.errored + self.skipped != len(self.results):
            raise ValueError("Evaluation counts must match result count.")
