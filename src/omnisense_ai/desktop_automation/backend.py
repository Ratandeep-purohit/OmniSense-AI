"""Platform adapters for bounded desktop actions."""

from __future__ import annotations

from dataclasses import dataclass
import os
import time
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
    """Windows-friendly bounded primitive-action adapter."""

    def __init__(self, *, allowed_apps: frozenset[str] = frozenset()) -> None:
        try:
            import pyautogui
        except ImportError as exc:
            raise RuntimeError("pyautogui is required for the desktop backend.") from exc
        self._pyautogui = pyautogui
        self._allowed_apps = allowed_apps

    def execute(self, step: ActionStep, target: ResolvedTarget) -> str:
        p = self._pyautogui
        params = dict(step.parameters)

        if step.action_type == ActionType.CLICK:
            if target.x is None or target.y is None:
                raise ValueError("CLICK requires x/y target coordinates.")
            p.click(target.x, target.y)
            return "click completed"

        if step.action_type == ActionType.MOVE:
            if target.x is None or target.y is None:
                raise ValueError("MOVE requires x/y target coordinates.")
            p.moveTo(target.x, target.y)
            return "move completed"

        if step.action_type == ActionType.TYPE:
            text = params.get("text")
            if text is None:
                raise ValueError("TYPE requires a text parameter.")
            p.write(text)
            return "type completed"

        if step.action_type == ActionType.HOTKEY:
            keys = params.get("keys")
            if not keys:
                raise ValueError("HOTKEY requires keys.")
            p.hotkey(*[k.strip() for k in keys.split("+")])
            return "hotkey completed"

        if step.action_type == ActionType.SCROLL:
            amount = int(params.get("amount", "1"))
            if abs(amount) > 10:
                raise ValueError("SCROLL amount exceeds the safety bound.")
            p.scroll(amount)
            return "scroll completed"

        if step.action_type == ActionType.WAIT:
            seconds = float(params.get("seconds", "0.5"))
            if not 0 <= seconds <= 30:
                raise ValueError("WAIT seconds out of bounds.")
            time.sleep(seconds)
            return "wait completed"

        raise ValueError(f"Action type {step.action_type} is not implemented by this adapter.")

    def close(self) -> None:
        return None


class WindowsDesktopBackend(PyAutoGUIDesktopBackend):
    """Explicit Windows backend with a small, fixed application allowlist.

    Application launching uses Windows Shell file/URI associations rather than
    arbitrary shell commands. No command string, PowerShell script, or
    user-supplied executable path is accepted.
    """

    _LAUNCH_TARGETS = {
        "word": "ms-word:",
        "excel": "ms-excel:",
        "powerpoint": "ms-powerpoint:",
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "steam": "steam://open/main",
    }

    def execute(self, step: ActionStep, target: ResolvedTarget) -> str:
        if step.action_type != ActionType.OPEN_APP:
            return super().execute(step, target)

        app = dict(step.parameters).get("app")
        launch_target = dict(step.parameters).get("launch_target")
        if app not in self._LAUNCH_TARGETS:
            raise ValueError("Application is not on the OmniSense allowlist.")
        if launch_target != self._LAUNCH_TARGETS[app]:
            raise ValueError("Application launch target does not match the allowlist.")

        if os.name != "nt":
            raise RuntimeError("Windows desktop automation is only available on Windows.")

        os.startfile(launch_target)
        time.sleep(0.8)
        return f"{app} launch requested"
