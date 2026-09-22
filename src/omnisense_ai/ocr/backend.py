"""OCR engine adapters for Phase 3."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .errors import OCRDependencyError, OCRExecutionError, OCRTimeoutError


@dataclass(frozen=True, slots=True)
class RawOCRToken:
    text: str
    confidence: float
    left: int
    top: int
    width: int
    height: int
    block: int
    paragraph: int
    line: int
    word: int


class OCREngine(Protocol):
    name: str

    def recognize(
        self,
        rgb_data: bytes,
        width: int,
        height: int,
        *,
        language: str,
        psm: int,
        timeout_seconds: float,
    ) -> tuple[RawOCRToken, ...]:
        ...


class TesseractOCREngine:
    """Tesseract adapter. The executable remains an external, user-installed dependency."""

    name = "tesseract"

    def __init__(self, executable: str | None = None) -> None:
        try:
            import pytesseract
        except ImportError as exc:
            raise OCRDependencyError(
                "pytesseract is not installed; install the OCR optional dependencies."
            ) from exc
        self._pytesseract = pytesseract
        if executable:
            self._pytesseract.pytesseract.tesseract_cmd = executable

    def is_available(self) -> bool:
        try:
            self._pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def recognize(
        self,
        rgb_data: bytes,
        width: int,
        height: int,
        *,
        language: str,
        psm: int,
        timeout_seconds: float,
    ) -> tuple[RawOCRToken, ...]:
        if not self.is_available():
            raise OCRDependencyError(
                "Tesseract executable is unavailable. Install Tesseract or configure its path."
            )
        try:
            from PIL import Image

            image = Image.frombytes("RGB", (width, height), rgb_data)
            data = self._pytesseract.image_to_data(
                image,
                lang=language,
                config=f"--psm {psm}",
                output_type=self._pytesseract.Output.DICT,
                timeout=timeout_seconds,
            )
        except RuntimeError as exc:
            if "timeout" in str(exc).lower():
                raise OCRTimeoutError("Tesseract OCR timed out.") from exc
            raise OCRExecutionError("Tesseract OCR execution failed.") from exc
        except Exception as exc:
            raise OCRExecutionError("Tesseract OCR execution failed.") from exc

        tokens: list[RawOCRToken] = []
        count = len(data.get("text", []))
        for i in range(count):
            text = str(data["text"][i]).strip()
            try:
                confidence = float(data["conf"][i])
                left = int(data["left"][i])
                top = int(data["top"][i])
                token_width = int(data["width"][i])
                token_height = int(data["height"][i])
                block = int(data["block_num"][i])
                paragraph = int(data["par_num"][i])
                line = int(data["line_num"][i])
                word = int(data["word_num"][i])
            except (KeyError, TypeError, ValueError, IndexError) as exc:
                raise OCRExecutionError("Tesseract returned malformed OCR metadata.") from exc
            if text and confidence >= 0 and token_width > 0 and token_height > 0:
                tokens.append(
                    RawOCRToken(
                        text=text,
                        confidence=confidence,
                        left=left,
                        top=top,
                        width=token_width,
                        height=token_height,
                        block=block,
                        paragraph=paragraph,
                        line=line,
                        word=word,
                    )
                )
        return tuple(tokens)
