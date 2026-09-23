"""Bounded recovery: re-observe/re-plan suggestions, never silent re-execution."""
from dataclasses import dataclass
from enum import StrEnum
class RecoveryAction(StrEnum): REOBSERVE="reobserve"; REPLAN="replan"; ASK_USER="ask_user"; STOP="stop"
@dataclass(frozen=True,slots=True)
class RecoveryDecision:
    action:RecoveryAction; reason:str; attempt:int; max_attempts:int
class RecoveryEngine:
    def __init__(self,max_attempts:int=2):
        if not 0<=max_attempts<=3: raise ValueError("max_attempts must be 0..3")
        self.max_attempts=max_attempts
    def decide(self,*,attempt:int,error:str,verified:bool=False)->RecoveryDecision:
        if verified:return RecoveryDecision(RecoveryAction.STOP,"action already verified",attempt,self.max_attempts)
        if attempt>=self.max_attempts:return RecoveryDecision(RecoveryAction.ASK_USER,"bounded recovery exhausted; explicit user decision required",attempt,self.max_attempts)
        if "stale" in error.casefold():return RecoveryDecision(RecoveryAction.REOBSERVE,"fresh context is required",attempt,self.max_attempts)
        if "target" in error.casefold() or "identity" in error.casefold():return RecoveryDecision(RecoveryAction.REPLAN,"target identity changed; rebuild the plan",attempt,self.max_attempts)
        return RecoveryDecision(RecoveryAction.ASK_USER,"failure cannot be safely recovered automatically",attempt,self.max_attempts)
