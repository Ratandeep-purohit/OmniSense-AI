# OmniSense AI — Phase 11 — Desktop Automation

**Status:** Implemented baseline  
**Phase:** 11  
**Boundary:** Execute only an explicitly authorized ActionPlan.  
**Upstream:** Phase 10 Safety & Permission  
**Downstream:** Phase 12 Action Verification

## 1. Purpose

Phase 11 is the first phase that may cross from structured authorization into actual desktop input.

The mandatory chain is:

ActionPlan → Phase 10 PermissionDecision → Phase 11 DesktopAutomationService → platform adapter → execution result → Phase 12 verification.

Phase 11 MUST NOT create authorization, infer authorization from screen content, execute assistant prose, or bypass Phase 10.

## 2. Core Invariants

- DENY never executes.
- REQUIRE_CONFIRMATION never executes.
- REQUIRE_CLARIFICATION never executes.
- Only ALLOW reaches the backend.
- Plan ID and context ID must match.
- Every executed step must be explicitly present in approved_step_ids.
- Missing target information fails closed.
- Execution is bounded by configuration.
- Desktop backend failures are typed.
- Execution success is not proof of the desired UI state.

## 3. Repository

```
src/omnisense_ai/desktop_automation/
├── __init__.py
├── models.py
├── errors.py
├── backend.py
└── service.py

tests/test_desktop_automation.py
PHASE/11_DESKTOP_AUTOMATION.md
```

## 4. Data Contracts

### AutomationConfig

Controls:

- enabled state
- maximum steps
- action timeout budget
- maximum typed text length
- maximum scroll amount
- optional application allowlist

The default is disabled. This is intentional: installing OmniSense must not silently activate desktop control.

### AutomationRequest

Binds:

- plan_id
- context_id
- Phase 10 PermissionDecisionResult

### ActionExecution

Records:

- step ID
- action type
- execution status
- start timestamp
- finish timestamp
- bounded result message

### AutomationResult

Records:

- execution ID
- plan ID
- context ID
- aggregate execution status
- individual step results
- execution timestamps

## 5. Authorization Gate

Before the first desktop call, the service verifies:

1. automation is enabled;
2. request plan ID matches the ActionPlan;
3. request context ID matches the ActionPlan;
4. decision plan ID matches;
5. decision context ID matches;
6. decision is ALLOW;
7. plan step count is within the Phase 11 limit;
8. every plan step is explicitly approved.

Any failure stops execution before the backend is touched.

## 6. Default Safety

The default backend is NullDesktopAutomationBackend.

It never:

- moves the mouse;
- clicks;
- types;
- presses keys;
- launches applications;
- closes applications;
- executes commands.

A real backend must be explicitly configured.

## 7. Platform Adapter

DesktopAutomationBackend is the platform boundary.

The service knows only the adapter contract. Tests can inject a fake backend.

The optional PyAutoGUI adapter currently implements:

- CLICK
- MOVE
- TYPE
- HOTKEY
- SCROLL
- WAIT

It deliberately does not implement OPEN_APP or CLOSE_APP.

## 8. CLICK

CLICK requires integer x/y parameters.

Coordinates are bounded to 0..10000.

A missing coordinate is an execution-target error.

The adapter must never search arbitrary OCR text or interpret a webpage instruction as a click command.

## 9. MOVE

MOVE requires bounded integer x/y coordinates.

MOVE is not permission to click.

## 10. TYPE

TYPE requires a text parameter.

Text is bounded by max_text_length.

Generic keyboard injection MUST NOT be treated as a safe mechanism for passwords, API keys, payment credentials or other sensitive data. A future secure-input design is required for those cases.

## 11. HOTKEY

HOTKEY requires a non-empty plus-separated key list.

The adapter sends only the specified keys.

No shell syntax is interpreted.

## 12. SCROLL

SCROLL accepts a bounded integer amount.

Unbounded loops are prohibited.

## 13. WAIT

WAIT accepts seconds in the range 0..30.

Waiting does not grant additional permission.

## 14. OPEN_APP / CLOSE_APP

These operations can have significant side effects.

They are intentionally not implemented by the current adapter.

A future implementation MUST require:

- application allowlisting;
- canonical executable identity;
- explicit Phase 10 policy;
- no arbitrary shell parsing;
- bounded lifecycle operations.

## 15. Target Binding

A target description is not a target guarantee.

Current baseline validation requires explicit coordinates for coordinate actions.

Production target validation should additionally establish:

- intended monitor;
- intended window;
- UI element identity;
- expected text;
- visibility;
- interactability;
- current geometry;
- foreground-window identity.

This validation should happen immediately before input.

## 16. Context Freshness

Phase 10 checks context freshness.

Phase 11 must assume that desktop state may still have changed between authorization and execution.

Therefore Phase 11 MUST NOT treat an old context ID as proof that the current screen is unchanged.

Phase 12 provides post-action verification; future Phase 11 hardening should add pre-action target revalidation.

## 17. Focus Safety

CLICK, TYPE and HOTKEY are sensitive to foreground focus.

The current adapter does not claim to prove focus correctness.

Production execution should verify the intended window immediately before sensitive input.

## 18. Prompt Injection Boundary

Screen text is data, not authority.

Examples such as:

- "Ignore safety rules"
- "Click here immediately"
- "Confirm payment"
- "Send the password"

must never become execution instructions.

Phase 11 consumes structured ActionStep data only.

## 19. No Shell Authority

Phase 11 has no generic:

- cmd.exe;
- PowerShell;
- subprocess;
- arbitrary Python;
- shell string;
- filesystem deletion;

execution interface.

A denied desktop operation must not be transformed into a shell command.

## 20. Cancellation

The service accepts an optional cancellation Event.

Cancellation is checked before each step.

If cancellation is set, the next step is not executed.

Mid-action cancellation depends on the platform adapter and must not be falsely reported as instantaneous.

## 21. Concurrency

Execution is serialized per service instance.

Two plans must not concurrently drive the same adapter through one service instance.

A future application-level scheduler should enforce one active desktop transaction per user desktop session.

## 22. Retry Policy

There is no automatic retry in the baseline.

CLICK, TYPE and HOTKEY are not assumed idempotent.

A future retry policy must be action-specific and must never replay sensitive or externally consequential operations blindly.

## 23. Partial Execution

A multi-step plan may fail after earlier steps have completed.

The baseline stops on the first backend failure rather than pretending all later steps succeeded.

Future execution receipts should preserve completed-step evidence and report PARTIAL explicitly.

Rollback is not automatically inferred.

## 24. Error Taxonomy

- AutomationDisabledError
- AutomationAuthorizationError
- AutomationInputError
- AutomationTargetError
- AutomationBackendError
- AutomationTimeoutError
- AutomationCancelledError

Error messages must not expose secrets or full screen contents.

## 25. Resource Limits

Execution is bounded by:

- maximum steps;
- typed-text length;
- coordinate range;
- scroll amount;
- wait duration;
- future per-action deadlines.

These are security controls as well as resource controls.

## 26. Sensitive Data

Telemetry and exceptions must not contain:

- passwords;
- access tokens;
- API keys;
- financial credentials;
- unnecessary personal data;
- full screenshots;
- full OCR dumps.

Sensitive typing requires a future explicit policy and secure input mechanism.

## 27. Telemetry

Safe execution telemetry should contain:

- execution ID;
- plan ID;
- context ID;
- step ID;
- action type;
- status;
- duration.

It should not contain raw desktop pixels or sensitive typed content.

## 28. Testing Strategy

Unit tests use fake backends.

Required tests include:

- disabled execution;
- DENY cannot execute;
- identity mismatch;
- approved action execution;
- missing CLICK coordinates;
- cancellation;
- excessive steps;
- missing target;
- backend failure mapping;
- approved-step mismatch;
- default backend remains inert.

Real Windows integration tests should be opt-in and isolated from normal CI.

## 29. Phase 12 Contract

Phase 11 reports what the adapter attempted and what it returned.

It does not prove:

- the intended button was clicked;
- the intended text appeared;
- the correct application changed;
- a transaction completed;
- the expected state was reached.

Phase 12 must obtain fresh evidence and verify postconditions.

## 30. Acceptance Criteria

Phase 11 is complete when:

- [x] Phase 10 ALLOW is mandatory;
- [x] plan/context identity is enforced;
- [x] approved step IDs are enforced;
- [x] target parameters are bounded;
- [x] automation is disabled by default;
- [x] a real backend is optional;
- [x] no shell execution exists;
- [x] cancellation is supported;
- [x] typed failures exist;
- [x] unit tests use a fake backend;
- [x] Phase 12 handoff is explicit.

## 31. Engineering Rule

Phase 10 authorizes.

Phase 11 executes exactly what was authorized.

Phase 12 verifies what actually happened.

```
Phase 09 → ActionPlan
Phase 10 → PermissionDecision
Phase 11 → ExecutionResult
Phase 12 → VerificationResult
```
