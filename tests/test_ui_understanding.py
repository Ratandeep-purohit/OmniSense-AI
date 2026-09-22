from datetime import datetime, timezone

import pytest

from omnisense_ai.ocr.models import OCRBoundingBox, OCRLine, OCRQuality, OCRResult, OCRToken
from omnisense_ai.ui_understanding import UIBox, UIElementType, UIInputError, UIUnderstandingService
from omnisense_ai.visual_processing.models import FrameQuality, PixelFormat, QualityLevel, VisualFrame
from omnisense_ai.window_detection.models import WindowDetectionResult, WindowInfo, WindowRect, WindowState


def _frame(sequence: int = 1) -> VisualFrame:
    return VisualFrame(
        data=bytes([30, 30, 30]) * 4,
        width=2,
        height=2,
        pixel_format=PixelFormat.RGB24,
        source_monitor_id="1",
        quality=FrameQuality(30, 20, QualityLevel.GOOD, True),
        changed=True,
        change_score=1.0,
        sequence=sequence,
    )


def _ocr(sequence: int = 1, text: str = "Save") -> OCRResult:
    token = OCRToken(
        text=text,
        confidence=92,
        box=OCRBoundingBox(0, 0, 2, 1),
        block=1,
        paragraph=1,
        line=1,
        word=1,
    )
    line = OCRLine(text=text, tokens=(token,), box=token.box)
    return OCRResult(
        text=text,
        tokens=(token,),
        lines=(line,),
        quality=OCRQuality.GOOD,
        source_monitor_id="1",
        source_sequence=sequence,
        engine="fake",
        language="eng",
    )


def _window() -> WindowDetectionResult:
    return WindowDetectionResult(
        window=WindowInfo(
            hwnd=100,
            title="Demo",
            process_id=200,
            process_name="demo.exe",
            executable_path=None,
            rect=WindowRect(0, 0, 2, 2),
            monitor_id="1",
            state=WindowState.ACTIVE,
            is_visible=True,
            is_foreground=True,
        ),
        detected_at=datetime.now(timezone.utc),
        backend="fake",
    )


def test_ui_understanding_builds_elements_and_provenance():
    result = UIUnderstandingService().understand(_frame(), _ocr(), _window())
    assert len(result.elements) == 1
    assert result.elements[0].element_type is UIElementType.BUTTON
    assert result.elements[0].source == ("ocr", "geometry", "heuristic")
    assert result.window_id == 100
    assert result.source_types == ("visual_frame", "ocr", "window")


def test_mismatched_ocr_sequence_is_rejected():
    with pytest.raises(UIInputError):
        UIUnderstandingService().understand(_frame(2), _ocr(1), _window())


def test_mismatched_monitor_is_rejected():
    ocr = _ocr()
    bad = OCRResult(
        text=ocr.text,
        tokens=ocr.tokens,
        lines=ocr.lines,
        quality=ocr.quality,
        source_monitor_id="2",
        source_sequence=ocr.source_sequence,
        engine=ocr.engine,
        language=ocr.language,
    )
    with pytest.raises(UIInputError):
        UIUnderstandingService().understand(_frame(), bad, _window())


def test_ui_box_geometry():
    box = UIBox(10, 20, 30, 40)
    assert box.right == 40
    assert box.bottom == 60
    assert box.area == 1200
    assert box.iou(UIBox(20, 30, 30, 40)) > 0


def test_ui_box_rejects_invalid_geometry():
    with pytest.raises(ValueError):
        UIBox(0, 0, 0, 10)
