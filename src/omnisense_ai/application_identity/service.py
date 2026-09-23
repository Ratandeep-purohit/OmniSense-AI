"""Windows-native runtime identity service.

This module is read-only. It does not start, stop, focus, inject into, or
otherwise control a process/window. It establishes identities that later
execution and verification layers can safely compare.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from pathlib import Path

from ..application_discovery import ApplicationCandidate, WindowsApplicationResolver
from .models import ApplicationIdentity, ProcessIdentity, WindowIdentity


class ApplicationIdentityError(RuntimeError):
    """Raised when Windows cannot establish a trustworthy runtime identity."""


class ApplicationIdentityService:
    """Resolve logical applications and capture immutable runtime identities."""

    _PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

    def __init__(self, resolver: WindowsApplicationResolver | None = None) -> None:
        self.resolver = resolver or WindowsApplicationResolver()
        self._user32 = None
        self._kernel32 = None
        if os.name == "nt":
            self._configure_windows_api()

    def resolve(self, query: str) -> ApplicationIdentity | None:
        candidate = self.resolver.resolve(query)
        return self.from_candidate(candidate) if candidate else None

    @staticmethod
    def from_candidate(candidate: ApplicationCandidate) -> ApplicationIdentity:
        processes = (candidate.process_name,) if candidate.process_name else ()
        name = candidate.display_name.casefold()
        adapter = "generic.windows"
        if "epic games" in name or "epicgameslauncher.exe" in " ".join(processes).casefold():
            adapter = "epic.games.launcher"
        elif name in {"microsoft word", "microsoft excel", "microsoft powerpoint"}:
            adapter = "microsoft.office"

        executable = (
            candidate.launch_target
            if candidate.launch_target.casefold().endswith(".exe")
            else None
        )
        aumid = candidate.launch_target if candidate.source == "aumid" else None
        return ApplicationIdentity(
            application_id=candidate.application_id,
            display_name=candidate.display_name,
            launch_target=candidate.launch_target,
            source=candidate.source,
            process_names=processes,
            executable_path=executable,
            aumid=aumid,
            adapter_id=adapter,
            aliases=(candidate.display_name,),
        )

    def identify_process(self, pid: int) -> ProcessIdentity:
        """Read the exact executable and creation time for a live process."""

        self._require_windows()
        if pid <= 0:
            raise ValueError("Process id must be positive.")

        handle = self._kernel32.OpenProcess(
            self._PROCESS_QUERY_LIMITED_INFORMATION,
            False,
            pid,
        )
        if not handle:
            raise ApplicationIdentityError(
                f"Windows denied identity access for process {pid}."
            )

        try:
            path = self._query_process_path(handle)
            creation_time = self._query_creation_time_ns(handle)
            session_id = self._query_session_id(pid)
        finally:
            self._kernel32.CloseHandle(handle)

        executable = Path(path).name
        if not executable:
            raise ApplicationIdentityError("Windows returned an empty process name.")

        return ProcessIdentity(
            pid=pid,
            executable_path=path,
            process_name=executable,
            creation_time_ns=creation_time,
            session_id=session_id,
        )

    def identify_window(self, hwnd: int) -> WindowIdentity:
        """Bind a top-level window handle to its current process instance."""

        self._require_windows()
        if hwnd <= 0:
            raise ValueError("Window handle must be positive.")
        if not self._user32.IsWindow(hwnd):
            raise ApplicationIdentityError("The supplied HWND is no longer valid.")

        process_id = wintypes.DWORD()
        if self._user32.GetWindowThreadProcessId(
            wintypes.HWND(hwnd), ctypes.byref(process_id)
        ) == 0:
            raise ApplicationIdentityError("Windows could not resolve the window process.")

        process = self.identify_process(int(process_id.value))
        return WindowIdentity(
            hwnd=hwnd,
            process=process,
            title=self._read_window_title(hwnd),
            class_name=self._read_class_name(hwnd),
            is_visible=bool(self._user32.IsWindowVisible(hwnd)),
        )

    def identify_foreground_window(self) -> WindowIdentity:
        """Read the identity of the current foreground window without changing focus."""

        self._require_windows()
        hwnd = int(self._user32.GetForegroundWindow())
        if hwnd <= 0:
            raise ApplicationIdentityError("Windows has no foreground window.")
        return self.identify_window(hwnd)

    def same_process(self, expected: ProcessIdentity, pid: int) -> bool:
        """Return False rather than throwing when the process has exited/reused its PID."""

        try:
            current = self.identify_process(pid)
        except (ApplicationIdentityError, OSError):
            return False
        return expected.same_instance(current)

    def same_window(self, expected: WindowIdentity, hwnd: int) -> bool:
        """Compare HWND and process-instance identity, preventing PID-reuse matches."""

        try:
            current = self.identify_window(hwnd)
        except (ApplicationIdentityError, OSError):
            return False
        return expected.same_window(current)

    def _configure_windows_api(self) -> None:
        self._user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        self._user32.GetForegroundWindow.argtypes = []
        self._user32.GetForegroundWindow.restype = wintypes.HWND
        self._user32.IsWindow.argtypes = [wintypes.HWND]
        self._user32.IsWindow.restype = wintypes.BOOL
        self._user32.IsWindowVisible.argtypes = [wintypes.HWND]
        self._user32.IsWindowVisible.restype = wintypes.BOOL
        self._user32.GetWindowThreadProcessId.argtypes = [
            wintypes.HWND, ctypes.POINTER(wintypes.DWORD)
        ]
        self._user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        self._user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        self._user32.GetWindowTextLengthW.restype = ctypes.c_int
        self._user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        self._user32.GetWindowTextW.restype = ctypes.c_int
        self._user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        self._user32.GetClassNameW.restype = ctypes.c_int

        self._kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self._kernel32.OpenProcess.restype = wintypes.HANDLE
        self._kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self._kernel32.CloseHandle.restype = wintypes.BOOL
        self._kernel32.QueryFullProcessImageNameW.argtypes = [
            wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)
        ]
        self._kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
        self._kernel32.GetProcessTimes.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
        ]
        self._kernel32.GetProcessTimes.restype = wintypes.BOOL
        self._kernel32.ProcessIdToSessionId.argtypes = [
            wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)
        ]
        self._kernel32.ProcessIdToSessionId.restype = wintypes.BOOL

    def _require_windows(self) -> None:
        if os.name != "nt" or self._user32 is None or self._kernel32 is None:
            raise ApplicationIdentityError("Windows identity APIs require Windows.")

    def _query_process_path(self, handle) -> str:
        size = wintypes.DWORD(32768)
        buffer = ctypes.create_unicode_buffer(size.value)
        if not self._kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            raise ApplicationIdentityError("Windows could not read the process executable path.")
        path = buffer.value[: size.value].strip()
        if not path:
            raise ApplicationIdentityError("Windows returned an empty executable path.")
        return path

    def _query_creation_time_ns(self, handle) -> int:
        creation = wintypes.FILETIME()
        exit_time = wintypes.FILETIME()
        kernel = wintypes.FILETIME()
        user = wintypes.FILETIME()
        if not self._kernel32.GetProcessTimes(
            handle, ctypes.byref(creation), ctypes.byref(exit_time), ctypes.byref(kernel), ctypes.byref(user)
        ):
            raise ApplicationIdentityError("Windows could not read process creation time.")
        return (creation.dwHighDateTime << 32) | creation.dwLowDateTime

    def _query_session_id(self, pid: int) -> int | None:
        session = wintypes.DWORD()
        if not self._kernel32.ProcessIdToSessionId(pid, ctypes.byref(session)):
            return None
        return int(session.value)

    def _read_window_title(self, hwnd: int) -> str:
        length = int(self._user32.GetWindowTextLengthW(hwnd))
        if length <= 0:
            return ""
        buffer = ctypes.create_unicode_buffer(min(length + 1, 4097))
        self._user32.GetWindowTextW(hwnd, buffer, len(buffer))
        return buffer.value[:4096]

    def _read_class_name(self, hwnd: int) -> str | None:
        buffer = ctypes.create_unicode_buffer(1025)
        length = int(self._user32.GetClassNameW(hwnd, buffer, len(buffer)))
        return buffer.value[:1024] if length else None
