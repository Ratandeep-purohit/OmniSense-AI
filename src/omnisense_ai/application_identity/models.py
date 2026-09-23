"""Canonical Windows identity contracts.

PID alone is not an identity because Windows can reuse a PID after a process
exits. Runtime identity therefore includes PID, executable path and creation
time. Window identity additionally binds an HWND to that process instance.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class IdentitySource(StrEnum):
    START_MENU = "start_menu"
    APP_PATHS = "app_paths"
    AUMID = "aumid"
    RUNTIME = "runtime"


@dataclass(frozen=True, slots=True)
class ApplicationIdentity:
    application_id: str
    display_name: str
    launch_target: str
    source: IdentitySource | str
    process_names: tuple[str, ...] = ()
    executable_path: str | None = None
    aumid: str | None = None
    adapter_id: str = "generic.windows"
    aliases: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for value, name in (
            (self.application_id, "application_id"),
            (self.display_name, "display_name"),
            (self.launch_target, "launch_target"),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required.")
        if len(self.process_names) > 32 or len(self.aliases) > 64:
            raise ValueError("Application identity contains too many aliases.")

    def matches_process(self, process_name: str | None) -> bool:
        if not process_name:
            return False
        return process_name.casefold() in {p.casefold() for p in self.process_names}


@dataclass(frozen=True, slots=True)
class ProcessIdentity:
    pid: int
    executable_path: str
    process_name: str
    creation_time_ns: int
    session_id: int | None = None

    def __post_init__(self) -> None:
        if self.pid <= 0:
            raise ValueError("Process id must be positive.")
        if not self.executable_path.strip() or not self.process_name.strip():
            raise ValueError("Process executable identity is required.")
        if self.creation_time_ns <= 0:
            raise ValueError("Process creation time must be positive.")
        if self.session_id is not None and self.session_id < 0:
            raise ValueError("Process session id must not be negative.")

    @property
    def normalized_executable_path(self) -> str:
        return self.executable_path.replace("/", "\").casefold()

    def same_instance(self, other: "ProcessIdentity") -> bool:
        return (
            self.pid == other.pid
            and self.creation_time_ns == other.creation_time_ns
            and self.normalized_executable_path == other.normalized_executable_path
        )


@dataclass(frozen=True, slots=True)
class WindowIdentity:
    hwnd: int
    process: ProcessIdentity
    title: str
    class_name: str | None = None
    is_visible: bool = True

    def __post_init__(self) -> None:
        if self.hwnd <= 0:
            raise ValueError("Window handle must be positive.")
        if len(self.title) > 4096:
            raise ValueError("Window title exceeds the supported limit.")
        if self.class_name is not None and len(self.class_name) > 1024:
            raise ValueError("Window class name exceeds the supported limit.")

    def same_window(self, other: "WindowIdentity") -> bool:
        return self.hwnd == other.hwnd and self.process.same_instance(other.process)

    def same_process(self, process: ProcessIdentity) -> bool:
        return self.process.same_instance(process)
