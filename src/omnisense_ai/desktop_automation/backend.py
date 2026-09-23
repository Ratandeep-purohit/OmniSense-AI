"""Platform adapters for bounded desktop actions."""

from __future__ import annotations

from dataclasses import dataclass
import os
import time
from typing import Protocol

from ..action_planning.models import ActionStep, ActionType
from ..application_discovery import WindowsApplicationResolver


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
    """Windows backend using OS-discovered application entry points.

    The backend does not accept arbitrary executable paths, shell commands or
    PowerShell. It launches only a target that the resolver can rediscover from
    Windows Start Menu shortcuts or App Paths registrations.
    """

    def __init__(self) -> None:
        super().__init__()
        self._application_resolver = WindowsApplicationResolver()

    def execute(self, step: ActionStep, target: ResolvedTarget) -> str:
        if step.action_type != ActionType.OPEN_APP:
            return super().execute(step, target)

        params = dict(step.parameters)
        launch_target = params.get("launch_target")
        application_id = params.get("application_id")
        display_name = params.get("display_name", "application")

        if not launch_target or not application_id:
            raise ValueError("Application launch requires a discovered application identity.")

        if not self._application_resolver.is_trusted_target(launch_target):
            raise ValueError("Application launch target is not a current Windows-discovered entry point.")

        if os.name != "nt":
            raise RuntimeError("Windows desktop automation is only available on Windows.")

        # os.startfile delegates to the Windows shell. It can launch a trusted
        # .lnk entry without exposing a command interpreter or arbitrary argv.
        os.startfile(launch_target)
        time.sleep(0.8)
        return f"{display_name} launch requested"
