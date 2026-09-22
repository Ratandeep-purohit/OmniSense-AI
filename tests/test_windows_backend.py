from omnisense_ai.action_planning.models import ActionRisk, ActionStep, ActionTarget, ActionType
from omnisense_ai.desktop_automation.backend import ResolvedTarget, WindowsDesktopBackend


def test_windows_backend_rejects_unknown_application():
    backend = object.__new__(WindowsDesktopBackend)
    step = ActionStep(
        "step-1",
        ActionType.OPEN_APP,
        ActionTarget("application", "Open unknown"),
        (("app", "unknown"), ("launch_target", "unknown.exe")),
        ActionRisk.LOW,
        "app_is:unknown.exe",
        True,
    )
    try:
        backend.execute(step, ResolvedTarget(app_key="unknown"))
    except ValueError as exc:
        assert "allowlist" in str(exc)
    else:
        raise AssertionError("Unknown applications must be rejected")


def test_windows_backend_uses_fixed_launch_target(monkeypatch):
    backend = object.__new__(WindowsDesktopBackend)
    launched = []
    monkeypatch.setattr("omnisense_ai.desktop_automation.backend.os.name", "nt")
    monkeypatch.setattr(
        "omnisense_ai.desktop_automation.backend.os.startfile",
        lambda target: launched.append(target),
        raising=False,
    )
    step = ActionStep(
        "step-1",
        ActionType.OPEN_APP,
        ActionTarget("application", "Open Notepad"),
        (("app", "notepad"), ("launch_target", "notepad.exe")),
        ActionRisk.LOW,
        "app_is:notepad.exe",
        True,
    )
    result = backend.execute(step, ResolvedTarget(app_key="notepad"))
    assert result == "notepad launch requested"
    assert launched == ["notepad.exe"]
