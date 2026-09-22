"""Platform adapter boundary for bounded desktop actions."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol
from ..action_planning.models import ActionStep, ActionType


@dataclass(frozen=True, slots=True)
class ResolvedTarget:
    x: int | None = None
    y: int | None = None
    app_key: str | None = None


class DesktopAutomationBackend(Protocol):
    def execute(self, step: ActionStep, target: ResolvedTarget) -> str: ...
    def close(self) -> None: ...


class NullDesktopAutomationBackend:
    """Safe backend used by default; it never touches the desktop."""
    def execute(self, step: ActionStep, target: ResolvedTarget) -> str:
        raise RuntimeError("No desktop automation backend is configured.")
    def close(self) -> None:
        return None


class PyAutoGUIDesktopBackend:
    """Optional Windows-friendly adapter. It exposes only bounded primitive actions."""
    def __init__(self, *, allowed_apps: frozenset[str] = frozenset()) -> None:
        try:
            import pyautogui
        except ImportError as exc:
            raise RuntimeError("pyautogui is required for the desktop backend.") from exc
        self._pyautogui = pyautogui
        self._allowed_apps = allowed_apps

    def execute(self, step: ActionStep, target: ResolvedTarget) -> str:
        p = self._pyautogui
        if step.action_type == ActionType.CLICK:
            if target.x is None or target.y is None: raise ValueError("CLICK requires x/y target coordinates.")
            p.click(target.x, target.y); return "click completed"
        if step.action_type == ActionType.MOVE:
            if target.x is None or target.y is None: raise ValueError("MOVE requires x/y target coordinates.")
            p.moveTo(target.x, target.y); return "move completed"
        if step.action_type == ActionType.TYPE:
            text = dict(step.parameters).get("text")
            if text is None: raise ValueError("TYPE requires a text parameter.")
            p.write(text); return "type completed"
        if step.action_type == ActionType.HOTKEY:
            keys = dict(step.parameters).get("keys")
            if not keys: raise ValueError("HOTKEY requires keys.")
            p.hotkey(*[k.strip() for k in keys.split("+")]); return "hotkey completed"
        if step.action_type == ActionType.SCROLL:
            amount = int(dict(step.parameters).get("amount", "1"))
            p.scroll(amount); return "scroll completed"
        if step.action_type == ActionType.WAIT:
            import time
            seconds = float(dict(step.parameters).get("seconds", "0.5"))
            if not 0 <= seconds <= 30: raise ValueError("WAIT seconds out of bounds.")
            time.sleep(seconds); return "wait completed"
        raise ValueError(f"Action type {step.action_type} is not implemented by this adapter.")

    def close(self) -> None:
        return None
