"""Application adapter contracts."""
from dataclasses import dataclass
from typing import Protocol
from ..application_identity.models import ApplicationIdentity
@dataclass(frozen=True,slots=True)
class SemanticTarget:
    name:str; control_type:str|None=None; automation_id:str|None=None; class_name:str|None=None
class ApplicationAdapter(Protocol):
    adapter_id:str
    def supports(self,identity:ApplicationIdentity)->bool: ...
    def semantic_aliases(self,text:str)->tuple[str,...]: ...
    def preferred_window_tokens(self,identity:ApplicationIdentity)->tuple[str,...]: ...
class GenericWindowsAdapter:
    adapter_id="generic.windows"
    def supports(self,identity): return True
    def semantic_aliases(self,text): return (text.strip(),)
    def preferred_window_tokens(self,identity): return (identity.display_name,)+identity.aliases
