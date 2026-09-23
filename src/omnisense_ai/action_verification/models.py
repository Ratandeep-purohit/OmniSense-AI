"""Typed contracts for temporal post-action verification."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from ..action_planning.models import ActionType
class VerificationStatus(StrEnum): VERIFIED="verified"; NOT_VERIFIED="not_verified"; INDETERMINATE="indeterminate"; REJECTED="rejected"
class VerificationCheckStatus(StrEnum): PASSED="passed"; FAILED="failed"; INDETERMINATE="indeterminate"
@dataclass(frozen=True,slots=True)
class VerificationConfig:
    max_age_seconds:float=5.0; max_evidence_text_length:int=12000; require_post_execution_evidence:bool=True; allow_indeterminate:bool=True; require_temporal_transition:bool=False
    def __post_init__(self):
        if not .1<=self.max_age_seconds<=300: raise ValueError("max_age_seconds is out of bounds.")
        if not 1<=self.max_evidence_text_length<=100000: raise ValueError("max_evidence_text_length is out of bounds.")
@dataclass(frozen=True,slots=True)
class VerificationEvidence:
    context_id:str; captured_at:datetime; visible_text:str=""; window_id:int|None=None; app_name:str|None=None; application_id:str|None=None; window_title:str|None=None; facts:tuple[tuple[str,str],...]=(); source:str="unknown"; executable_path:str|None=None
    def __post_init__(self):
        if not self.context_id.strip(): raise ValueError("Evidence context_id is required.")
        if self.captured_at.tzinfo is None: raise ValueError("Evidence timestamp must be timezone-aware.")
        if len(self.visible_text)>100000: raise ValueError("Evidence text is too large.")
@dataclass(frozen=True,slots=True)
class VerificationCheck:
    step_id:str; action_type:ActionType; status:VerificationCheckStatus; expectation:str; message:str; observed_at:datetime
@dataclass(frozen=True,slots=True)
class VerificationResult:
    verification_id:str; plan_id:str; context_id:str; status:VerificationStatus; checks:tuple[VerificationCheck,...]; verified_at:datetime; evidence_captured_at:datetime; evidence_source:str; transition_proven:bool=False
