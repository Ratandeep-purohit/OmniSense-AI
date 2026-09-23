from omnisense_ai.application_discovery import ApplicationCandidate, WindowsApplicationResolver


def test_application_candidate_requires_identity():
    candidate = ApplicationCandidate("id", "Example App", r"C:\Apps\Example.lnk", "start_menu")
    assert candidate.display_name == "Example App"


def test_application_name_normalization_and_scoring():
    assert WindowsApplicationResolver._normalize("Epic Games Launcher") == "epic games launcher"
    assert WindowsApplicationResolver._score("epic", "Epic Games Launcher") == 90
    assert WindowsApplicationResolver._score("games", "Epic Games Launcher") == 90


def test_deduplicate_keeps_unique_launch_entries():
    first = ApplicationCandidate("1", "Example", r"C:\Apps\Example.lnk", "start_menu")
    duplicate = ApplicationCandidate("2", "Example", r"C:\Apps\Example.lnk", "start_menu")
    second = ApplicationCandidate("3", "Example", r"C:\Apps\Example2.lnk", "start_menu")
    result = WindowsApplicationResolver._deduplicate([first, duplicate, second])
    assert result == (first, second)


def test_non_windows_discovery_is_safe_and_empty(monkeypatch):
    monkeypatch.setattr("omnisense_ai.application_discovery.os.name", "posix")
    resolver = WindowsApplicationResolver()
    assert resolver.discover() == ()
    assert resolver.is_trusted_target("/tmp/example.exe") is False
