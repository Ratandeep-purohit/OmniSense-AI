# Windows Compatibility Matrix

| Application | Discovery | Identity | Launch | Verification | Semantic UIA |
|---|---|---|---|---|---|
| Notepad | Required | Process/window | Windows-owned target | Required | Target-dependent |
| Calculator | Required | Packaged/process identity | AUMID/Start Menu | Required | Target-dependent |
| Word | Required | WINWORD.EXE/window | Start Menu | Required | UIA preferred |
| Excel | Required | EXCEL.EXE/window | Start Menu | Required | UIA preferred |
| PowerPoint | Required | POWERPNT.EXE/window | Start Menu | Required | UIA preferred |
| Chrome | Required | chrome.exe/window | Start Menu | Required | UIA dependent on exposed controls |
| Edge | Required | msedge.exe/window | Start Menu | Required | UIA dependent on exposed controls |
| VS Code | Required | code.exe/window | Start Menu | Required | UIA dependent on exposed controls |
| Steam | Required | steam.exe/window | Start Menu | Required | Adapter may be required |
| Epic Games Launcher | Required | EpicGamesLauncher.exe/window | Start Menu | Required | Adapter may be required |
| Explorer | Required | explorer.exe/window | Windows shell | Required | UIA supported where exposed |

A row marked Required is a release criterion, not a claim that every installed version exposes identical UI Automation controls. The real Windows E2E suite must record discovered identity, launch behavior and verification evidence per machine.
