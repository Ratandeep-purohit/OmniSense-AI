"""Validated Phase 04 window and application detection contracts."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum


class WindowState(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MINIMIZED = "minimized"


@dataclass(frozen=True, slots=True)
class WindowRect:
    left: int
    top: int
    right: int
    bottom: int

    def __post_init__(self) -> None:
        if self.right <= self.left or self.bottom <= self.top:
            raise ValueError("Window rectangle must have positive width and height.")

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top


@dataclass(frozen=True, slots=True)
class WindowInfo:
    hwnd: int
    title: str
    process_id: int
    process_name: str | None
    executable_path: str | None
    rect: WindowRect
    monitor_id: str | None
    state: WindowState
    is_visible: bool
    is_foreground: bool

    def __post_init__(self) -> None:
        if self.hwnd <= 0:
            raise ValueError("Window handle must be positive.")
        if self.process_id < 0:
            raise ValueError("Process id must not be negative.")
        if len(self.title) > 4096:
            raise ValueError("Window title exceeds the supported limit.")
        for value, name in ((self.process_name, "process name"), (self.executable_path, "executable path"), (self.monitor_id, "monitor id")):
            if value is not None and len(value) > 4096:
                raise ValueError(f"{name} exceeds the supported limit.")


@dataclass(frozen=True, slots=True)
class WindowDetectionResult:
    window: WindowInfo | None
    detected_at: datetime
    backend: str

    def __post_init__(self) -> None:
        if self.detected_at.tzinfo is None:
            raise ValueError("Detection timestamp must be timezone-aware.")
        if not self.backend.strip():
            raise ValueError("Detection backend must not be empty.")

    @classmethod
    def empty(cls, backend: str) -> "WindowDetectionResult":
        return cls(window=None, detected_at=datetime.now(timezone.utc), backend=backend)
