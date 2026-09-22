"""Deterministic visual processing for captured screen frames."""

from __future__ import annotations

from math import sqrt

from ..screen_capture.models import ScreenFrame
from .errors import InvalidFrameError, UnsupportedPixelFormatError
from .models import FrameQuality, PixelFormat, ProcessingConfig, QualityLevel, VisualFrame


class VisualProcessor:
    """Validate, resize, convert, normalize, score, and compare screen frames."""

    def __init__(self, config: ProcessingConfig | None = None) -> None:
        self.config = config or ProcessingConfig()
        self._previous_signature: bytes | None = None
        self._sequence = 0

    def reset(self) -> None:
        self._previous_signature = None
        self._sequence = 0

    def process(self, frame: ScreenFrame) -> VisualFrame:
        self._validate(frame)
        rgb = self._bgra_to_rgb(frame.data)
        width, height = frame.width, frame.height

        if (width, height) != (self.config.target_width, self.config.target_height):
            rgb = self._resize_rgb(
                rgb, width, height, self.config.target_width, self.config.target_height
            )
            width, height = self.config.target_width, self.config.target_height

        rgb = self._normalize_rgb(rgb)
        quality = self._quality(rgb)
        signature = self._signature(rgb, width, height)
        score = self._change_score(signature, self._previous_signature)
        changed = self._previous_signature is None or score >= self.config.change_threshold
        self._previous_signature = signature
        self._sequence += 1

        return VisualFrame(
            data=rgb,
            width=width,
            height=height,
            pixel_format=PixelFormat.RGB24,
            source_monitor_id=frame.monitor_id,
            quality=quality,
            changed=changed,
            change_score=score,
            sequence=self._sequence,
        )

    def _validate(self, frame: ScreenFrame) -> None:
        if frame.pixel_format.upper() != "BGRA":
            raise UnsupportedPixelFormatError(
                f"Unsupported capture pixel format: {frame.pixel_format}."
            )
        if frame.width > 7680 or frame.height > 4320:
            raise InvalidFrameError("Input frame exceeds the maximum supported dimensions.")
        expected = frame.width * frame.height * 4
        if len(frame.data) != expected:
            raise InvalidFrameError("Input frame byte length does not match BGRA dimensions.")

    @staticmethod
    def _bgra_to_rgb(data: bytes) -> bytes:
        out = bytearray(len(data) // 4 * 3)
        j = 0
        for i in range(0, len(data), 4):
            out[j] = data[i + 2]
            out[j + 1] = data[i + 1]
            out[j + 2] = data[i]
            j += 3
        return bytes(out)

    @staticmethod
    def _resize_rgb(data: bytes, src_w: int, src_h: int, dst_w: int, dst_h: int) -> bytes:
        out = bytearray(dst_w * dst_h * 3)
        for y in range(dst_h):
            sy = min(src_h - 1, (y * src_h) // dst_h)
            for x in range(dst_w):
                sx = min(src_w - 1, (x * src_w) // dst_w)
                src = (sy * src_w + sx) * 3
                dst = (y * dst_w + x) * 3
                out[dst:dst + 3] = data[src:src + 3]
        return bytes(out)

    @staticmethod
    def _normalize_rgb(data: bytes) -> bytes:
        # Canonical RGB byte representation; avoid destructive contrast changes.
        return bytes(data)

    @staticmethod
    def _quality(data: bytes) -> FrameQuality:
        if not data:
            raise InvalidFrameError("Cannot score an empty frame.")
        brightness_sum = 0.0
        values = bytearray(len(data) // 3)
        for i in range(0, len(data), 3):
            luminance = 0.2126 * data[i] + 0.7152 * data[i + 1] + 0.0722 * data[i + 2]
            brightness_sum += luminance
            values[i // 3] = int(luminance)
        brightness = brightness_sum / len(values)
        mean = brightness
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        contrast = sqrt(variance)

        if brightness < 5 or brightness > 250:
            level = QualityLevel.REJECT
        elif contrast < 3:
            level = QualityLevel.LOW
        elif contrast < 10:
            level = QualityLevel.ACCEPTABLE
        else:
            level = QualityLevel.GOOD
        return FrameQuality(
            brightness=round(brightness, 3),
            contrast=round(contrast, 3),
            level=level,
            usable=level is not QualityLevel.REJECT,
        )

    def _signature(self, data: bytes, width: int, height: int) -> bytes:
        size = self.config.signature_size
        signature = bytearray(size * size)
        for y in range(size):
            sy = min(height - 1, (y * height) // size)
            for x in range(size):
                sx = min(width - 1, (x * width) // size)
                idx = (sy * width + sx) * 3
                signature[y * size + x] = int(
                    0.2126 * data[idx] + 0.7152 * data[idx + 1] + 0.0722 * data[idx + 2]
                )
        return bytes(signature)

    @staticmethod
    def _change_score(current: bytes, previous: bytes | None) -> float:
        if previous is None:
            return 1.0
        if len(current) != len(previous):
            return 1.0
        return sum(abs(a - b) for a, b in zip(current, previous)) / (len(current) * 255)
