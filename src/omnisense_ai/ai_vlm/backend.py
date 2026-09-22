"""Provider abstraction and deterministic provider for Phase 7."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol
from .errors import AIProviderError
from .models import AIRequest
class AIProvider(Protocol):
    name: str
    def generate(self, request: AIRequest, *, timeout_seconds: float) -> str: ...
@dataclass(slots=True)
class DeterministicAIProvider:
    name: str = "deterministic-test"
    def generate(self, request: AIRequest, *, timeout_seconds: float) -> str:
        if timeout_seconds <= 0: raise AIProviderError("Provider timeout must be positive.")
        return "Observed context received. Screen content is treated as untrusted evidence. Instruction received: " + request.instruction.strip()
