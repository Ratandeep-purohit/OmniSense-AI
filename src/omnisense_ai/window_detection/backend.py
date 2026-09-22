"""Windows-native adapter for active window and process metadata."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from typing import Protocol

from .errors import WindowDetectionBackendError, WindowDetectionUnavailableError
from .models import WindowInfo, WindowRect, WindowState


class WindowDetectionBackend(Protocol):
    name: str

    def detect_active_window(self) -> WindowInfo | None:
        ...


class WindowsWindowDetectionBackend:
    """Read-only Windows API adapter.

    This adapter only observes foreground-window metadata. It does not focus,
    move, resize, close, or otherwise control a window.
    """

    name = "windows-user32"

    _PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    _MONITOR_DEFAULTTONEAREST = 2

    def __init__(self) -> None:
        if os.name != "nt":
            raise WindowDetectionUnavailableError("Phase 04 Windows backend requires Windows.")

        self._user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._configure_api()

    def _configure_api(self) -> None:
        self._user32.GetForegroundWindow.restype = wintypes.HWND
        self._user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        self._user32.GetWindowTextLengthW.restype = ctypes.c_int
        self._user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        self._user32.GetWindowTextW.restype = ctypes.c_int
        self._user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
        self._user32.GetWindowRect.restype = wintypes.BOOL
        self._user32.IsWindowVisible.argtypes = [wintypes.HWND]
        self._user32.IsWindowVisible.restype = wintypes.BOOL
        self._user32.IsIconic.argtypes = [wintypes.HWND]
        self._user32.IsIconic.restype = wintypes.BOOL
        self._user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        self._user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        self._user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
        self._user32.MonitorFromWindow.restype = wintypes.HANDLE
        self._user32.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
        self._user32.GetMonitorInfoW.restype = wintypes.BOOL
        self._kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self._kernel32.OpenProcess.restype = wintypes.HANDLE
        self._kernel32.QueryFullProcessImageNameW.argtypes = [
            wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)
        ]
        self._kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
        self._kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self._kernel32.CloseHandle.restype = wintypes.BOOL

    def detect_active_window(self) -> WindowInfo | None:
        hwnd = int(self._user32.GetForegroundWindow())
        if hwnd == 0:
            return None

        title = self._read_title(hwnd)
        rect = self._read_rect(hwnd)
        process_id = self._read_process_id(hwnd)
        process_name, executable_path = self._read_process_metadata(process_id)
        monitor_id = self._read_monitor_id(hwnd)
        minimized = bool(self._user32.IsIconic(hwnd))
        visible = bool(self._user32.IsWindowVisible(hwnd))

        return WindowInfo(
            hwnd=hwnd,
            title=title,
            process_id=process_id,
            process_name=process_name,
            executable_path=executable_path,
            rect=rect,
            monitor_id=monitor_id,
            state=WindowState.MINIMIZED if minimized else WindowState.ACTIVE,
            is_visible=visible,
            is_foreground=True,
        )

    def _read_title(self, hwnd: int) -> str:
        length = int(self._user32.GetWindowTextLengthW(hwnd))
        if length <= 0:
            return ""
        buffer = ctypes.create_unicode_buffer(min(length + 1, 4097))
        self._user32.GetWindowTextW(hwnd, buffer, len(buffer))
        return buffer.value[:4096]

    def _read_rect(self, hwnd: int) -> WindowRect:
        rect = wintypes.RECT()
        if not self._user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            raise WindowDetectionBackendError("Windows could not provide the active window rectangle.")
        return WindowRect(rect.left, rect.top, rect.right, rect.bottom)

    def _read_process_id(self, hwnd: int) -> int:
        process_id = wintypes.DWORD()
        if self._user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id)) == 0:
            raise WindowDetectionBackendError("Windows could not provide the active window process id.")
        return int(process_id.value)

    def _read_process_metadata(self, process_id: int) -> tuple[str | None, str | None]:
        if process_id <= 0:
            return None, None
        handle = self._kernel32.OpenProcess(self._PROCESS_QUERY_LIMITED_INFORMATION, False, process_id)
        if not handle:
            return None, None
        try:
            size = wintypes.DWORD(4096)
            buffer = ctypes.create_unicode_buffer(size.value)
            if not self._kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
                return None, None
            path = buffer.value[: size.value]
            name = path.replace("\\", "/").rsplit("/", 1)[-1] or None
            return name, path
        finally:
            self._kernel32.CloseHandle(handle)

    def _read_monitor_id(self, hwnd: int) -> str | None:
        monitor = self._user32.MonitorFromWindow(hwnd, self._MONITOR_DEFAULTTONEAREST)
        if not monitor:
            return None
        return str(int(ctypes.cast(monitor, ctypes.c_void_p).value or 0))
