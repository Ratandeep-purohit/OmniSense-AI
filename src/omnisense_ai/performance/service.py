"""Bounded latency measurement and benchmark service for Phase 14."""
from __future__ import annotations

from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter
from threading import RLock
from typing import Callable, Iterator, TypeVar

from .errors import PerformanceDisabledError, PerformanceInputError
from .models import PerformanceConfig, PerformanceReport, PerformanceSample, PerformanceStatus, StageBudget, StageStats

T = TypeVar("T")

@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    iterations: int
    warmups: int
    min_ms: float
    mean_ms: float
    p50_ms: float
    p95_ms: float
    max_ms: float
    failures: int

    @property
    def status(self) -> PerformanceStatus:
        return PerformanceStatus.BREACHED if self.failures else PerformanceStatus.HEALTHY

class PerformanceMonitor:
    """Observe latency without changing execution or granting authority."""

    def __init__(self, config: PerformanceConfig | None = None) -> None:
        self.config = config or PerformanceConfig()
        self._samples: deque[PerformanceSample] = deque(maxlen=self.config.max_samples)
        self._lock = RLock()
        self._closed = False

    def record(self, stage: str, duration_ms: float, *, success: bool = True,
               recorded_at: datetime | None = None) -> PerformanceSample:
        self._ensure_open()
        normalized = self._validate_stage(stage)
        try:
            duration = float(duration_ms)
        except (TypeError, ValueError) as exc:
            raise PerformanceInputError("duration_ms must be numeric.") from exc
        if duration < 0:
            raise PerformanceInputError("duration_ms must be non-negative.")
        if not isinstance(success, bool):
            raise PerformanceInputError("success must be boolean.")
        sample = PerformanceSample(normalized, duration, success, recorded_at or datetime.now(timezone.utc))
        with self._lock:
            self._samples.append(sample)
        return sample

    @contextmanager
    def measure(self, stage: str) -> Iterator[None]:
        self._ensure_open()
        normalized = self._validate_stage(stage)
        started = perf_counter()
        success = True
        try:
            yield
        except Exception:
            success = False
            raise
        finally:
            self.record(normalized, (perf_counter() - started) * 1000.0, success=success)

    def timed(self, stage: str, operation: Callable[[], T]) -> T:
        if not callable(operation):
            raise PerformanceInputError("operation must be callable.")
        with self.measure(stage):
            return operation()

    def snapshot(self, *, now: datetime | None = None) -> PerformanceReport:
        self._ensure_open()
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None or current.utcoffset() is None:
            raise PerformanceInputError("now must be timezone-aware.")
        with self._lock:
            samples = tuple(self._samples)
        grouped: dict[str, list[PerformanceSample]] = {}
        for sample in samples:
            grouped.setdefault(sample.stage, []).append(sample)
        stages = tuple(
            StageStats.from_samples(stage, tuple(grouped[stage]), self._budget(stage))
            for stage in sorted(grouped)
        )
        statuses = [item.status for item in stages]
        status = (PerformanceStatus.BREACHED if PerformanceStatus.BREACHED in statuses
                  else PerformanceStatus.WARNING if PerformanceStatus.WARNING in statuses
                  else PerformanceStatus.HEALTHY)
        return PerformanceReport(current, len(samples), stages, status)

    def benchmark(self, operation: Callable[[], object], *, iterations: int = 10, warmups: int = 1) -> BenchmarkResult:
        if not callable(operation):
            raise PerformanceInputError("operation must be callable.")
        if iterations < 1 or warmups < 0 or iterations > self.config.max_samples:
            raise PerformanceInputError("iterations are outside configured bounds.")
        for _ in range(warmups):
            operation()
        durations: list[float] = []
        failures = 0
        for _ in range(iterations):
            started = perf_counter()
            try:
                operation()
            except Exception:
                failures += 1
            finally:
                durations.append((perf_counter() - started) * 1000.0)
        ordered = sorted(durations)
        def percentile(value: float) -> float:
            index = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * value)))
            return ordered[index]
        return BenchmarkResult(iterations, warmups, round(ordered[0],3), round(sum(ordered)/len(ordered),3),
                               round(percentile(.50),3), round(percentile(.95),3), round(ordered[-1],3), failures)

    def budgets(self) -> tuple[StageBudget, ...]:
        self._ensure_open()
        return tuple(sorted(self.config.budgets.values(), key=lambda item: item.stage))

    def reset(self) -> None:
        self._ensure_open()
        with self._lock:
            self._samples.clear()

    def close(self) -> None:
        with self._lock:
            self._closed = True
            self._samples.clear()

    def _budget(self, stage: str) -> StageBudget:
        return self.config.budgets.get(stage, StageBudget(stage, self.config.default_warning_ms, self.config.default_failure_ms))

    def _validate_stage(self, stage: str) -> str:
        if not isinstance(stage, str):
            raise PerformanceInputError("stage must be a string.")
        normalized = stage.strip()
        if not normalized or len(normalized) > self.config.max_stage_name_length:
            raise PerformanceInputError("stage name is empty or exceeds configured length.")
        return normalized

    def _ensure_open(self) -> None:
        if self._closed:
            raise PerformanceInputError("Performance monitor is closed.")
