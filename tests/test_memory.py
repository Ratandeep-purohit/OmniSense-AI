from datetime import datetime, timedelta, timezone

import pytest

from omnisense_ai.memory import (
    MemoryConfig,
    MemoryDisabledError,
    MemoryEntry,
    MemoryKind,
    MemoryNotFoundError,
    MemoryResourceError,
    MemorySecurityError,
    MemorySensitivity,
    MemoryService,
)


NOW = datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc)


def service(**kwargs):
    return MemoryService(MemoryConfig(enabled=True, **kwargs))


def test_memory_disabled_by_default():
    with pytest.raises(MemoryDisabledError):
        MemoryService().remember(kind=MemoryKind.PREFERENCE, key="theme", value="dark")


def test_remember_and_recall():
    memory = service()
    entry = memory.remember(kind=MemoryKind.PREFERENCE, key="theme", value="dark", now=NOW)
    result = memory.recall("theme", now=NOW)
    assert result.entries[0] == entry


def test_update_same_kind_and_key():
    memory = service()
    first = memory.remember(kind=MemoryKind.PREFERENCE, key="theme", value="dark", now=NOW)
    second = memory.remember(kind=MemoryKind.PREFERENCE, key="theme", value="light", now=NOW + timedelta(seconds=1))
    assert second.memory_id == first.memory_id
    assert second.value == "light"


def test_kind_filters_results():
    memory = service()
    memory.remember(kind=MemoryKind.PREFERENCE, key="language", value="Hinglish", now=NOW)
    memory.remember(kind=MemoryKind.FACT, key="language", value="Python", now=NOW)
    result = memory.recall("language", kind=MemoryKind.PREFERENCE, now=NOW)
    assert len(result.entries) == 1
    assert result.entries[0].value == "Hinglish"


def test_result_limit_is_bounded():
    memory = service(max_results=2)
    with pytest.raises(Exception):
        memory.recall("x", limit=3, now=NOW)


def test_sensitive_memory_is_denied_by_default():
    memory = service()
    with pytest.raises(MemorySecurityError):
        memory.remember(
            kind=MemoryKind.FACT,
            key="secret",
            value="hidden",
            sensitivity=MemorySensitivity.SENSITIVE,
            now=NOW,
        )


def test_sensitive_memory_can_be_explicitly_enabled():
    memory = service(allow_sensitive=True)
    entry = memory.remember(
        kind=MemoryKind.FACT,
        key="secret",
        value="hidden",
        sensitivity=MemorySensitivity.SENSITIVE,
        now=NOW,
    )
    assert entry.sensitivity is MemorySensitivity.SENSITIVE


def test_retention_expiry_removes_entry():
    memory = service(retention_seconds=10)
    memory.remember(kind=MemoryKind.FACT, key="temporary", value="value", now=NOW)
    assert memory.recall("temporary", now=NOW + timedelta(seconds=11)).entries == ()


def test_max_entries_is_enforced():
    memory = service(max_entries=1)
    memory.remember(kind=MemoryKind.FACT, key="a", value="1", now=NOW)
    with pytest.raises(MemoryResourceError):
        memory.remember(kind=MemoryKind.FACT, key="b", value="2", now=NOW)


def test_forget_deletes_entry():
    memory = service()
    entry = memory.remember(kind=MemoryKind.FACT, key="a", value="1", now=NOW)
    memory.forget(entry.memory_id)
    assert memory.recall("a", now=NOW).entries == ()


def test_forget_unknown_entry_fails():
    memory = service()
    with pytest.raises(MemoryNotFoundError):
        memory.forget("mem-missing")


def test_clear_removes_all_entries():
    memory = service()
    memory.remember(kind=MemoryKind.FACT, key="a", value="1", now=NOW)
    memory.remember(kind=MemoryKind.FACT, key="b", value="2", now=NOW)
    memory.clear()
    assert memory.recall("a", now=NOW).entries == ()
    assert memory.recall("b", now=NOW).entries == ()


def test_provenance_is_preserved():
    memory = service()
    entry = memory.remember(
        kind=MemoryKind.FACT,
        key="editor",
        value="VS Code",
        source="user",
        provenance=("user_message",),
        now=NOW,
    )
    assert entry.provenance == ("user_message",)


def test_closed_service_rejects_operations():
    memory = service()
    memory.close()
    with pytest.raises(MemoryDisabledError):
        memory.recall("x", now=NOW)


def test_expired_memory_does_not_count_toward_limit():
    memory = service(max_entries=1, retention_seconds=1)
    memory.remember(kind=MemoryKind.FACT, key="old", value="1", now=NOW)
    memory.remember(kind=MemoryKind.FACT, key="new", value="2", now=NOW + timedelta(seconds=2))
    assert memory.recall("new", now=NOW + timedelta(seconds=2)).entries[0].key == "new"
