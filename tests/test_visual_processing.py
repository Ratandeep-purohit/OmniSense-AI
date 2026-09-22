from datetime import datetime, timezone

import pytest

from omnisense_ai.screen_capture.models import FrameSource, ScreenFrame
from omnisense_ai.visual_processing import (
    InvalidFrameError,
    PixelFormat,
    ProcessingConfig,
    QualityLevel,
    UnsupportedPixelFormatError,
    VisualProcessor,
)


def frame(width=4, height=2, pixel_format="BGRA", data=None):
    if data is None:
        data = bytes([10, 20, 30, 255]) * (width * height)
    return ScreenFrame(
        data=data,
        width=width,
        height=height,
        pixel_format=pixel_format,
        monitor_id="1",
        source=FrameSource.MONITOR,
        captured_at=datetime.now(timezone.utc),
    )


def test_bgra_is_converted_to_rgb_and_resized() -> None:
    result = VisualProcessor(ProcessingConfig(target_width=2, target_height=1)).process(frame())

    assert result.pixel_format is PixelFormat.RGB24
    assert (result.width, result.height) == (2, 1)
    assert result.data == bytes([30, 20, 10]) * 2
    assert result.changed is True
    assert result.sequence == 1


def test_quality_and_change_detection_are_deterministic() -> None:
    processor = VisualProcessor(ProcessingConfig(target_width=4, target_height=2))
    first = processor.process(frame())
    second = processor.process(frame())

    assert first.quality.level is QualityLevel.LOW
    assert first.change_score == 1.0
    assert second.change_score == 0.0
    assert second.changed is False
    assert second.sequence == 2


def test_changed_frame_gets_nonzero_change_score() -> None:
    processor = VisualProcessor(ProcessingConfig(target_width=4, target_height=2))
    processor.process(frame())
    changed = bytes([200, 200, 200, 255]) * 8
    result = processor.process(frame(data=changed))

    assert result.change_score > 0
    assert result.changed is True


def test_invalid_pixel_format_is_rejected() -> None:
    with pytest.raises(UnsupportedPixelFormatError):
        VisualProcessor().process(frame(pixel_format="RGB24"))


def test_invalid_byte_length_is_rejected() -> None:
    class MalformedFrame:
        data = b"bad"
        width = 4
        height = 2
        pixel_format = "BGRA"
        monitor_id = "1"

    with pytest.raises(InvalidFrameError):
        VisualProcessor().process(MalformedFrame())


def test_reset_starts_new_sequence() -> None:
    processor = VisualProcessor(ProcessingConfig(target_width=4, target_height=2))
    processor.process(frame())
    processor.reset()
    result = processor.process(frame())

    assert result.sequence == 1
    assert result.changed is True
    assert result.change_score == 1.0
