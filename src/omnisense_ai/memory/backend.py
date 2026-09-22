"""Storage boundary for Phase 13 memory."""
from __future__ import annotations

from typing import Protocol
from datetime import datetime, timezone

from .models import MemoryEntry, MemoryKind, MemoryStatus


class MemoryBackend(Protocol):
    def put(self, entry: MemoryEntry) -> None: ...
    def delete(self, memory_id: str) -> None: ...
    def get(self, memory_id: str) -> MemoryEntry | None: ...
    def search(
        self,
        query: str,
        *,
        kind: MemoryKind | None = None,
        limit: int = 10,
        now: datetime | None = None,
    ) -> tuple[MemoryEntry, ...]: ...
    def list_active(self, *, now: datetime | None = None) -> tuple[MemoryEntry, ...]: ...
    def list_entries(self) -> tuple[MemoryEntry, ...]: ...
    def close(self) -> None: ...


class InMemoryMemoryBackend:
    """Deterministic bounded backend used by Phase 13 and tests."""

    def __init__(self) -> None:
        self._entries: dict[str, MemoryEntry] = {}
        self._closed = False

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("Memory backend is closed.")

    def put(self, entry: MemoryEntry) -> None:
        self._ensure_open()
        self._entries[entry.memory_id] = entry

    def delete(self, memory_id: str) -> None:
        self._ensure_open()
        self._entries.pop(memory_id, None)

    def get(self, memory_id: str) -> MemoryEntry | None:
        self._ensure_open()
        return self._entries.get(memory_id)

    def search(
        self,
        query: str,
        *,
        kind: MemoryKind | None = None,
        limit: int = 10,
        now: datetime | None = None,
    ) -> tuple[MemoryEntry, ...]:
        self._ensure_open()
        current = now or datetime.now(timezone.utc)
        needle = query.casefold()
        matches = []
        for entry in self._entries.values():
            if entry.is_expired(now=current):
                continue
            if entry.status is not MemoryStatus.ACTIVE:
                continue
            if kind is not None and entry.kind is not kind:
                continue
            haystack = f"{entry.key} {entry.value}".casefold()
            if needle in haystack:
                matches.append(entry)
        matches.sort(key=lambda item: item.updated_at, reverse=True)
        return tuple(matches[:limit])

    def list_entries(self) -> tuple[MemoryEntry, ...]:
        self._ensure_open()
        return tuple(self._entries.values())

    def list_active(self, *, now: datetime | None = None) -> tuple[MemoryEntry, ...]:
        self._ensure_open()
        current = now or datetime.now(timezone.utc)
        entries = tuple(
            entry
            for entry in self._entries.values()
            if entry.status is MemoryStatus.ACTIVE and not entry.is_expired(now=current)
        )
        return tuple(sorted(entries, key=lambda item: item.updated_at, reverse=True))

    def close(self) -> None:
        self._closed = True
