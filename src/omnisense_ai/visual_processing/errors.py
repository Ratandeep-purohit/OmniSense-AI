"""Phase 2 visual-processing errors."""

from ..errors import OmniSenseError


class VisualProcessingError(OmniSenseError):
    """Base Phase 2 error."""


class UnsupportedPixelFormatError(VisualProcessingError):
    """Input pixel format is not supported."""


class InvalidFrameError(VisualProcessingError):
    """Input frame is malformed or exceeds processing limits."""


class ProcessingResourceError(VisualProcessingError):
    """Processing could not complete within resource constraints."""
