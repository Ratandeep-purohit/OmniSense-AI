"""Performance contracts for Phase 14."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from math import ceil
from statistics import mean
from typing import Mapping


class PerformanceStatus(StrEnum):
    HEALTHY = "healthy"
    WARNING = "warning"
    BREACHED = "breached"


@dataclass(frozen=True, slots=True)
class StageBudget:
    stage: str
    warning_ms: float
    failure_ms: float

    def __post_init__(self) -> None:
        if not self.stage.strip():
            raise ValueError("Stage name must not be empty.")
        if self.warning_ms < 0 or self.failure_ms < 0:
            raise ValueError("Latency budgets must be non-negative.")
        if self.warning_ms > self.failure_ms:
            raise ValueError("warning_ms must not exceed failure_ms.")


@dataclass(frozen=True, slots=True)
class PerformanceConfig:
    enabled: bool = True
    max_samples: int = 5000
    max_stage_name_length: int = 80
    default_warning_ms: float = 100.0
    default_failure_ms: float = 500.0
    budgets: Mapping[str, StageBudget] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.max_samples < 1:
            raise ValueError("max_samples must be positive.")
        if self.max_stage_name_length < 1:
            raise ValueError("max_stage_name_length must be positive.")
        if self.default_warning_ms < 0 or self.default_failure_ms < 0:
            raise ValueError("Default latency budgets must be non-negative.")
        if self.default_warning_ms > self.default_failure_ms:
            raise ValueError("default_warning_ms must not exceed default_failure_ms.")


@dataclass(frozen=True, slots=True)
class PerformanceSample:
    stage: str
    duration_ms: float
    success: bool
    recorded_at: datetime

    def __post_init__(self) -> None:
        if not self.stage.strip():
            raise ValueError("Stage name must not be empty.")
        if self.duration_ms < 0:
            raise ValueError("Duration must be non-negative.")
        if self.recorded_at.tzinfo is None or self.recorded_at.utcoffset() is None:
            raise ValueError("recorded_at must be timezone-aware.")


@dataclass(frozen=True, slots=True)
class StageStats:
    stage: str
    count: int
    failures: int
    min_ms: float
    mean_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    max_ms: float
    status: PerformanceStatus

    @classmethod
    def from_samples(cls, stage: str, samples: tuple[PerformanceSample, ...], budget: StageBudget) -> "StageStats":
        durations = sorted(sample.duration_ms for sample in samples)
        failures = sum(not sample.success for sample in samples)

        def percentile(value: float) -> float:
            index = max(0, min(len(durations) - 1, ceil(len(durations) * value) - 1))
            return durations[index]

        p50 = percentile(0.50)
        p95 = percentile(0.95)
        p99 = percentile(0.99)
        status = (
            PerformanceStatus.BREACHED if p99 > budget.failure_ms or failures
            else PerformanceStatus.WARNING if p99 > budget.warning_ms
            else PerformanceStatus.HEALTHY
        )
        return cls(stage, len(durations), failures, round(durations[0],3), round(mean(durations),3),
                   round(p50,3), round(p95,3), round(p99,3), round(durations[-1],3), status)


@dataclass(frozen=True, slots=True)
class PerformanceReport:
    generated_at: datetime
    samples: int
    stages: tuple[StageStats, ...]
    status: PerformanceStatus

    def __post_init__(self) -> None:
        if self.generated_at.tzinfo is None or self.generated_at.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware.")
        if self.samples < 0:
            raise ValueError("samples must be non-negative.")

    @classmethod
    def empty(cls) -> "PerformanceReport":
        return cls(datetime.now(timezone.utc), 0, (), PerformanceStatus.HEALTHY)
