"""Bounded security validation and secret-redaction service."""

from __future__ import annotations

from datetime import datetime, timezone
from re import Pattern, compile as re_compile
from urllib.parse import urlsplit

from .errors import SecurityDisabledError, SecurityInputError, SecurityPolicyError
from .models import SecurityConfig, SecurityInspection, SecurityStatus

_SECRET_PATTERNS: tuple[Pattern[str], ...] = (
    re_compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re_compile(r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|password|passwd|secret)\s*[:=]\s*[^\s,;]+"),
    re_compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re_compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
)
_CONTROL_PATTERN = re_compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_IDENTIFIER_PATTERN = re_compile(r"^[A-Za-z0-9._:/@+\-]+$")


class SecurityService:
    """Apply local security invariants without granting system authority."""

    def __init__(self, config: SecurityConfig | None = None) -> None:
        self.config = config or SecurityConfig()
        self._closed = False

    def inspect_text(self, value: str) -> SecurityInspection:
        self._ensure_enabled()
        self._ensure_open()
        if not isinstance(value, str):
            raise SecurityInputError("Security input must be text.")
        original_length = len(value)
        if original_length > self.config.max_input_length:
            raise SecurityPolicyError("Security input exceeds the configured length limit.")
        sanitized = _CONTROL_PATTERN.sub("", value)
        redacted = False
        if self.config.redact_secrets:
            for pattern in _SECRET_PATTERNS:
                sanitized, count = pattern.subn("[REDACTED]", sanitized)
                redacted = redacted or count > 0
        reasons: list[str] = []
        if sanitized != value:
            reasons.append("control_characters_removed")
        if redacted:
            reasons.append("secrets_redacted")
        return SecurityInspection(SecurityStatus.SAFE, original_length, sanitized, redacted, tuple(reasons), datetime.now(timezone.utc))

    def validate_identifier(self, value: str) -> str:
        self._ensure_enabled()
        self._ensure_open()
        if not isinstance(value, str):
            raise SecurityInputError("Identifier must be text.")
        normalized = value.strip()
        if not normalized:
            raise SecurityInputError("Identifier must not be empty.")
        if len(normalized) > self.config.max_identifier_length:
            raise SecurityPolicyError("Identifier exceeds the configured length limit.")
        if not _IDENTIFIER_PATTERN.fullmatch(normalized):
            raise SecurityPolicyError("Identifier contains unsupported characters.")
        return normalized

    def validate_url(self, value: str) -> str:
        self._ensure_enabled()
        self._ensure_open()
        if not isinstance(value, str):
            raise SecurityInputError("URL must be text.")
        normalized = value.strip()
        if len(normalized) > self.config.max_input_length:
            raise SecurityPolicyError("URL exceeds the configured length limit.")
        parsed = urlsplit(normalized)
        if parsed.scheme.lower() not in self.config.allowed_url_schemes:
            raise SecurityPolicyError("URL scheme is not allowed by security policy.")
        if not parsed.netloc or parsed.username is not None or parsed.password is not None:
            raise SecurityPolicyError("URL must contain a host and must not contain credentials.")
        return normalized

    def validate_metadata(self, metadata: dict[str, str]) -> dict[str, str]:
        self._ensure_enabled()
        self._ensure_open()
        if not isinstance(metadata, dict):
            raise SecurityInputError("Metadata must be a dictionary.")
        if len(metadata) > self.config.max_metadata_items:
            raise SecurityPolicyError("Metadata item limit exceeded.")
        sanitized: dict[str, str] = {}
        for key, value in metadata.items():
            safe_key = self.validate_identifier(str(key))
            if not isinstance(value, str):
                raise SecurityInputError("Metadata values must be text.")
            if len(value) > self.config.max_metadata_value_length:
                raise SecurityPolicyError("Metadata value exceeds the configured length limit.")
            sanitized[safe_key] = self.inspect_text(value).sanitized_text
        return sanitized

    def close(self) -> None:
        self._closed = True

    def _ensure_open(self) -> None:
        if self._closed:
            raise SecurityInputError("Security service is closed.")

    def _ensure_enabled(self) -> None:
        if not self.config.enabled:
            raise SecurityDisabledError("Security service is disabled.")
