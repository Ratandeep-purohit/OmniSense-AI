"""Data contracts for Phase 7 provider-neutral AI/VLM reasoning."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import StrEnum

class EvidenceTrust(StrEnum):
    OBSERVED = "observed"
    USER_PROVIDED = "user_provided"
    SYSTEM_POLICY = "system_policy"

class AIOutputStatus(StrEnum):
    SUCCESS = "success"
    REJECTED = "rejected"
    FAILED = "failed"

@dataclass(frozen=True, slots=True)
class AIConfig:
    enabled: bool = False
    provider: str = "none"
    model: str = ""
    timeout_seconds: float = 15.0
    max_input_chars: int = 24_000
    max_output_chars: int = 12_000
    max_retries: int = 1
    allow_visual_input: bool = True
    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0 or self.timeout_seconds > 120: raise ValueError("AI timeout must be within (0, 120] seconds.")
        if self.max_input_chars <= 0 or self.max_input_chars > 200_000: raise ValueError("AI max input is out of bounds.")
        if self.max_output_chars <= 0 or self.max_output_chars > 100_000: raise ValueError("AI max output is out of bounds.")
        if self.max_retries < 0 or self.max_retries > 3: raise ValueError("AI max retries must be within 0..3.")
        if self.enabled and not self.provider.strip(): raise ValueError("An AI provider is required when AI is enabled.")
        if len(self.provider) > 64 or len(self.model) > 128: raise ValueError("AI provider/model name is too long.")

@dataclass(frozen=True, slots=True)
class AIRequest:
    request_id: str
    context_id: str
    instruction: str
    observed_context: str
    user_context: str | None
    evidence_trust: EvidenceTrust = EvidenceTrust.OBSERVED
    visual_data: bytes | None = None
    visual_mime_type: str | None = None
    def __post_init__(self) -> None:
        if not self.request_id.strip() or not self.context_id.strip(): raise ValueError("AI request identifiers are required.")
        if not self.instruction.strip(): raise ValueError("AI instruction is required.")
        if not self.observed_context.strip(): raise ValueError("Observed context is required.")
        if len(self.instruction) > 20_000: raise ValueError("AI instruction is too long.")
        if self.visual_data is not None and (not self.visual_mime_type or not self.visual_mime_type.startswith("image/")): raise ValueError("Visual data requires an image MIME type.")

@dataclass(frozen=True, slots=True)
class AIResponse:
    request_id: str
    provider: str
    model: str
    status: AIOutputStatus
    answer: str
    confidence: float | None = None
    finish_reason: str | None = None
    usage_input: int | None = None
    usage_output: int | None = None
    warnings: tuple[str, ...] = field(default_factory=tuple)
    duration_ms: float = 0.0
    def __post_init__(self) -> None:
        if not self.request_id.strip() or not self.provider.strip(): raise ValueError("AI response identifiers are required.")
        if self.status is AIOutputStatus.SUCCESS and not self.answer.strip(): raise ValueError("Successful AI responses require an answer.")
        if self.confidence is not None and not 0 <= self.confidence <= 1: raise ValueError("AI confidence must be within 0..1.")
        if self.duration_ms < 0: raise ValueError("AI duration must not be negative.")
