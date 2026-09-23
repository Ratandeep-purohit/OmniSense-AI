from omnisense_ai.action_planning.models import ActionRisk, ActionStep, ActionTarget, ActionType
from omnisense_ai.application_discovery import ApplicationCandidate
from omnisense_ai.desktop_automation.backend import ResolvedTarget, WindowsDesktopBackend


class FakeResolver:
    def __init__(self, *, trusted_targets=()):
        self.trusted_targets = set(trusted_targets)

    def is_trusted_target(self, target):
        return target in self.trusted_targets


def _step(*, display_name="Notepad", launch_target="notepad.exe", application_id="app-paths:notepad.exe"):
    return ActionStep(
        "step-1",
        ActionType.OPEN_APP,
        ActionTarget("application", f"Open {display_name}"),
        (
            ("app", display_name.casefold()),
            ("display_name", display_name),
            ("launch_target", launch_target),
            ("application_id", application_id),
        ),
        ActionRisk.LOW,
        "app_is_any:notepad.exe",
        False,
    )


def test_windows_backend_rejects_missing_discovered_identity():
    backend = object.__new__(WindowsDesktopBackend)
    step = _step(launch_target="unknown.exe", application_id="")
    try:
        backend.execute(step, ResolvedTarget(app_key="unknown"))
    except ValueError as exc:
        assert "discovered application identity" in str(exc)
    else:
        raise AssertionError("Applications without a discovered identity must be rejected")


def test_windows_backend_rejects_untrusted_launch_target(monkeypatch):
    backend = object.__new__(WindowsDesktopBackend)
    backend._application_resolver = FakeResolver()
    step = _step(launch_target="unknown.exe")
    try:
        backend.execute(step, ResolvedTarget(app_key="unknown"))
    except ValueError as exc:
        assert "current Windows-discovered entry point" in str(exc)
    else:
        raise AssertionError("Untrusted launch targets must be rejected")


def test_windows_backend_uses_currently_discovered_launch_target(monkeypatch):
    backend = object.__new__(WindowsDesktopBackend)
    backend._application_resolver = FakeResolver(trusted_targets={"notepad.exe"})
    launched = []
    monkeypatch.setattr("omnisense_ai.desktop_automation.backend.os.name", "nt")
    monkeypatch.setattr(
        "omnisense_ai.desktop_automation.backend.os.startfile",
        lambda target: launched.append(target),
        raising=False,
    )
    monkeypatch.setattr("omnisense_ai.desktop_automation.backend.time.sleep", lambda _: None)

    result = backend.execute(_step(), ResolvedTarget(app_key="notepad"))

    assert result == "Notepad launch requested"
    assert launched == ["notepad.exe"]
