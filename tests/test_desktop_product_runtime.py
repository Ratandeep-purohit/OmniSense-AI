from omnisense_ai.application_discovery import ApplicationCandidate
from omnisense_ai.desktop_product_runtime import DesktopProductRuntime
from omnisense_ai.window_detection.models import WindowInfo, WindowRect, WindowState


def make_window(title, process="EpicGamesLauncher.exe", foreground=False):
    return WindowInfo(
        hwnd=101,
        title=title,
        process_id=5001,
        process_name=process,
        executable_path=r"C:\Program Files\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe",
        rect=WindowRect(0, 0, 1200, 800),
        monitor_id="1",
        state=WindowState.ACTIVE,
        is_visible=True,
        is_foreground=foreground,
    )


def test_epic_launcher_can_verify_from_visible_background_window():
    candidate = ApplicationCandidate(
        application_id="startmenu:epic",
        display_name="Epic Games Launcher",
        launch_target=r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Epic Games Launcher.lnk",
        source="start_menu",
    )
    window = make_window("Epic Games Launcher", foreground=False)
    assert DesktopProductRuntime._window_matches(window, candidate, set(), "") is True


def test_unrelated_window_does_not_verify_discovered_application():
    candidate = ApplicationCandidate(
        application_id="startmenu:epic",
        display_name="Epic Games Launcher",
        launch_target=r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Epic Games Launcher.lnk",
        source="start_menu",
    )
    window = make_window("Steam", process="steam.exe")
    assert DesktopProductRuntime._window_matches(window, candidate, set(), "") is False
