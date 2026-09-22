"""Typed contracts for Phase 13 bounded local memory."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum


class MemoryKind(StrEnum):
    PREFERENCE = "preference"
    FACT = "fact"
    TASK = "task"
    EPISODE = "episode"


class MemorySensitivity(StrEnum):
    NORMAL = "normal"
    SENSITIVE = "sensitive"


class MemoryStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    DELETED = "deleted"


@dataclass(frozen=True, slots=True)
class MemoryConfig:
    enabled: bool = False
    max_entries: int = 1000
    max_key_length: int = 256
    max_value_length: int = 4096
    max_query_length: int = 512
    max_results: int = 20
    retention_seconds: float = 30 * 24 * 3600
    allow_sensitive: bool = False

    def __post_init__(self) -> None:
        if not 1 <= self.max_entries <= 100_000:
            raise ValueError("max_entries must be within 1..100000.")
        if not 1 <= self.max_key_length <= 4096:
            raise ValueError("max_key_length is out of bounds.")
        if not 1 <= self.max_value_length <= 1_000_000:
            raise ValueError("max_value_length is out of bounds.")
        if not 1 <= self.max_query_length <= 100_000:
            raise ValueError("max_query_length is out of bounds.")
        if not 1 <= self.max_results <= 1000:
            raise ValueError("max_results is out of bounds.")
        if self.retention_seconds <= 0 or self.retention_seconds > 10 * 365 * 24 * 3600:
            raise ValueError("retention_seconds is out of bounds.")


@dataclass(frozen=True, slots=True)
class MemoryEntry:
    memory_id: str
    kind: MemoryKind
    key: str
    value: str
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    sensitivity: MemorySensitivity = MemorySensitivity.NORMAL
    source: str = "user"
    status: MemoryStatus = MemoryStatus.ACTIVE
    provenance: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.memory_id.strip() or not self.key.strip():
            raise ValueError("Memory identity is required.")
        if not self.value.strip():
            raise ValueError("Memory value is required.")
        for stamp in (self.created_at, self.updated_at, self.expires_at):
            if stamp.tzinfo is None:
                raise ValueError("Memory timestamps must be timezone-aware.")
        if self.updated_at < self.created_at:
            raise ValueError("updated_at cannot precede created_at.")
        if self.expires_at <= self.updated_at:
            raise ValueError("expires_at must be after updated_at.")
        if not self.source.strip():
            raise ValueError("Memory source is required.")
        if any(not item.strip() for item in self.provenance):
            raise ValueError("Memory provenance entries must not be empty.")

    def is_expired(self, *, now: datetime | None = None) -> bool:
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            raise ValueError("now must be timezone-aware.")
        return current >= self.expires_at


@dataclass(frozen=True, slots=True)
class MemoryQuery:
    query: str
    kind: MemoryKind | None = None
    limit: int = 10

    def __post_init__(self) -> None:
        if not self.query.strip():
            raise ValueError("Memory query is required.")
        if self.limit < 1 or self.limit > 1000:
            raise ValueError("Memory query limit is out of bounds.")


@dataclass(frozen=True, slots=True)
class MemoryResult:
    entries: tuple[MemoryEntry, ...]
    queried_at: datetime

    def __post_init__(self) -> None:
        if self.queried_at.tzinfo is None:
            raise ValueError("Query timestamp must be timezone-aware.")
