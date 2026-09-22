"""Bounded memory service for Phase 13."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from threading import RLock
from uuid import uuid4

from .backend import InMemoryMemoryBackend, MemoryBackend
from .errors import (
    MemoryDisabledError,
    MemoryInputError,
    MemoryNotFoundError,
    MemoryResourceError,
    MemorySecurityError,
)
from .models import (
    MemoryConfig,
    MemoryEntry,
    MemoryKind,
    MemoryResult,
    MemorySensitivity,
    MemoryStatus,
)


class MemoryService:
    """Owns explicit, bounded, user-controlled memory.

    Memory never receives raw screenshots and never grants desktop authority.
    """

    def __init__(
        self,
        config: MemoryConfig | None = None,
        backend: MemoryBackend | None = None,
    ) -> None:
        self.config = config or MemoryConfig()
        self.backend = backend or InMemoryMemoryBackend()
        self._lock = RLock()
        self._closed = False

    def remember(
        self,
        *,
        kind: MemoryKind,
        key: str,
        value: str,
        source: str = "user",
        sensitivity: MemorySensitivity = MemorySensitivity.NORMAL,
        provenance: tuple[str, ...] = (),
        now: datetime | None = None,
    ) -> MemoryEntry:
        self._ensure_enabled()
        current = self._now(now)
        self._validate_text(key, self.config.max_key_length, "Memory key")
        self._validate_text(value, self.config.max_value_length, "Memory value")
        if not source.strip():
            raise MemoryInputError("Memory source is required.")
        if sensitivity is MemorySensitivity.SENSITIVE and not self.config.allow_sensitive:
            raise MemorySecurityError("Sensitive memory is disabled by policy.")
        if any(not item.strip() for item in provenance):
            raise MemoryInputError("Memory provenance entries must not be empty.")

        with self._lock:
            self._purge_expired(current)
            existing = self._find_same_key(kind, key)
            memory_id = existing.memory_id if existing else f"mem-{uuid4().hex}"
            created_at = existing.created_at if existing else current
            entry = MemoryEntry(
                memory_id=memory_id,
                kind=kind,
                key=key.strip(),
                value=value.strip(),
                created_at=created_at,
                updated_at=current,
                expires_at=current + timedelta(seconds=self.config.retention_seconds),
                sensitivity=sensitivity,
                source=source.strip(),
                status=MemoryStatus.ACTIVE,
                provenance=tuple(provenance),
            )
            if existing is None and self._count(current) >= self.config.max_entries:
                raise MemoryResourceError("Memory entry limit reached.")
            self.backend.put(entry)
            return entry

    def recall(
        self,
        query: str,
        *,
        kind: MemoryKind | None = None,
        limit: int | None = None,
        now: datetime | None = None,
    ) -> MemoryResult:
        self._ensure_enabled()
        self._validate_text(query, self.config.max_query_length, "Memory query")
        requested = limit if limit is not None else self.config.max_results
        if requested < 1 or requested > self.config.max_results:
            raise MemoryInputError("Memory result limit is out of bounds.")
        current = self._now(now)
        with self._lock:
            self._purge_expired(current)
            entries = self.backend.search(
                query.strip(),
                kind=kind,
                limit=requested,
                now=current,
            )
        return MemoryResult(entries=entries, queried_at=current)

    def forget(self, memory_id: str, *, now: datetime | None = None) -> None:
        self._ensure_enabled()
        if not memory_id.strip():
            raise MemoryInputError("Memory ID is required.")
        with self._lock:
            if self.backend.get(memory_id) is None:
                raise MemoryNotFoundError(memory_id)
            self.backend.delete(memory_id)

    def clear(self) -> None:
        self._ensure_enabled()
        with self._lock:
            for entry in self.backend.list_active():
                self.backend.delete(entry.memory_id)

    def recall_all(self, *, now: datetime | None = None) -> tuple[MemoryEntry, ...]:
        self._ensure_enabled()
        current = self._now(now)
        with self._lock:
            self._purge_expired(current)
            return self.backend.list_active(now=current)

    def close(self) -> None:
        with self._lock:
            if not self._closed:
                self.backend.close()
                self._closed = True

    def _find_same_key(self, kind: MemoryKind, key: str) -> MemoryEntry | None:
        if isinstance(self.backend, InMemoryMemoryBackend):
            for entry in self.backend.list_active():
                if entry.kind is kind and entry.key.casefold() == key.strip().casefold():
                    return entry
            return None
        # Generic backends can expose exact matching through search.
        matches = self.backend.search(key.strip(), kind=kind, limit=self.config.max_results)
        for entry in matches:
            if entry.key.casefold() == key.strip().casefold():
                return entry
        return None

    def _purge_expired(self, now: datetime) -> None:
        for entry in self.backend.list_active(now=now):
            if entry.is_expired(now=now):
                self.backend.delete(entry.memory_id)

    def _count(self, now: datetime) -> int:
        return len(self.backend.list_active(now=now))

    def _ensure_enabled(self) -> None:
        if self._closed:
            raise MemoryDisabledError("Memory service is closed.")
        if not self.config.enabled:
            raise MemoryDisabledError("Memory is disabled by default.")

    @staticmethod
    def _validate_text(value: str, maximum: int, label: str) -> None:
        if not value or not value.strip():
            raise MemoryInputError(f"{label} is required.")
        if len(value) > maximum:
            raise MemoryResourceError(f"{label} exceeds configured limit.")

    @staticmethod
    def _now(now: datetime | None) -> datetime:
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            raise MemoryInputError("Timestamp must be timezone-aware.")
        return current
