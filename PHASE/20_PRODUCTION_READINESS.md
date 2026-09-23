# OmniSense AI — Production Readiness Batch

This batch establishes the production engineering spine across Windows identity, discovery, adapters, native UI Automation, semantic targeting, action graphs, preconditions, capabilities, temporal verification direction, recovery, observability, E2E harnessing, packaging, diagnostics, compatibility and smoke tests.

## Non-negotiable boundary

AI proposes. Planning structures. Safety authorizes. Capability grants authority. Automation performs. Verification proves. Recovery may re-observe or re-plan, but never silently re-authorizes or retries a failed desktop action.

## Windows matrix

The real smoke matrix is Notepad, Calculator, Word, Excel, PowerPoint, Chrome, Edge, VS Code, Steam, Epic Games Launcher and Explorer. Discovery failures are surfaced as unsupported/needs-clarification; they are not converted into arbitrary executable paths.

## UI automation

The native semantic layer uses Microsoft UI Automation through pywinauto's UIA backend when installed. Coordinate automation remains a bounded fallback and is never treated as semantic proof.

## Verification

Application identity is canonical. Post-action verification matches the discovered identity and visible Windows state. The next hardening step is pre-action snapshot + temporal state transition for every executable action.

## Recovery

Recovery is deliberately conservative: re-observe, re-plan, ask the user, or stop. There is no silent retry after a desktop mutation.

## Packaging

PyInstaller and Inno Setup definitions are included. The installer is intentionally not considered release-complete until a clean Windows VM smoke test validates install, launch, upgrade, uninstall and rollback behavior.
