from collections.abc import Sequence

import pytest

from omnisense_ai.config import CaptureConfig
from omnisense_ai.screen_capture import (
    CaptureBackendError,
    CaptureNotActiveError,
    CapturePermissionError,
    CaptureRegion,
    CaptureState,
    FrameSource,
    InvalidCaptureRegionError,
    MonitorInfo,
    MonitorNotFoundError,
    ScreenCaptureService,
    ScreenFrame,
)


class FakeBackend:
    def __init__(self, monitors: Sequence[MonitorInfo] | None = None, *, should_fail: bool = False) -> None:
        self.monitors = list(monitors or [MonitorInfo(id="1", x=0, y=0, width=100, height=80, is_primary=True)])
        self.should_fail = should_fail
        self.is_closed = False
        self.captured_regions: list[CaptureRegion] = []

    def enumerate_monitors(self) -> Sequence[MonitorInfo]:
        return self.monitors

    def capture_monitor(self, monitor: MonitorInfo) -> ScreenFrame:
        return self.capture_region(monitor, monitor.region)

    def capture_region(self, monitor: MonitorInfo, region: CaptureRegion) -> ScreenFrame:
        if self.should_fail:
            raise CaptureBackendError("backend failed")
        self.captured_regions.append(region)
        return ScreenFrame(
            data=b"x" * (region.width * region.height * 4),
            width=region.width,
            height=region.height,
            pixel_format="BGRA",
            monitor_id=monitor.id,
            source=FrameSource.REGION if region != monitor.region else FrameSource.MONITOR,
            region=region,
        )

    def close(self) -> None:
        self.is_closed = True


def enabled_config(**overrides: object) -> CaptureConfig:
    values = {
        "is_enabled": True,
        "monitor_id": "primary",
        "interval_ms": 1000,
        "max_fps": 1.0,
        "region": None,
    }
    values.update(overrides)
    return CaptureConfig(**values)


def test_monitor_enumeration_uses_backend_without_starting_capture() -> None:
    backend = FakeBackend()
    service = ScreenCaptureService(backend, enabled_config())

    monitors = service.enumerate_monitors()

    assert len(monitors) == 1
    assert service.state is CaptureState.STOPPED


def test_capture_requires_enabled_configuration() -> None:
    service = ScreenCaptureService(
        FakeBackend(),
        CaptureConfig(False, "primary", 1000, 1.0, None),
    )

    with pytest.raises(CapturePermissionError):
        service.start()


def test_capture_selected_monitor_after_start() -> None:
    service = ScreenCaptureService(FakeBackend(), enabled_config())

    service.start()
    frame = service.capture_selected_monitor()

    assert frame.monitor_id == "1"
    assert frame.source is FrameSource.MONITOR
    assert frame.width == 100
    assert frame.height == 80


def test_explicit_monitor_selection() -> None:
    monitors = [
        MonitorInfo(id="1", x=0, y=0, width=100, height=80, is_primary=True),
        MonitorInfo(id="2", x=100, y=0, width=200, height=120),
    ]
    service = ScreenCaptureService(FakeBackend(monitors), enabled_config(monitor_id="2"))

    service.start()
    frame = service.capture_selected_monitor()

    assert frame.monitor_id == "2"
    assert frame.width == 200


def test_region_capture_validates_bounds() -> None:
    service = ScreenCaptureService(FakeBackend(), enabled_config())

    service.start()
    frame = service.capture_region(CaptureRegion(10, 10, 20, 20))

    assert frame.source is FrameSource.REGION
    assert frame.width == 20
    assert frame.height == 20


def test_configured_region_is_used_when_present() -> None:
    backend = FakeBackend()
    service = ScreenCaptureService(backend, enabled_config(region=(1, 2, 30, 40)))

    service.start()
    frame = service.capture_configured_region_or_monitor()

    assert frame.region == CaptureRegion(1, 2, 30, 40)
    assert backend.captured_regions == [CaptureRegion(1, 2, 30, 40)]


def test_invalid_monitor_selection_fails_safely() -> None:
    service = ScreenCaptureService(FakeBackend(), enabled_config(monitor_id="missing"))

    service.start()
    with pytest.raises(MonitorNotFoundError):
        service.capture_selected_monitor()


def test_invalid_region_fails_before_backend_capture() -> None:
    backend = FakeBackend()
    service = ScreenCaptureService(backend, enabled_config())

    service.start()
    with pytest.raises(InvalidCaptureRegionError):
        service.capture_region(CaptureRegion(90, 70, 20, 20))

    assert backend.captured_regions == []


def test_capture_failure_is_reported_as_controlled_error() -> None:
    service = ScreenCaptureService(FakeBackend(should_fail=True), enabled_config())

    service.start()
    with pytest.raises(CaptureBackendError):
        service.capture_selected_monitor()


def test_state_transitions_pause_resume_stop_start_and_cleanup() -> None:
    backend = FakeBackend()
    service = ScreenCaptureService(backend, enabled_config())

    service.start()
    assert service.state is CaptureState.RUNNING

    service.pause()
    assert service.state is CaptureState.PAUSED

    with pytest.raises(CaptureNotActiveError):
        service.capture_selected_monitor()

    service.resume()
    assert service.state is CaptureState.RUNNING

    service.stop()
    assert service.state is CaptureState.STOPPED
    assert backend.is_closed is True

    with pytest.raises(CaptureNotActiveError):
        service.capture_selected_monitor()
