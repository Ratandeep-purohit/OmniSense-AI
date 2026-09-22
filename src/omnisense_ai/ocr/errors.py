"""Typed errors for Phase 3 OCR."""
from __future__ import annotations


class OCRError(RuntimeError):
    """Base class for OCR failures."""


class OCRDependencyError(OCRError):
    """OCR engine dependency is missing or unavailable."""


class OCRInputError(OCRError):
    """Visual input cannot be processed as OCR input."""


class OCRTimeoutError(OCRError):
    """OCR engine exceeded its bounded execution time."""


class OCRResourceError(OCRError):
    """OCR processing exceeded a configured resource limit."""


class OCRExecutionError(OCRError):
    """OCR engine failed during execution."""
