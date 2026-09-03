"""Centralized logging with basic redaction for sensitive values."""

from __future__ import annotations

import logging
import re


_SENSITIVE_VALUE = re.compile(
    r"(?i)\b(api[_-]?key|password|token|secret|authorization)\b\s*[:=]\s*([^\s,;]+)"
)


class RedactingFormatter(logging.Formatter):
    """Format log records without exposing common secret-value patterns."""

    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        return _SENSITIVE_VALUE.sub(r"\1=***REDACTED***", formatted)


def configure_logging(log_level: str) -> logging.Logger:
    """Configure and return the application logger without duplicate handlers."""

    logger = logging.getLogger("omnisense_ai")
    logger.setLevel(log_level)
    logger.propagate = False

    if not any(getattr(handler, "_omnisense_handler", False) for handler in logger.handlers):
        handler = logging.StreamHandler()
        handler._omnisense_handler = True  # type: ignore[attr-defined]
        handler.setFormatter(RedactingFormatter("%(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)

    return logger
