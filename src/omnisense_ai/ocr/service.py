"""Phase 3 OCR orchestration and output normalization."""
from __future__ import annotations

from time import perf_counter

from ..visual_processing.models import QualityLevel, VisualFrame
from .backend import OCREngine, TesseractOCREngine
from .errors import OCRExecutionError, OCRInputError, OCRResourceError
from .models import OCRBoundingBox, OCRConfig, OCRLine, OCRQuality, OCRResult, OCRToken


class OCRService:
    """Run bounded OCR against a validated VisualFrame."""

    def __init__(
        self,
        config: OCRConfig | None = None,
        engine: OCREngine | None = None,
    ) -> None:
        self.config = config or OCRConfig()
        self.engine = engine or TesseractOCREngine()

    def recognize(self, frame: VisualFrame) -> OCRResult:
        self._validate_input(frame)
        started = perf_counter()
        raw_tokens = self.engine.recognize(
            frame.data,
            frame.width,
            frame.height,
            language=self.config.language,
            psm=self.config.psm,
            timeout_seconds=self.config.timeout_seconds,
        )
        if len(raw_tokens) > self.config.max_tokens:
            raise OCRResourceError("OCR token count exceeded configured limit.")

        tokens = self._normalize_tokens(raw_tokens)
        text, truncated = self._build_text(tokens)
        lines = self._build_lines(tokens)
        quality = self._quality(tokens, text)
        return OCRResult(
            text=text,
            tokens=tokens,
            lines=lines,
            quality=quality,
            source_monitor_id=frame.source_monitor_id,
            source_sequence=frame.sequence,
            engine=self.engine.name,
            language=self.config.language,
            truncated=truncated,
            duration_ms=round((perf_counter() - started) * 1000, 3),
        )

    def _validate_input(self, frame: VisualFrame) -> None:
        if not frame.data or frame.width <= 0 or frame.height <= 0:
            raise OCRInputError("Visual frame is empty or has invalid dimensions.")
        if frame.pixel_format.value != "RGB24":
            raise OCRInputError("Phase 3 requires RGB24 VisualFrame input.")
        if frame.quality.level is QualityLevel.REJECT or not frame.quality.usable:
            raise OCRInputError("Visual frame quality is insufficient for OCR.")

    def _normalize_tokens(self, raw_tokens) -> tuple[OCRToken, ...]:
        normalized: list[OCRToken] = []
        for raw in raw_tokens:
            text = raw.text.strip()
            if not text or raw.confidence < self.config.min_confidence:
                continue
            try:
                token = OCRToken(
                    text=text[: self.config.max_text_length],
                    confidence=raw.confidence,
                    box=OCRBoundingBox(raw.left, raw.top, raw.width, raw.height),
                    block=raw.block,
                    paragraph=raw.paragraph,
                    line=raw.line,
                    word=raw.word,
                )
            except ValueError as exc:
                raise OCRExecutionError("OCR engine returned invalid token metadata.") from exc
            normalized.append(token)
        return tuple(
            sorted(
                normalized,
                key=lambda item: (
                    item.block,
                    item.paragraph,
                    item.line,
                    item.box.top,
                    item.box.left,
                    item.word,
                ),
            )
        )

    def _build_text(self, tokens: tuple[OCRToken, ...]) -> tuple[str, bool]:
        parts: list[str] = []
        total = 0
        truncated = False
        for token in tokens:
            separator = "" if not parts or token.line == tokens[max(0, len(parts) - 1)].line else "\n"
            addition = separator + token.text
            if total + len(addition) > self.config.max_text_length:
                remaining = self.config.max_text_length - total
                if remaining > 0:
                    parts.append(addition[:remaining])
                truncated = True
                break
            parts.append(addition)
            total += len(addition)
        return "".join(parts).strip(), truncated

    @staticmethod
    def _build_lines(tokens: tuple[OCRToken, ...]) -> tuple[OCRLine, ...]:
        groups: dict[tuple[int, int, int], list[OCRToken]] = {}
        for token in tokens:
            groups.setdefault((token.block, token.paragraph, token.line), []).append(token)
        lines: list[OCRLine] = []
        for key in sorted(groups):
            line_tokens = tuple(sorted(groups[key], key=lambda item: (item.box.top, item.box.left)))
            left = min(t.box.left for t in line_tokens)
            top = min(t.box.top for t in line_tokens)
            right = max(t.box.right for t in line_tokens)
            bottom = max(t.box.bottom for t in line_tokens)
            lines.append(
                OCRLine(
                    text=" ".join(t.text for t in line_tokens),
                    tokens=line_tokens,
                    box=OCRBoundingBox(left, top, right - left, bottom - top),
                )
            )
        return tuple(lines)

    @staticmethod
    def _quality(tokens: tuple[OCRToken, ...], text: str) -> OCRQuality:
        if not tokens or not text:
            return OCRQuality.EMPTY
        average = sum(t.confidence for t in tokens) / len(tokens)
        if average < 50:
            return OCRQuality.LOW
        if average < 80:
            return OCRQuality.ACCEPTABLE
        return OCRQuality.GOOD
