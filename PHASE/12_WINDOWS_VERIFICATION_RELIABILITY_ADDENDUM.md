# Windows Verification Reliability Addendum

## Purpose
This addendum records the production-oriented verification changes that close the gap between automation success and demonstrable Windows application state.

## Problem
Foreground-window-only verification is insufficient for real Windows launch behavior. Applications may launch without immediately owning the foreground window, hand off from a bootstrapper/updater, expose a delayed top-level window, or change foreground ownership during startup.

A successful desktop launch call is therefore not proof of application success.

## Architecture
User Intent -> Application Discovery -> Canonical Application Identity -> Action Plan -> Safety -> Trusted Launch -> Windows State Observation -> Visible Top-Level Window Matching -> Canonical Application Identity Verification

Launch plans carry the discovered application_id as their expected postcondition instead of encoding a developer-maintained process allowlist into the planner.

## Read-only Windows observation
The Windows window backend now exposes foreground observation, visible top-level window enumeration, process ID, process name, executable path, window title, visibility, foreground state, and monitor identity.

Enumeration is observational only. It does not focus, move, close, or launch windows.

## Temporal verification
After execution, OmniSense polls for a bounded interval and evaluates the complete visible-window set. A matching background window is valid evidence when the requested application is not foreground. Foreground matches are preferred when multiple matching windows exist.

## Matching policy
For applications with a discovered process identity, the observed process must match the discovered process.

For Start Menu applications without a process identity, normalized display-name matching against the window title is preferred. Otherwise meaningful token overlap between application display name and observed title/process name is required.

Unrelated applications are rejected.

The verifier never converts execution success directly into verified success.

## Epic Games Launcher regression
Epic Games Launcher exposed the original design weakness: the application could visibly launch while foreground-only verification failed. The production path now observes the complete visible Windows window set and binds the evidence to the discovered application identity.

## Testing
Regression coverage includes visible background application windows, unrelated-window rejection, canonical application identity expectations, visible-window backend enumeration, and application identity verification.

Real Windows smoke testing is still required on the target machine because repository tests cannot reproduce every installed-application and Windows-shell configuration.