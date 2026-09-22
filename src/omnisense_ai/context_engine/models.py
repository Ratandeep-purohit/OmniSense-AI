"""Data contracts for Phase 6 desktop context."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum


class ContextSource(StrEnum):
    OBSERVED = "observed"
    DERIVED = "derived"
    USER_PROVIDED = "user_provided"


class Sensitivity(StrEnum):
    NORMAL = "normal"
    SENSITIVE = "sensitive"


class ContextFreshness(StrEnum):
    FRESH = "fresh"
    STALE = "stale"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class ContextConfig:
    max_facts: int = 500
    max_fact_value_length: int = 4096
    max_user_context_length: int = 4096
    max_age_seconds: float = 5.0
    stale_after_seconds: float = 2.0
    max_visible_text_length: int = 12_000

    def __post_init__(self) -> None:
        if self.max_facts <= 0 or self.max_facts > 10_000:
            raise ValueError("max_facts must be within 1..10000.")
        if self.max_fact_value_length <= 0 or self.max_fact_value_length > 100_000:
            raise ValueError("max_fact_value_length is out of bounds.")
        if self.max_user_context_length <= 0 or self.max_user_context_length > 100_000:
            raise ValueError("max_user_context_length is out of bounds.")
        if self.max_age_seconds <= 0 or self.max_age_seconds > 3600:
            raise ValueError("max_age_seconds is out of bounds.")
        if self.stale_after_seconds < 0 or self.stale_after_seconds > self.max_age_seconds:
            raise ValueError("stale_after_seconds must be within the context age.")
        if self.max_visible_text_length <= 0 or self.max_visible_text_length > 100_000:
            raise ValueError("max_visible_text_length is out of bounds.")


@dataclass(frozen=True, slots=True)
class ContextFact:
    key: str
    value: str
    source: ContextSource
    confidence: float
    sensitivity: Sensitivity = Sensitivity.NORMAL
    observed_at: datetime | None = None
    provenance: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("Context fact key is required.")
        if not 0 <= self.confidence <= 1:
            raise ValueError("Context fact confidence must be within 0..1.")
        if len(self.value) > 100_000:
            raise ValueError("Context fact value is too large.")
        if self.observed_at is not None and self.observed_at.tzinfo is None:
            raise ValueError("Context fact timestamp must be timezone-aware.")
        if any(not item.strip() for item in self.provenance):
            raise ValueError("Context provenance entries must not be empty.")


@dataclass(frozen=True, slots=True)
class ContextAge:
    captured_at: datetime
    age_seconds: float
    freshness: ContextFreshness

    def __post_init__(self) -> None:
        if self.captured_at.tzinfo is None:
            raise ValueError("Context timestamp must be timezone-aware.")
        if self.age_seconds < 0:
            raise ValueError("Context age must not be negative.")


@dataclass(frozen=True, slots=True)
class DesktopContext:
    context_id: str
    captured_at: datetime
    monitor_id: str
    frame_sequence: int
    freshness: ContextFreshness
    age: ContextAge
    facts: tuple[ContextFact, ...]
    visible_text: str
    window_id: int | None
    app_name: str | None
    window_title: str | None
    ui_element_count: int
    ui_relationship_count: int
    sources: tuple[str, ...]
    truncated: bool = False

    def __post_init__(self) -> None:
        if not self.context_id.strip():
            raise ValueError("Context ID is required.")
        if self.captured_at.tzinfo is None:
            raise ValueError("Context timestamp must be timezone-aware.")
        if not self.monitor_id.strip():
            raise ValueError("Context monitor ID is required.")
        if self.frame_sequence < 1:
            raise ValueError("Frame sequence must be >= 1.")
        if self.ui_element_count < 0 or self.ui_relationship_count < 0:
            raise ValueError("UI counts must not be negative.")
        if any(not item.strip() for item in self.sources):
            raise ValueError("Context sources must not be empty.")


@dataclass(frozen=True, slots=True)
class ContextSnapshot:
    context: DesktopContext
    user_context: str | None = None

    @property
    def authorization(self) -> None:
        """Authorization is deliberately not represented by context."""
        return None

    def is_fresh(self) -> bool:
        return self.context.freshness is ContextFreshness.FRESH
