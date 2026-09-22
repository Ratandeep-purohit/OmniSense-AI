"""Phase 8 assistant contracts."""
from dataclasses import dataclass
from enum import StrEnum

class AssistantMode(StrEnum):
    ANSWER="answer"; EXPLAIN="explain"; SUGGEST="suggest"; CLARIFY="clarify"; REFUSE="refuse"

class AssistantStatus(StrEnum):
    SUCCESS="success"; NEEDS_CLARIFICATION="needs_clarification"; FAILED="failed"

@dataclass(frozen=True, slots=True)
class AssistantConfig:
    max_instruction_chars:int=4000
    max_response_chars:int=12000
    allow_suggestions:bool=True
    def __post_init__(self):
        if not 0 < self.max_instruction_chars <= 20000: raise ValueError("max_instruction_chars is out of bounds.")
        if not 0 < self.max_response_chars <= 100000: raise ValueError("max_response_chars is out of bounds.")

@dataclass(frozen=True, slots=True)
class AssistantRequest:
    instruction:str
    mode:AssistantMode=AssistantMode.ANSWER
    require_grounding:bool=True
    allow_suggestions:bool=True
    def __post_init__(self):
        if not self.instruction.strip(): raise ValueError("Assistant instruction is required.")
        if len(self.instruction)>20000: raise ValueError("Assistant instruction is too long.")

@dataclass(frozen=True, slots=True)
class AssistantResponse:
    status:AssistantStatus
    mode:AssistantMode
    answer:str
    context_id:str
    ai_request_id:str
    grounded:bool
    warnings:tuple[str,...]=()
    def __post_init__(self):
        if not self.context_id.strip() or not self.ai_request_id.strip(): raise ValueError("Assistant response IDs are required.")
        if not self.answer.strip(): raise ValueError("Assistant response requires an answer.")
        if len(self.answer)>100000: raise ValueError("Assistant response is too large.")
