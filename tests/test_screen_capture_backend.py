import os

import pytest

from omnisense_ai.screen_capture import CaptureBackendError, MssScreenCaptureBackend


def test_mss_backend_reports_missing_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    original_import = __import__

    def blocked_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "mss":
            raise ImportError("blocked for test")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", blocked_import)

    with pytest.raises(CaptureBackendError, match="mss is required"):
        MssScreenCaptureBackend()


@pytest.mark.skipif(
    os.environ.get("OMNISENSE_RUN_SCREEN_CAPTURE_INTEGRATION") != "1",
    reason="Real screen capture integration is opt-in.",
)
def test_mss_backend_can_capture_real_primary_monitor_when_enabled() -> None:
    backend = MssScreenCaptureBackend()
    try:
        monitors = list(backend.enumerate_monitors())
        assert monitors

        frame = backend.capture_monitor(monitors[0])

        assert frame.data
        assert frame.width == monitors[0].width
        assert frame.height == monitors[0].height
    finally:
        backend.close()
