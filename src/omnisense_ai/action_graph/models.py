"""Explicit action graph contracts with pre/postcondition boundaries."""
from dataclasses import dataclass
from enum import StrEnum
from ..action_planning.models import ActionStep
class NodeState(StrEnum): PENDING="pending"; READY="ready"; RUNNING="running"; SUCCEEDED="succeeded"; FAILED="failed"; BLOCKED="blocked"
@dataclass(frozen=True,slots=True)
class ActionNode:
    node_id:str; step:ActionStep; preconditions:tuple[str,...]=(); postconditions:tuple[str,...]=(); state:NodeState=NodeState.PENDING
@dataclass(frozen=True,slots=True)
class ActionEdge:
    source:str; target:str; condition:str="success"
@dataclass(frozen=True,slots=True)
class ActionGraph:
    graph_id:str; nodes:tuple[ActionNode,...]; edges:tuple[ActionEdge,...]
    def __post_init__(self):
        ids={n.node_id for n in self.nodes}
        if len(ids)!=len(self.nodes): raise ValueError("Action graph node IDs must be unique.")
        if any(e.source not in ids or e.target not in ids for e in self.edges): raise ValueError("Action graph edge references an unknown node.")
