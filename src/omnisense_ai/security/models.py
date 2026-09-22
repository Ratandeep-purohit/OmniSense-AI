"""Security policy and inspection contracts.

Phase 15 is deliberately observation/validation oriented. It does not grant
execution authority and does not replace Phase 10 authorization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum


class SecurityStatus(StrEnum):
    SAFE = "safe"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class SecurityConfig:
    enabled: bool = True
    max_input_length: int = 12000
    max_identifier_length: int = 256
    max_metadata_items: int = 32
    max_metadata_value_length: int = 1024
    redact_secrets: bool = True
    allowed_url_schemes: frozenset[str] = field(default_factory=lambda: frozenset({"https"}))

    def __post_init__(self) -> None:
        if self.max_input_length < 1:
            raise ValueError("max_input_length must be positive.")
        if self.max_identifier_length < 1:
            raise ValueError("max_identifier_length must be positive.")
        if self.max_metadata_items < 1:
            raise ValueError("max_metadata_items must be positive.")
        if self.max_metadata_value_length < 1:
            raise ValueError("max_metadata_value_length must be positive.")
        schemes = frozenset(s.strip().lower() for s in self.allowed_url_schemes if s.strip())
        if not schemes:
            raise ValueError("allowed_url_schemes must not be empty.")
        object.__setattr__(self, "allowed_url_schemes", schemes)


@dataclass(frozen=True, slots=True)
class SecurityInspection:
    status: SecurityStatus
    original_length: int
    sanitized_text: str
    redacted: bool
    reasons: tuple[str, ...]
    inspected_at: datetime

    def __post_init__(self) -> None:
        if self.inspected_at.tzinfo is None or self.inspected_at.utcoffset() is None:
            raise ValueError("inspected_at must be timezone-aware.")
