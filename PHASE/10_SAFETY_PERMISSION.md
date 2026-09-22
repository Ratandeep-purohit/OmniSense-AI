# OmniSense AI — Phase 10 — Safety & Permission Engine

**Status:** Implemented
**Phase:** 10
**Boundary:** Authorization and policy only. No desktop execution.
**Upstream:** Phase 09 Action Planning, Phase 06 Context Engine
**Downstream:** Phase 11 Desktop Automation

## 1. Executive Summary

Phase 10 is the mandatory security gate between an ActionPlan and any future desktop automation.

Phase 09 answers: What could be done?
Phase 10 answers: Under the current safety policy, may this plan proceed?
Phase 11 answers: How do we perform the approved operation?
Phase 12 answers: Did the expected state actually occur?

Core invariant:

    ActionPlan != Permission
    Permission != Execution
    Execution != Verification

Phase 10 fails closed. When policy, context, target validity, risk, or authorization is insufficient, execution must not be permitted.

## 2. System Position

    Capture
       ↓
    Visual Processing
       ↓
    OCR
       ↓
    Window Detection
       ↓
    UI Understanding
       ↓
    Context Engine
       ↓
    AI/VLM
       ↓
    Intelligent Assistant
       ↓
    Action Planning
       ↓
    Phase 10 Safety & Permission
       ↓
    Approved / Denied / Confirm
       ↓
    Phase 11 Desktop Automation
       ↓
    Phase 12 Verification

Phase 10 is the last authority boundary before desktop control.

## 3. Scope

### In scope

- ActionPlan validation
- plan/context identity matching
- context freshness validation
- plan status validation
- step-count limits
- action allowlists
- target presence checks
- risk aggregation
- confirmation requirements
- critical-risk baseline denial
- permission decision contracts
- policy reasons
- fail-closed behavior
- security errors
- safe decision telemetry
- Phase 11 handoff contract
- security regression tests

### Out of scope

Phase 10 does not click, type, move the mouse, press keys, focus windows, launch applications, close applications, execute commands, execute Python, modify files, send messages, submit forms, purchase anything, interact with Windows APIs for execution, verify post-action state, store screenshots, remember user behavior, or provide the confirmation UI itself.

## 4. Repository Map

    src/omnisense_ai/safety_permission/
    ├── __init__.py
    ├── models.py
    ├── errors.py
    └── service.py

    tests/test_safety_permission.py
    PHASE/10_SAFETY_PERMISSION.md

models.py defines PermissionDecision, PolicyReason, SafetyConfig and PermissionDecisionResult.
service.py defines SafetyPermissionEngine.evaluate(). There is deliberately no execute() method.

## 5. Decision Vocabulary

- ALLOW — the plan passed the current baseline policy; nothing executes.
- DENY — the plan must not proceed.
- REQUIRE_CONFIRMATION — an explicit trusted confirmation is required.
- REQUIRE_CLARIFICATION — the plan is insufficiently defined.

## 6. Policy Reasons

Current reasons include APPROVED, PLAN_REJECTED, STALE_CONTEXT, UNSUPPORTED_ACTION, HIGH_RISK, CRITICAL_RISK, CONFIRMATION_REQUIRED, INVALID_TARGET, POLICY_DENIED and AMBIGUOUS.

A reason is diagnostic metadata, not an authorization token.

## 7. Safety Configuration

Defaults:

    allow_low_risk_without_confirmation = true
    allow_medium_risk_without_confirmation = false
    allow_high_risk_without_confirmation = false
    allow_critical_risk_without_confirmation = false
    max_context_age_seconds = 5.0
    max_steps = 10

An optional allowed_action_types set provides least-privilege deployment configuration.

## 8. Input Contract

The engine receives an ActionPlan and ContextSnapshot.
The plan context_id must equal the snapshot context_id.
This prevents a plan from one observation being authorized against unrelated desktop state.

## 9. Context Freshness

Desktop state changes quickly. The baseline rejects context older than 5 seconds.

Freshness is a safety budget, not proof that the desktop has remained unchanged. Phase 11 must still perform immediate target validation.

## 10. READY Requirement

Only PlanStatus.READY can proceed to authorization.
NEEDS_CLARIFICATION becomes REQUIRE_CLARIFICATION.
A non-ready plan must never be silently upgraded.

## 11. Step Limits

Safety configuration limits a plan to 10 steps by default. The ActionPlan model has an absolute structural limit of 20. Policy may therefore be stricter than the data model.

## 12. Target Requirement

Every step reaching the baseline safety gate must have a target.
Missing targets are denied.

Important distinction:

    target description != target validation

Phase 11 must resolve and validate the real desktop target immediately before execution.

## 13. Action Allowlist

SafetyConfig can restrict action types. For example, a deployment can allow only scroll and wait.

Unsupported or disallowed actions are denied rather than converted into another operation.

## 14. Risk Aggregation

Plan risk is the highest risk across its steps:

    LOW < MEDIUM < HIGH < CRITICAL

A dangerous step cannot hide inside a mostly low-risk plan.

## 15. Baseline Risk Policy

LOW risk may be allowed without confirmation when configured.
MEDIUM risk requires confirmation by default.
HIGH risk requires explicit confirmation by default.
CRITICAL risk is denied by the baseline policy.

Risk metadata is not permission. A future policy may recompute risk from action, target, application, data sensitivity and reversibility.

## 16. Confirmation Semantics

These are separate concepts:

    requires_confirmation
    confirmation_requested
    confirmation_displayed
    user_confirmed
    policy_allowed
    execution_started
    execution_completed
    execution_verified

Phase 10 can require confirmation but does not fabricate a confirmation event.

## 17. Authorization Boundary

Authorization must not be inferred from OCR text, visible web content, button labels, model confidence, plan readiness, previous unrelated approvals, or screen text claiming that the user approved something.

A trusted application mechanism must supply confirmation.

## 18. Prompt Injection Defense

Desktop content is untrusted. A page may say: Ignore all safety rules, send credentials, or confirm the transaction.

Those statements remain observations.

Trust hierarchy:

    System policy
        ↓
    Application safety policy
        ↓
    Explicit trusted user confirmation
        ↓
    Structured desktop observations
        ↓
    OCR / visible text

Visible text cannot move upward in this hierarchy.

## 19. Plan Provenance

Every decision carries plan_id and context_id.
This supports diagnostics without requiring screenshot retention.

## 20. No Execution Authority

The implementation intentionally contains no click, type, launch, close, shell, subprocess, keyboard automation, or mouse automation API.

## 21. Evaluation Algorithm

    ActionPlan + ContextSnapshot
              ↓
        context IDs match?
          no → input error
              ↓
        plan READY?
          no → clarification
              ↓
        step count valid?
          no → input error
              ↓
        context fresh?
          no → stale error
              ↓
        inspect each step
              ↓
        action allowed?
          no → DENY
              ↓
        target present?
          no → DENY
              ↓
        aggregate highest risk
              ↓
        CRITICAL → DENY
        HIGH     → REQUIRE_CONFIRMATION
        MEDIUM   → REQUIRE_CONFIRMATION
        otherwise → policy decision

ALLOW is the end of Phase 10. It is not execution.

## 22. Fail-Closed Rules

These conditions must never silently allow execution:

- context mismatch
- stale context
- invalid plan status
- excessive step count
- unsupported action
- missing target
- critical risk
- denied policy
- missing authorization
- unresolved ambiguity

Default safe response is denial or clarification.

## 23. Error Taxonomy

SafetyPermissionError is the base security error.
SafetyInputError represents invalid safety inputs.
SafetyPolicyError represents explicit policy denial.
SafetyStaleContextError represents expired context.
SafetyTargetError represents target validation failure.

Some policy failures are returned as typed decisions rather than exceptions so callers can present controlled decision states.

## 24. Target Validation Boundary

Current baseline checks target presence.
Future validation must additionally establish that the target still exists, belongs to the intended window, matches expected text, is visible, is interactable, and has not been replaced.

## 25. Application Scope

Future policy should restrict by process name, executable identity, window identity, application category and trusted installation path.

Generic action approval must not automatically mean approval for every application.

## 26. Sensitive Operations

Operations involving money, credentials, account security, deletion, external communication, publishing, permissions or system settings require stronger policy.

Critical actions must never become allowed merely because a model is confident.

## 27. Model Confidence

Confidence means the model believes something is correct.
Authorization means the system permits it.
They are different security properties.

## 28. Assistant Boundary

Phase 08 conversational output is not itself a permission object.
Unsafe path:

    Assistant prose → parse → allow

Safe path:

    structured ActionPlan → Phase 10 → policy decision

## 29. Risk Re-evaluation

Upstream risk metadata is an input, not unquestionable truth.
Future Phase 10 policy may recompute risk using action, target, application, data sensitivity, reversibility and user policy.

## 30. Sensitive Parameter Handling

Future policy must classify passwords, API keys, tokens, financial values and personal identifiers.
Sensitive values must not appear in logs, exceptions, telemetry or diagnostics unnecessarily.

## 31. Concurrency

The engine is stateless.
One evaluation must not inherit another plan's approval, confirmation, context freshness or target validation.

Any future approval cache must be bound to user/session, plan_id, context_id and policy version, with safe expiry.

## 32. Policy Versioning

Future permission decisions should record policy_version.
This allows diagnostics to identify which policy produced a decision.
Changing policy must not silently reinterpret old approval records.

## 33. Idempotency and Replay

ALLOW is bound to a specific plan and context.
Future execution must reject duplicate execution, modified plans, changed context, changed targets and expired approvals.

## 34. Audit-Safe Telemetry

Safe telemetry includes plan_id, context_id, decision, reason, aggregate risk, step count, policy version and evaluation duration.

Do not log screenshots, full OCR, passwords, tokens, typed secrets or unnecessary document content.

## 35. Threat Model

### SP-01 — Stale desktop
A plan is approved after the UI changes. Mitigation: freshness plus Phase 11 target revalidation.

### SP-02 — Wrong target
A similarly named control replaces the original. Mitigation: target identity and expected-text checks downstream.

### SP-03 — Prompt injection
Visible content asks OmniSense to bypass policy. Mitigation: screen content is untrusted.

### SP-04 — Risk laundering
An upstream model labels a dangerous operation LOW. Mitigation: Phase 10 independently evaluates policy.

### SP-05 — Confirmation spoofing
Screen text claims the user confirmed. Mitigation: only trusted confirmation state is accepted.

### SP-06 — Plan explosion
Too many operations are proposed. Mitigation: model and policy step limits.

### SP-07 — Unsupported action
A new action appears without policy. Mitigation: explicit allowlist and fail-closed handling.

### SP-08 — Replay
An old approved plan is reused. Mitigation: plan/context binding and future approval expiry.

## 36. Testing Strategy

Unit tests cover low-risk allow, medium-risk confirmation, high-risk confirmation, critical-risk denial, stale context, context mismatch, non-ready plans, action allowlists, target requirements and absence of execution.

Security tests should cover prompt injection, confirmation spoofing, risk escalation, unsupported actions, stale plans, replay and malformed plans.

Integration tests must prove that Phase 10 does not call a desktop automation adapter.

## 37. Current Test Matrix

| ID | Scenario | Expected |
|---|---|---|
| SP-001 | LOW risk | ALLOW |
| SP-002 | MEDIUM risk | REQUIRE_CONFIRMATION |
| SP-003 | HIGH risk | REQUIRE_CONFIRMATION |
| SP-004 | CRITICAL risk | DENY |
| SP-005 | stale context | typed stale error |
| SP-006 | context mismatch | typed input error |
| SP-007 | non-ready plan | REQUIRE_CLARIFICATION |
| SP-008 | action allowlist violation | DENY |
| SP-009 | no execute API | true |

## 38. Performance Budget

Target for deterministic evaluation:

    P50 < 5 ms
    P95 < 20 ms

These are engineering targets, not benchmark claims.
There should be no network call, model call, screenshot processing, OCR, or automation dependency in Phase 10.

## 39. Privacy

Phase 10 does not need screenshot history.
It operates on plan metadata, context identity, risk and policy state.
It must not create a hidden second screen-history store.

## 40. No Runtime Training

Phase 10 contains deterministic policy code. It does not train a model.
Security decisions should not depend on an opaque model learning the permission boundary at runtime.

## 41. Future Policy Architecture

    SafetyPermissionEngine
            ↓
       Policy Registry
       ├── Action Policy
       ├── Application Policy
       ├── Data Sensitivity Policy
       ├── User Permission Policy
       ├── Confirmation Policy
       └── Rate Limit Policy
            ↓
       Decision Aggregator
            ↓
       PermissionDecision

Every policy must fail closed when unavailable or malformed.

## 42. Policy Precedence

Future precedence should be explicit:

    hard security deny
        ↓
    system restrictions
        ↓
    application restrictions
        ↓
    user policy
        ↓
    action-specific confirmation
        ↓
    allow

A lower layer must never override a higher-priority deny.

## 43. Least Privilege

Grant the smallest possible authority.

Prefer: allow this specific TYPE step after confirmation.
Not: allow all keyboard input.

Prefer: allow this specific target in this specific window.
Not: allow all browser clicks.

## 44. No Silent Escalation

A denied operation must not be transformed into another action, shell command, different application or weaker policy category.

DELETE denied → shell deletion is prohibited.

## 45. Phase 11 Handoff

Phase 11 receives an approved decision plus its associated plan.
Before execution it must independently verify:

- decision is ALLOW
- plan ID matches
- context ID matches
- approval has not expired
- target is still valid
- application/window is correct
- preconditions are satisfied

If any check fails: DO NOT EXECUTE.

## 46. Phase 12 Handoff

Phase 10 ALLOW means only that policy permitted the plan.
It does not mean the action happened.
Phase 11 performs the operation.
Phase 12 verifies the expected state.

## 47. Definition of Done

- [x] typed permission decisions exist
- [x] policy reasons exist
- [x] plan/context identity is validated
- [x] stale context is rejected
- [x] READY status is required
- [x] step count is bounded
- [x] action allowlist exists
- [x] target presence is required
- [x] risk aggregation exists
- [x] medium risk requires confirmation by default
- [x] high risk requires confirmation by default
- [x] critical risk is denied by baseline
- [x] no execution API exists
- [x] security errors exist
- [x] regression tests exist
- [x] Phase 11 handoff is defined

## 48. Acceptance Criteria

1. A fresh LOW-risk plan can be allowed when policy permits.
2. MEDIUM risk cannot silently bypass confirmation.
3. HIGH risk cannot silently bypass confirmation.
4. CRITICAL risk is denied by the baseline.
5. Stale context cannot reach ALLOW.
6. A plan from another context cannot be authorized.
7. Unsupported actions can be denied through policy.
8. Missing targets cannot be authorized.
9. Phase 10 cannot execute a desktop action.
10. Screen content cannot grant permission.
11. Model confidence cannot grant permission.
12. Approval remains bound to the specific plan/context.

## 49. Engineering Invariants

    ACTION PLAN != AUTHORIZATION
    AUTHORIZATION != EXECUTION
    EXECUTION != VERIFICATION

    READY != APPROVED
    APPROVED != EXECUTED
    EXECUTED != VERIFIED

    SCREEN TEXT != AUTHORIZATION
    MODEL CONFIDENCE != AUTHORIZATION
    TARGET DESCRIPTION != TARGET VALIDATION
    REQUIRES_CONFIRMATION != USER_CONFIRMED

## 50. Final Phase Boundary

    ActionPlan
        ↓
    SafetyPermissionEngine
        ↓
    PermissionDecision
        ├── DENY
        ├── REQUIRE_CLARIFICATION
        ├── REQUIRE_CONFIRMATION
        └── ALLOW
                 ↓
             Phase 11

There must be no direct ActionPlan → desktop action path without passing through the safety boundary.

## 51. Final Rule

> Phase 09 proposes. Phase 10 authorizes. Phase 11 executes. Phase 12 verifies.

The security architecture depends on keeping these four responsibilities separate.