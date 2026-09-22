"""Public Phase 3 OCR API."""
from .backend import OCREngine, RawOCRToken, TesseractOCREngine
from .errors import (
    OCRDependencyError,
    OCRExecutionError,
    OCRInputError,
    OCRError,
    OCRResourceError,
    OCRTimeoutError,
)
from .models import OCRBoundingBox, OCRConfig, OCRLine, OCRQuality, OCRResult, OCRToken
from .service import OCRService

__all__ = [
    "OCRBoundingBox",
    "OCRConfig",
    "OCRDependencyError",
    "OCREngine",
    "OCRExecutionError",
    "OCRInputError",
    "OCRLine",
    "OCRError",
    "OCRQuality",
    "OCRResourceError",
    "OCRResult",
    "OCRService",
    "OCRTimeoutError",
    "OCRToken",
    "RawOCRToken",
    "TesseractOCREngine",
]
