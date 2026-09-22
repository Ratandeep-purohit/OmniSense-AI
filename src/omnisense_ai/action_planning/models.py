"""Typed contracts for Phase 9 action planning."""
from dataclasses import dataclass
from enum import StrEnum
class ActionType(StrEnum):
    CLICK="click"; TYPE="type"; HOTKEY="hotkey"; OPEN_APP="open_app"; CLOSE_APP="close_app"; MOVE="move"; SCROLL="scroll"; WAIT="wait"
class ActionRisk(StrEnum):
    LOW="low"; MEDIUM="medium"; HIGH="high"; CRITICAL="critical"
class PlanStatus(StrEnum):
    READY="ready"; NEEDS_CLARIFICATION="needs_clarification"; REJECTED="rejected"
@dataclass(frozen=True,slots=True)
class ActionTarget:
    target_id:str; description:str; expected_text:str|None=None; window_id:str|None=None
    def __post_init__(self):
        if not self.target_id.strip() or not self.description.strip(): raise ValueError("Action target identifiers are required.")
@dataclass(frozen=True,slots=True)
class ActionStep:
    step_id:str; action_type:ActionType; target:ActionTarget|None; parameters:tuple[tuple[str,str],...]; risk:ActionRisk; expected_outcome:str; reversible:bool=False
    def __post_init__(self):
        if not self.step_id.strip() or not self.expected_outcome.strip(): raise ValueError("Action step fields are required.")
        if len(self.parameters)>30: raise ValueError("Too many action parameters.")
@dataclass(frozen=True,slots=True)
class ActionPlan:
    plan_id:str; context_id:str; intent:str; status:PlanStatus; steps:tuple[ActionStep,...]=(); rationale:str=""; requires_confirmation:bool=True
    def __post_init__(self):
        if not self.plan_id.strip() or not self.context_id.strip() or not self.intent.strip(): raise ValueError("Plan identifiers and intent are required.")
        if len(self.steps)>20: raise ValueError("Action plan contains too many steps.")
@dataclass(frozen=True,slots=True)
class ActionPlanningConfig:
    max_steps:int=10; max_intent_chars:int=4000; allow_high_risk_plans:bool=False
    def __post_init__(self):
        if not 1<=self.max_steps<=20: raise ValueError("max_steps is out of bounds.")
        if not 1<=self.max_intent_chars<=20000: raise ValueError("max_intent_chars is out of bounds.")
