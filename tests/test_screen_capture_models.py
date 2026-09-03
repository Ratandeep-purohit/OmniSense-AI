from datetime import datetime, timezone

import pytest

from omnisense_ai.screen_capture import (
    CaptureRegion,
    FrameSource,
    InvalidCaptureRegionError,
    MonitorInfo,
    ScreenFrame,
)


def test_monitor_reports_contained_region() -> None:
    monitor = MonitorInfo(id="1", x=-100, y=0, width=500, height=400, is_primary=True)

    assert monitor.contains_region(CaptureRegion(-50, 10, 100, 100)) is True
    assert monitor.contains_region(CaptureRegion(-150, 10, 100, 100)) is False


def test_capture_region_rejects_empty_dimensions() -> None:
    with pytest.raises(InvalidCaptureRegionError, match="positive"):
        CaptureRegion(0, 0, 0, 100)


def test_screen_frame_requires_non_empty_data() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        ScreenFrame(
            data=b"",
            width=1,
            height=1,
            pixel_format="BGRA",
            monitor_id="1",
            source=FrameSource.MONITOR,
            captured_at=datetime.now(timezone.utc),
        )


def test_screen_frame_region_dimensions_must_match() -> None:
    with pytest.raises(ValueError, match="dimensions"):
        ScreenFrame(
            data=b"abcd",
            width=2,
            height=2,
            pixel_format="BGRA",
            monitor_id="1",
            source=FrameSource.REGION,
            region=CaptureRegion(0, 0, 1, 1),
        )
