from datetime import datetime, timezone

import pytest

from omnisense_ai.window_detection import (
    WindowDetectionBackendError,
    WindowDetectionResult,
    WindowDetectionService,
    WindowInfo,
    WindowRect,
    WindowState,
)


class FakeBackend:
    name = "fake"

    def __init__(self, window=None, error=None):
        self.window = window
        self.error = error

    def detect_active_window(self):
        if self.error:
            raise self.error
        return self.window


def make_window(**overrides):
    values = {
        "hwnd": 101,
        "title": "Visual Studio Code",
        "process_id": 9001,
        "process_name": "Code.exe",
        "executable_path": r"C:\Program Files\Microsoft VS Code\Code.exe",
        "rect": WindowRect(10, 20, 1010, 820),
        "monitor_id": "monitor-1",
        "state": WindowState.ACTIVE,
        "is_visible": True,
        "is_foreground": True,
    }
    values.update(overrides)
    return WindowInfo(**values)


def test_window_rect_dimensions_are_derived():
    rect = WindowRect(10, 20, 1010, 820)
    assert rect.width == 1000
    assert rect.height == 800


def test_window_info_contract():
    window = make_window()
    assert window.hwnd == 101
    assert window.process_id == 9001
    assert window.rect.width == 1000
    assert window.state is WindowState.ACTIVE


def test_service_returns_active_window_snapshot():
    window = make_window()
    result = WindowDetectionService(FakeBackend(window)).detect_active_window()
    assert result.window == window
    assert result.backend == "fake"
    assert result.detected_at.tzinfo is not None


def test_service_allows_no_foreground_window():
    result = WindowDetectionService(FakeBackend(None)).detect_active_window()
    assert result.window is None
    assert result.detected_at.tzinfo is not None


def test_service_maps_backend_failure():
    result = WindowDetectionService(FakeBackend(error=RuntimeError("boom")))
    with pytest.raises(WindowDetectionBackendError):
        result.detect_active_window()


def test_service_rejects_after_close():
    service = WindowDetectionService(FakeBackend(make_window()))
    service.close()
    with pytest.raises(WindowDetectionBackendError):
        service.detect_active_window()


def test_window_contract_rejects_invalid_rect():
    with pytest.raises(ValueError):
        WindowRect(10, 20, 10, 100)

    with pytest.raises(ValueError):
        WindowRect(10, 20, 100, 20)


def test_window_detection_result_requires_timezone_aware_timestamp():
    with pytest.raises(ValueError):
        WindowDetectionResult(
            window=None,
            detected_at=datetime(2026, 1, 1),
            backend="fake",
        )
