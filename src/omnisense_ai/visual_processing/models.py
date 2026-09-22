"""Contracts for Phase 2 visual processing."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PixelFormat(StrEnum):
    RGB24 = "RGB24"
    GRAY8 = "GRAY8"


class QualityLevel(StrEnum):
    REJECT = "reject"
    LOW = "low"
    ACCEPTABLE = "acceptable"
    GOOD = "good"


@dataclass(frozen=True, slots=True)
class ProcessingConfig:
    """Bounded, deterministic visual-processing configuration."""

    target_width: int = 1280
    target_height: int = 720
    min_brightness: float = 5.0
    max_brightness: float = 250.0
    min_contrast: float = 3.0
    change_threshold: float = 0.08
    signature_size: int = 16

    def __post_init__(self) -> None:
        if self.target_width <= 0 or self.target_height <= 0:
            raise ValueError("Target dimensions must be positive.")
        if not 0 <= self.min_brightness < self.max_brightness <= 255:
            raise ValueError("Brightness bounds must be within 0..255.")
        if self.min_contrast < 0:
            raise ValueError("Minimum contrast must not be negative.")
        if not 0 <= self.change_threshold <= 1:
            raise ValueError("Change threshold must be within 0..1.")
        if self.signature_size <= 0 or self.signature_size > 64:
            raise ValueError("Signature size must be between 1 and 64.")


@dataclass(frozen=True, slots=True)
class FrameQuality:
    brightness: float
    contrast: float
    level: QualityLevel
    usable: bool


@dataclass(frozen=True, slots=True)
class VisualFrame:
    data: bytes
    width: int
    height: int
    pixel_format: PixelFormat
    source_monitor_id: str
    quality: FrameQuality
    changed: bool
    change_score: float
    sequence: int

    def __post_init__(self) -> None:
        expected = self.width * self.height * (3 if self.pixel_format is PixelFormat.RGB24 else 1)
        if len(self.data) != expected:
            raise ValueError("Visual frame byte length does not match dimensions and format.")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Visual frame dimensions must be positive.")
        if self.sequence < 1:
            raise ValueError("Visual frame sequence must start at 1.")
        if not 0 <= self.change_score <= 1:
            raise ValueError("Change score must be within 0..1.")
