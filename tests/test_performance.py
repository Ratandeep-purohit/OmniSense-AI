from datetime import datetime

import pytest

from omnisense_ai.performance import PerformanceConfig, PerformanceInputError, PerformanceMonitor, PerformanceStatus, StageBudget


def test_record_and_snapshot() -> None:
    monitor = PerformanceMonitor(PerformanceConfig(budgets={"capture": StageBudget("capture", 10, 20)}))
    monitor.record("capture", 4)
    monitor.record("capture", 8)
    report = monitor.snapshot()
    assert report.samples == 2
    assert report.status is PerformanceStatus.HEALTHY
    assert report.stages[0].mean_ms == 6
    assert report.stages[0].p95_ms == 8


def test_warning_then_breach() -> None:
    monitor = PerformanceMonitor(PerformanceConfig(budgets={"stage": StageBudget("stage", 10, 20)}))
    monitor.record("stage", 15)
    assert monitor.snapshot().status is PerformanceStatus.WARNING
    monitor.record("stage", 25)
    assert monitor.snapshot().status is PerformanceStatus.BREACHED


def test_failed_sample_breaches() -> None:
    monitor = PerformanceMonitor()
    monitor.record("ocr", 1, success=False)
    assert monitor.snapshot().status is PerformanceStatus.BREACHED


def test_measure_records_success_and_failure() -> None:
    monitor = PerformanceMonitor()
    with monitor.measure("success"):
        pass
    with pytest.raises(RuntimeError):
        with monitor.measure("failure"):
            raise RuntimeError("boom")
    assert monitor.snapshot().samples == 2
    assert monitor.snapshot().stages[0].failures == 1


def test_timed_preserves_result() -> None:
    monitor = PerformanceMonitor()
    assert monitor.timed("operation", lambda: 42) == 42
    assert monitor.snapshot().samples == 1


def test_benchmark_reports_failures() -> None:
    monitor = PerformanceMonitor(PerformanceConfig(max_samples=10))
    calls = {"count": 0}
    def operation() -> None:
        calls["count"] += 1
        if calls["count"] == 3:
            raise ValueError("expected")
    result = monitor.benchmark(operation, iterations=4, warmups=1)
    assert result.iterations == 4
    assert result.failures == 1


def test_retention_is_bounded() -> None:
    monitor = PerformanceMonitor(PerformanceConfig(max_samples=3))
    for value in range(5):
        monitor.record("stage", value)
    assert monitor.snapshot().samples == 3


def test_invalid_inputs() -> None:
    monitor = PerformanceMonitor()
    with pytest.raises(PerformanceInputError):
        monitor.record("", 1)
    with pytest.raises(PerformanceInputError):
        monitor.record("stage", -1)
    with pytest.raises(PerformanceInputError):
        monitor.snapshot(now=datetime.now())


def test_reset_and_close() -> None:
    monitor = PerformanceMonitor()
    monitor.record("stage", 1)
    monitor.reset()
    assert monitor.snapshot().samples == 0
    monitor.close()
    with pytest.raises(PerformanceInputError):
        monitor.record("stage", 1)


def test_budget_order() -> None:
    monitor = PerformanceMonitor(PerformanceConfig(budgets={"z": StageBudget("z",1,2), "a": StageBudget("a",1,2)}))
    assert [item.stage for item in monitor.budgets()] == ["a", "z"]



def test_disabled_monitor_rejects_collection() -> None:
    from omnisense_ai.performance import PerformanceDisabledError

    monitor = PerformanceMonitor(PerformanceConfig(enabled=False))
    with pytest.raises(PerformanceDisabledError):
        monitor.record("stage", 1)
    with pytest.raises(PerformanceDisabledError):
        monitor.snapshot()
