"""Windows UI Automation via pywinauto UIA when installed; inert elsewhere."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True, slots=True)
class UIElement:
    name: str
    control_type: str | None
    automation_id: str | None
    class_name: str | None
    handle: int | None

class NativeUIAutomationService:
    """Semantic UIA access. It refuses arbitrary coordinates when semantic data is requested."""
    def __init__(self): self.available=self._load()
    def _load(self):
        try:
            import pywinauto  # noqa: F401
            return True
        except Exception: return False
    def _window(self, hwnd: int):
        if not self.available: raise RuntimeError("Native UI Automation dependency is not installed.")
        from pywinauto import Desktop
        return Desktop(backend="uia").window(handle=hwnd)
    def enumerate(self, hwnd: int, *, max_depth: int=4, max_items: int=500) -> tuple[UIElement,...]:
        if max_depth<1 or max_depth>8 or max_items<1 or max_items>2000: raise ValueError("UIA enumeration bounds are invalid.")
        root=self._window(hwnd); out=[]
        def walk(control, depth):
            if depth>max_depth or len(out)>=max_items: return
            try:
                out.append(UIElement(str(control.window_text() or ""),getattr(control.element_info,"control_type",None),getattr(control.element_info,"automation_id",None),getattr(control.element_info,"class_name",None),getattr(control.element_info,"handle",None)))
                for child in control.children(): walk(child,depth+1)
            except Exception: return
        walk(root,0); return tuple(out)
    def find(self, hwnd: int, *, name: str|None=None, control_type: str|None=None, automation_id: str|None=None) -> UIElement | None:
        for item in self.enumerate(hwnd,max_depth=6,max_items=1000):
            if name and item.name.casefold()!=name.casefold(): continue
            if control_type and (item.control_type or "").casefold()!=control_type.casefold(): continue
            if automation_id and (item.automation_id or "").casefold()!=automation_id.casefold(): continue
            return item
        return None
