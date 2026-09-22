"""Bounded deterministic evaluation runner for Phase 16."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from time import perf_counter
from threading import RLock
from typing import Iterator

from .errors import EvaluationDisabledError, EvaluationInputError, EvaluationResourceError
from .models import (
    EvaluationCase,
    EvaluationConfig,
    EvaluationOutcome,
    EvaluationReport,
    EvaluationResult,
    EvaluationStatus,
)


class EvaluationService:
    """Run bounded checks without granting application authority."""

    def __init__(self, config: EvaluationConfig | None = None) -> None:
        self.config = config or EvaluationConfig()
        self._closed = False
        self._lock = RLock()

    def run_case(self, case: EvaluationCase) -> EvaluationResult:
        self._ensure_enabled()
        self._ensure_open()
        self._validate_case(case)
        started = perf_counter()
        outcome = EvaluationOutcome.PASS
        message = ""
        try:
            case.check()
        except AssertionError as exc:
            outcome = EvaluationOutcome.FAIL
            message = str(exc) or "assertion failed"
        except Exception as exc:
            outcome = EvaluationOutcome.ERROR
            message = f"{type(exc).__name__}: {exc}"
        return EvaluationResult(
            case_id=case.case_id,
            name=case.name,
            outcome=outcome,
            duration_ms=(perf_counter() - started) * 1000.0,
            message=message[: self.config.max_message_length],
            tags=case.tags,
            critical=case.critical,
        )

    def run_suite(self, suite_name: str, cases: tuple[EvaluationCase, ...]) -> EvaluationReport:
        self._ensure_enabled()
        self._ensure_open()
        if not isinstance(suite_name, str) or not suite_name.strip():
            raise EvaluationInputError("suite_name is required.")
        if len(suite_name) > self.config.max_case_name_length:
            raise EvaluationInputError("suite_name exceeds the configured length limit.")
        if len(cases) > self.config.max_cases:
            raise EvaluationResourceError("Evaluation case limit exceeded.")

        results: list[EvaluationResult] = []
        with self._lock:
            for case in cases:
                result = self.run_case(case)
                results.append(result)
                if self.config.fail_fast and result.outcome is not EvaluationOutcome.PASS:
                    break

        passed = sum(r.outcome is EvaluationOutcome.PASS for r in results)
        failed = sum(r.outcome is EvaluationOutcome.FAIL for r in results)
        errored = sum(r.outcome is EvaluationOutcome.ERROR for r in results)
        skipped = len(cases) - len(results)
        status = EvaluationStatus.FAILED if failed or errored else EvaluationStatus.PASSED
        if skipped and status is EvaluationStatus.PASSED:
            status = EvaluationStatus.SKIPPED
        return EvaluationReport(
            suite_name=suite_name.strip(),
            generated_at=datetime.now(timezone.utc),
            status=status,
            results=tuple(results),
            passed=passed,
            failed=failed,
            errored=errored,
            skipped=skipped,
        )

    @contextmanager
    def case(self, case_id: str, name: str, *, tags: tuple[str, ...] = (), critical: bool = False) -> Iterator[None]:
        self._ensure_enabled()
        self._ensure_open()
        self._validate_case(
            EvaluationCase(case_id=case_id, name=name, check=lambda: None, tags=tags, critical=critical)
        )
        yield

    def close(self) -> None:
        with self._lock:
            self._closed = True

    def _validate_case(self, case: EvaluationCase) -> None:
        if len(case.case_id) > self.config.max_case_name_length:
            raise EvaluationInputError("case_id exceeds the configured length limit.")
        if len(case.name) > self.config.max_case_name_length:
            raise EvaluationInputError("case name exceeds the configured length limit.")

    def _ensure_open(self) -> None:
        if self._closed:
            raise EvaluationInputError("Evaluation service is closed.")

    def _ensure_enabled(self) -> None:
        if not self.config.enabled:
            raise EvaluationDisabledError("Evaluation service is disabled.")
