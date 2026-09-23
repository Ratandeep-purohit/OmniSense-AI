"""Platform adapters for bounded desktop actions."""
from __future__ import annotations
from dataclasses import dataclass
import os,time
from typing import Protocol
from ..action_planning.models import ActionStep,ActionType
from ..application_discovery import WindowsApplicationResolver
from ..ui_automation import NativeUIAutomationService

@dataclass(frozen=True,slots=True)
class ResolvedTarget:
    x:int|None=None; y:int|None=None; app_key:str|None=None; window_id:int|None=None
    semantic_name:str|None=None; control_type:str|None=None; automation_id:str|None=None

class DesktopAutomationBackend(Protocol):
    def execute(self,step:ActionStep,target:ResolvedTarget)->str: ...
    def close(self)->None: ...

class NullDesktopAutomationBackend:
    def execute(self,step,target): raise RuntimeError("No desktop automation backend is configured.")
    def close(self): return None

class PyAutoGUIDesktopBackend:
    def __init__(self,*,allowed_apps:frozenset[str]=frozenset()):
        try: import pyautogui
        except ImportError as exc: raise RuntimeError("pyautogui is required for the desktop backend.") from exc
        self._pyautogui=pyautogui; self._allowed_apps=allowed_apps
    def execute(self,step,target):
        p=self._pyautogui; params=dict(step.parameters)
        if step.action_type==ActionType.CLICK:
            if target.x is None or target.y is None: raise ValueError("CLICK requires x/y target coordinates.")
            p.click(target.x,target.y); return "click completed"
        if step.action_type==ActionType.MOVE:
            if target.x is None or target.y is None: raise ValueError("MOVE requires x/y target coordinates.")
            p.moveTo(target.x,target.y); return "move completed"
        if step.action_type==ActionType.TYPE:
            text=params.get("text")
            if text is None: raise ValueError("TYPE requires a text parameter.")
            p.write(text); return "type completed"
        if step.action_type==ActionType.HOTKEY:
            keys=params.get("keys")
            if not keys: raise ValueError("HOTKEY requires keys.")
            p.hotkey(*[k.strip() for k in keys.split("+")]); return "hotkey completed"
        if step.action_type==ActionType.SCROLL:
            amount=int(params.get("amount","1"))
            if abs(amount)>10: raise ValueError("SCROLL amount exceeds the safety bound.")
            p.scroll(amount); return "scroll completed"
        if step.action_type==ActionType.WAIT:
            seconds=float(params.get("seconds","0.5"))
            if not 0<=seconds<=30: raise ValueError("WAIT seconds out of bounds.")
            time.sleep(seconds); return "wait completed"
        raise ValueError(f"Action type {step.action_type} is not implemented by this adapter.")
    def close(self): return None

class WindowsDesktopBackend(PyAutoGUIDesktopBackend):
    """Windows backend using discovered identity plus optional native UIA semantic control targeting."""
    def __init__(self):
        super().__init__(); self._application_resolver=WindowsApplicationResolver(); self._uia=NativeUIAutomationService()
    def execute(self,step,target):
        if step.action_type in (ActionType.CLICK,ActionType.TYPE) and target.semantic_name and target.window_id:
            return self._execute_semantic(step,target)
        if step.action_type!=ActionType.OPEN_APP: return super().execute(step,target)
        params=dict(step.parameters); launch_target=params.get("launch_target"); application_id=params.get("application_id"); display_name=params.get("display_name","application")
        if not launch_target or not application_id: raise ValueError("Application launch requires a discovered application identity.")
        if not self._application_resolver.is_trusted_target(launch_target): raise ValueError("Application launch target is not a current Windows-discovered entry point.")
        if os.name!="nt": raise RuntimeError("Windows desktop automation is only available on Windows.")
        os.startfile(launch_target); time.sleep(.8); return f"{display_name} launch requested"
    def _execute_semantic(self,step,target):
        if not self._uia.available: raise RuntimeError("Native UI Automation dependency is not installed.")
        from pywinauto import Desktop
        window=Desktop(backend="uia").window(handle=target.window_id)
        selector=window.child_window(title=target.semantic_name,control_type=target.control_type,auto_id=target.automation_id)
        selector.wait("exists enabled",timeout=3)
        if step.action_type==ActionType.CLICK: selector.click_input(); return "semantic click completed"
        text=dict(step.parameters).get("text")
        if text is None: raise ValueError("TYPE requires a text parameter.")
        selector.set_focus(); selector.type_keys(text,with_spaces=True,pause=.01); return "semantic type completed"
    def close(self): return None
