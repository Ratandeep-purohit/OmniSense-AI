import logging

from omnisense_ai.logging_config import RedactingFormatter, configure_logging


def test_redacting_formatter_hides_sensitive_values() -> None:
    formatter = RedactingFormatter("%(message)s")
    record = logging.LogRecord(
        "omnisense_ai", logging.INFO, __file__, 0, "API_KEY=very-secret TOKEN: abc123", (), None
    )

    formatted = formatter.format(record)

    assert "very-secret" not in formatted
    assert "abc123" not in formatted
    assert "***REDACTED***" in formatted


def test_configure_logging_does_not_add_duplicate_handlers() -> None:
    logger = configure_logging("INFO")
    logger = configure_logging("INFO")

    managed_handlers = [handler for handler in logger.handlers if getattr(handler, "_omnisense_handler", False)]

    assert len(managed_handlers) == 1
