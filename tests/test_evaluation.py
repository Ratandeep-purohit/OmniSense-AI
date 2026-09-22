import pytest

from omnisense_ai.evaluation import (
    EvaluationCase,
    EvaluationConfig,
    EvaluationDisabledError,
    EvaluationInputError,
    EvaluationOutcome,
    EvaluationResourceError,
    EvaluationService,
    EvaluationStatus,
)


def passing_case() -> EvaluationCase:
    return EvaluationCase("pass-1", "passing case", lambda: None, tags=("smoke",))


def failing_case() -> EvaluationCase:
    return EvaluationCase("fail-1", "failing case", lambda: (_ for _ in ()).throw(AssertionError("expected")))


def error_case() -> EvaluationCase:
    return EvaluationCase("error-1", "error case", lambda: (_ for _ in ()).throw(RuntimeError("boom")))


def test_passing_case() -> None:
    result = EvaluationService().run_case(passing_case())
    assert result.outcome is EvaluationOutcome.PASS
    assert result.duration_ms >= 0


def test_failing_case_is_recorded() -> None:
    result = EvaluationService().run_case(failing_case())
    assert result.outcome is EvaluationOutcome.FAIL
    assert "expected" in result.message


def test_error_case_is_distinguished() -> None:
    result = EvaluationService().run_case(error_case())
    assert result.outcome is EvaluationOutcome.ERROR
    assert "RuntimeError" in result.message


def test_suite_aggregates_results() -> None:
    report = EvaluationService().run_suite("smoke", (passing_case(), failing_case(), error_case()))
    assert report.status is EvaluationStatus.FAILED
    assert (report.passed, report.failed, report.errored, report.skipped) == (1, 1, 1, 0)


def test_fail_fast_marks_remaining_cases_skipped() -> None:
    service = EvaluationService(EvaluationConfig(fail_fast=True))
    report = service.run_suite("smoke", (passing_case(), failing_case(), passing_case()))
    assert report.status is EvaluationStatus.FAILED
    assert report.skipped == 1
    assert len(report.results) == 2


def test_case_and_suite_bounds() -> None:
    service = EvaluationService(EvaluationConfig(max_cases=1))
    with pytest.raises(EvaluationResourceError):
        service.run_suite("too-many", (passing_case(), passing_case()))

    with pytest.raises(EvaluationInputError):
        service.run_suite("", ())


def test_disabled_and_closed_lifecycle() -> None:
    with pytest.raises(EvaluationDisabledError):
        EvaluationService(EvaluationConfig(enabled=False)).run_case(passing_case())

    service = EvaluationService()
    service.close()
    with pytest.raises(EvaluationInputError):
        service.run_case(passing_case())


def test_invalid_case_contracts() -> None:
    with pytest.raises(ValueError):
        EvaluationCase("", "name", lambda: None)
    with pytest.raises(ValueError):
        EvaluationCase("id", "name", None)  # type: ignore[arg-type]


def test_critical_case_metadata_is_preserved() -> None:
    case = EvaluationCase("critical", "critical case", lambda: None, critical=True)
    result = EvaluationService().run_case(case)
    assert result.critical is True


def test_suite_report_is_timezone_aware() -> None:
    report = EvaluationService().run_suite("time", (passing_case(),))
    assert report.generated_at.tzinfo is not None
