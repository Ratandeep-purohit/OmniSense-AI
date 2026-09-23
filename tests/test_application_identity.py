from omnisense_ai.application_discovery import ApplicationCandidate
from omnisense_ai.application_identity import (
    ApplicationIdentity,
    ApplicationIdentityService,
    ProcessIdentity,
    WindowIdentity,
)


def process(pid=101, path=r"C:\Apps\Example\Example.exe", created=123456):
    return ProcessIdentity(
        pid=pid,
        executable_path=path,
        process_name="Example.exe",
        creation_time_ns=created,
        session_id=1,
    )


def test_process_identity_rejects_pid_only_matching():
    first = process()
    reused_pid = process(created=999999)
    assert first.pid == reused_pid.pid
    assert not first.same_instance(reused_pid)


def test_process_identity_requires_executable_and_creation_time():
    import pytest

    with pytest.raises(ValueError):
        process(path="")
    with pytest.raises(ValueError):
        process(created=0)


def test_window_identity_binds_hwnd_to_process_instance():
    p = process()
    same = WindowIdentity(1001, p, "Example")
    recreated = WindowIdentity(1001, process(created=999999), "Example")
    different_hwnd = WindowIdentity(1002, p, "Example")
    assert same.same_window(same)
    assert not same.same_window(recreated)
    assert not same.same_window(different_hwnd)


def test_application_identity_from_discovered_candidate():
    candidate = ApplicationCandidate(
        "startmenu:example",
        "Example App",
        r"C:\Apps\Example.lnk",
        "start_menu",
        "Example.exe",
    )
    identity = ApplicationIdentityService.from_candidate(candidate)
    assert isinstance(identity, ApplicationIdentity)
    assert identity.application_id == "startmenu:example"
    assert identity.matches_process("example.exe")
    assert not identity.matches_process("other.exe")


def test_non_windows_runtime_identity_is_explicitly_unavailable():
    import pytest

    service = ApplicationIdentityService()
    with pytest.raises(Exception, match="Windows identity APIs require Windows"):
        service.identify_process(1)
