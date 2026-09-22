from omnisense_ai.ocr import OCRConfig, OCRInputError, OCRQuality, OCRService, RawOCRToken
from omnisense_ai.visual_processing.models import FrameQuality, PixelFormat, QualityLevel, VisualFrame


def frame() -> VisualFrame:
    quality = FrameQuality(brightness=120, contrast=40, level=QualityLevel.GOOD, usable=True)
    return VisualFrame(
        data=bytes([40, 50, 60] * 4),
        width=2,
        height=2,
        pixel_format=PixelFormat.RGB24,
        source_monitor_id="1",
        quality=quality,
        changed=True,
        change_score=1.0,
        sequence=1,
    )


class FakeEngine:
    name = "fake"

    def __init__(self, tokens):
        self.tokens = tuple(tokens)
        self.calls = 0

    def recognize(self, rgb_data, width, height, *, language, psm, timeout_seconds):
        self.calls += 1
        assert len(rgb_data) == width * height * 3
        assert language == "eng"
        assert psm == 6
        assert timeout_seconds == 5.0
        return self.tokens


def token(text, left, top, line, word, confidence=90.0):
    return RawOCRToken(text, confidence, left, top, max(1, len(text) * 4), 8, 1, 1, line, word)


def test_ocr_normalizes_tokens_and_builds_reading_order():
    engine = FakeEngine(
        [
            token("World", 20, 20, 2, 1),
            token("Hello", 2, 2, 1, 1),
            token("there", 30, 2, 1, 2),
        ]
    )
    result = OCRService(engine=engine).recognize(frame())
    assert result.text == "Hello there\nWorld"
    assert [line.text for line in result.lines] == ["Hello there", "World"]
    assert result.quality is OCRQuality.GOOD
    assert result.source_sequence == 1
    assert engine.calls == 1


def test_min_confidence_filters_tokens():
    engine = FakeEngine([token("bad", 0, 0, 1, 1, 20), token("good", 10, 0, 1, 2, 90)])
    result = OCRService(OCRConfig(min_confidence=50), engine).recognize(frame())
    assert result.text == "good"
    assert len(result.tokens) == 1


def test_reject_quality_fails_closed():
    bad = frame()
    object.__setattr__(
        bad,
        "quality",
        FrameQuality(brightness=1, contrast=1, level=QualityLevel.REJECT, usable=False),
    )
    try:
        OCRService(engine=FakeEngine([])).recognize(bad)
    except OCRInputError:
        pass
    else:
        raise AssertionError("Expected OCRInputError")


def test_config_bounds():
    try:
        OCRConfig(timeout_seconds=0)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")
