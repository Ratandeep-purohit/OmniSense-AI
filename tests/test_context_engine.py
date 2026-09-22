from datetime import datetime, timezone

import pytest

from omnisense_ai.context_engine import (
    ContextConfig,
    ContextEngine,
    ContextFreshness,
    ContextInputError,
    ContextSource,
    Sensitivity,
)
from omnisense_ai.ocr.models import OCRBoundingBox, OCRLine, OCRQuality, OCRResult, OCRToken
from omnisense_ai.ui_understanding.models import UIUnderstandingResult
from omnisense_ai.visual_processing.models import FrameQuality, PixelFormat, QualityLevel, VisualFrame
from omnisense_ai.window_detection.models import WindowDetectionResult, WindowInfo, WindowRect, WindowState


def frame(sequence=1):
    return VisualFrame(
        bytes([30, 30, 30]) * 4, 2, 2, PixelFormat.RGB24, "1",
        FrameQuality(30, 20, QualityLevel.GOOD, True), True, 1.0, sequence
    )


def ocr(sequence=1, text="Save"):
    token = OCRToken(text, 92, OCRBoundingBox(0, 0, 2, 1), 1, 1, 1, 1)
    line = OCRLine(text, (token,), token.box)
    return OCRResult(text, (token,), (line,), OCRQuality.GOOD, "1", sequence, "fake", "eng")


def ui(sequence=1):
    return UIUnderstandingResult((), (), None, "1", sequence, ("visual_frame", "ocr", "window"))


def window():
    return WindowDetectionResult(
        WindowInfo(100, "Private Document", 200, "editor.exe", None, WindowRect(0, 0, 2, 2),
                   "1", WindowState.ACTIVE, True, True),
        datetime.now(timezone.utc), "fake"
    )


def test_context_fuses_current_observations():
    result = ContextEngine().build(frame(), ocr(), window(), ui())
    assert result.context.frame_sequence == 1
    assert result.context.monitor_id == "1"
    assert result.context.visible_text == "Save"
    assert result.context.freshness is ContextFreshness.FRESH
    assert any(f.key == "desktop.visible_text_available" for f in result.context.facts)


def test_window_facts_are_observed_and_sensitive_where_appropriate():
    result = ContextEngine().build(frame(), ocr(), window(), ui())
    title = next(f for f in result.context.facts if f.key == "window.title")
    assert title.source is ContextSource.OBSERVED
    assert title.sensitivity is Sensitivity.SENSITIVE


def test_sequence_mismatch_is_rejected():
    with pytest.raises(ContextInputError):
        ContextEngine().build(frame(2), ocr(1), window(), ui(2))


def test_ui_monitor_mismatch_is_rejected():
    bad_ui = UIUnderstandingResult((), (), None, "2", 1, ("visual_frame", "ocr", "window"))
    with pytest.raises(ContextInputError):
        ContextEngine().build(frame(), ocr(), window(), bad_ui)


def test_user_context_is_not_authorization():
    result = ContextEngine().build(
        frame(), ocr(), window(), ui(),
        user_context="please help me understand this",
    )
    assert result.user_context == "please help me understand this"
    assert result.authorization is None


def test_user_context_bound_is_enforced():
    with pytest.raises(Exception):
        ContextEngine(ContextConfig(max_user_context_length=4)).build(
            frame(), ocr(), window(), ui(), user_context="too long"
        )


def test_long_visible_text_is_bounded():
    result = ContextEngine(ContextConfig(max_visible_text_length=4)).build(
        frame(), ocr(text="Save this document"), window(), ui()
    )
    assert result.context.visible_text == "Save"
    assert result.context.truncated is True
