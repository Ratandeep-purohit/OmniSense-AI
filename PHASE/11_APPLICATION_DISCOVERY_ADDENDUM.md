# Phase 11 — Dynamic Windows Application Discovery Addendum

## Purpose

OmniSense no longer maintains a developer-authored execution allowlist such as word, steam, or epic. Application launch requests are resolved against Windows-owned application entry points at runtime.

## Architecture

User: open epic
  -> ActionPlanner
  -> WindowsApplicationResolver
     -> Start Menu .lnk entries
     -> HKCU/HKLM App Paths
  -> ApplicationCandidate
  -> Phase 10 Safety / Permission
  -> WindowsDesktopBackend
     -> re-discover + validate exact launch target
     -> os.startfile(trusted target)
  -> Phase 12 verification

## Why this scales

Adding a normal installed desktop application does not require a source-code change. If Windows exposes the application through a Start Menu shortcut or an App Paths registration, OmniSense can discover it by name.

Examples include browsers, developer tools, game launchers, media applications, Office applications, and other normally installed desktop software.

## Trust boundary

Dynamic discovery does not mean arbitrary executable execution.

The backend accepts only a launch target that is currently rediscoverable from the user's Start Menu Programs folder, the common Start Menu Programs folder, or Windows App Paths registry entries under HKCU/HKLM.

User text cannot directly supply an executable path, shell command, PowerShell command, or command-line string.

The exact discovered target is revalidated immediately before execution.

## Resolution behavior

The resolver normalizes application names and scores exact display-name match, substring match, complete token-set match, and single-token match.

If equally strong unrelated candidates exist, the resolver refuses to guess and the planner returns NEEDS_CLARIFICATION.

## Verification

For applications with a known executable identity, Phase 12 uses app_is_any:<process>.

For Start Menu shortcuts where the process identity is not directly available, the planner uses a bounded window_title_contains:<display name> expectation.

Verification remains post-execution and does not grant additional authority.

## Important limitation

Packaged Windows applications are also discovered through AUMID registry entries and launched through the Windows AppsFolder shell namespace. The AUMID target is revalidated before execution.

Applications that expose none of these Windows-owned entry points remain unresolved rather than falling back to arbitrary executable paths.

## Acceptance criteria

- No production per-application allowlist is required for launch discovery.
- Start Menu application shortcuts are discovered dynamically.
- HKCU/HKLM App Paths are discovered dynamically.
- Launch targets are revalidated immediately before execution.
- Arbitrary executable paths are rejected.
- Shell/PowerShell command execution is not introduced.
- Existing Phase 10 permission and Phase 12 verification boundaries remain.
- Resolver behavior has deterministic unit-test coverage.