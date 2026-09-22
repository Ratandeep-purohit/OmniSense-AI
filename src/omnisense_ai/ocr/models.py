"""Contracts for Phase 3 OCR."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class OCRQuality(StrEnum):
    EMPTY = "empty"
    LOW = "low"
    ACCEPTABLE = "acceptable"
    GOOD = "good"


@dataclass(frozen=True, slots=True)
class OCRConfig:
    language: str = "eng"
    psm: int = 6
    timeout_seconds: float = 5.0
    min_confidence: float = 0.0
    max_text_length: int = 20_000
    max_tokens: int = 2_000

    def __post_init__(self) -> None:
        if not self.language or len(self.language) > 32:
            raise ValueError("OCR language must be 1..32 characters.")
        if not 0 <= self.psm <= 13:
            raise ValueError("OCR page segmentation mode must be within 0..13.")
        if self.timeout_seconds <= 0 or self.timeout_seconds > 60:
            raise ValueError("OCR timeout must be within (0, 60] seconds.")
        if not 0 <= self.min_confidence <= 100:
            raise ValueError("Minimum OCR confidence must be within 0..100.")
        if self.max_text_length <= 0 or self.max_text_length > 1_000_000:
            raise ValueError("Maximum OCR text length is out of bounds.")
        if self.max_tokens <= 0 or self.max_tokens > 50_000:
            raise ValueError("Maximum OCR token count is out of bounds.")


@dataclass(frozen=True, slots=True)
class OCRBoundingBox:
    left: int
    top: int
    width: int
    height: int

    def __post_init__(self) -> None:
        if min(self.left, self.top, self.width, self.height) < 0:
            raise ValueError("OCR bounding-box values must be non-negative.")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("OCR bounding-box dimensions must be positive.")

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height


@dataclass(frozen=True, slots=True)
class OCRToken:
    text: str
    confidence: float
    box: OCRBoundingBox
    block: int
    paragraph: int
    line: int
    word: int

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("OCR token text must not be empty.")
        if not 0 <= self.confidence <= 100:
            raise ValueError("OCR confidence must be within 0..100.")
        if min(self.block, self.paragraph, self.line, self.word) < 0:
            raise ValueError("OCR hierarchy identifiers must be non-negative.")


@dataclass(frozen=True, slots=True)
class OCRLine:
    text: str
    tokens: tuple[OCRToken, ...]
    box: OCRBoundingBox

    def __post_init__(self) -> None:
        if not self.text.strip() or not self.tokens:
            raise ValueError("OCR line must contain text and tokens.")


@dataclass(frozen=True, slots=True)
class OCRResult:
    text: str
    tokens: tuple[OCRToken, ...]
    lines: tuple[OCRLine, ...]
    quality: OCRQuality
    source_monitor_id: str
    source_sequence: int
    engine: str
    language: str
    truncated: bool = False
    duration_ms: float = 0.0

    def __post_init__(self) -> None:
        if self.source_sequence < 1:
            raise ValueError("OCR source sequence must be >= 1.")
        if not self.source_monitor_id:
            raise ValueError("OCR source monitor ID is required.")
        if not self.engine or not self.language:
            raise ValueError("OCR engine and language are required.")
        if self.duration_ms < 0:
            raise ValueError("OCR duration must not be negative.")
