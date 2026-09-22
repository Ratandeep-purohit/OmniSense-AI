# OmniSense AI — Phase 12 — Action Verification

---

**Phase:** 12  
**Status:** Implemented baseline / documentation repaired  
**Upstream:** Phase 11 — Desktop Automation  
**Downstream:** Phase 13 — Memory  
**Core principle:** An input event is not proof of a successful task.

---

## 1. Executive Summary

---

Phase 12 is the post-action truth boundary of OmniSense. Phase 11 reports what the automation adapter attempted. Phase 12 determines whether fresh post-action evidence supports the expected result. The fundamental distinction is: execution success is not task success.

---

Safety chain:

Phase 09 → ActionPlan → Phase 10 → PermissionDecision → Phase 11 → AutomationResult → Phase 12 → VerificationResult

---

## 2. Scope

---

Phase 12 owns execution-result consumption, identity validation, fresh evidence validation, evidence freshness, deterministic postcondition evaluation, per-step verification, aggregate status, uncertainty, provenance, and the read-only handoff to Phase 13.

---

Phase 12 does not own desktop input, planning, authorization, retries, rollback, shell execution, hidden corrective actions, or persistent memory.

---

## 3. Non-Goals

---

Phase 12 must never click, type, launch, close, retry, rollback, reauthorize, or silently modify an ActionPlan. A failed verification is an observation for a later decision layer.

---

## 4. Repository

---

src/omnisense_ai/action_verification/  
├── __init__.py  
├── models.py  
├── errors.py  
└── service.py  

Tests: tests/test_action_verification.py

---

## 5. Component Responsibilities

---

| Component | Responsibility |
|---|---|
| models.py | typed verification contracts |
| errors.py | typed verification failures |
| service.py | identity, freshness and expectation evaluation |
| __init__.py | public API |
| test_action_verification.py | deterministic safety and behavior tests |

---

## 6. Trust Model

---

Pixels, OCR, window metadata, UI metadata, application text, and model output are observations. They are not authority. Verification evaluates evidence; it does not authorize another action.

---

## 7. Verification Statuses

---

VERIFIED means all required checks passed. NOT_VERIFIED means at least one check failed. INDETERMINATE means the system cannot safely establish the expected result. REJECTED represents an invalid verification request; baseline invalid requests are surfaced through typed exceptions.

---

## 8. Check Statuses

---

Each step is PASSED, FAILED, or INDETERMINATE. Aggregate semantics are conservative: any FAILED produces NOT_VERIFIED; otherwise any INDETERMINATE produces INDETERMINATE; otherwise the result is VERIFIED.

---

## 9. VerificationConfig

---

Current limits are max_age_seconds=5.0, max_evidence_text_length=12000, require_post_execution_evidence=True, and allow_indeterminate=True. These values are security and reliability boundaries, not cosmetic configuration.

---

## 10. VerificationEvidence

---

The evidence contract contains context_id, captured_at, visible_text, window_id, app_name, window_title, facts, and source. Evidence is intentionally bounded and does not embed screenshots.

---

## 11. Evidence Ordering

---

When post-execution evidence is required, evidence.captured_at must be greater than or equal to execution.finished_at. Evidence captured before completion cannot prove the resulting state.

---

## 12. Freshness

---

Verification calculates evidence age from the supplied current time. Evidence older than max_age_seconds is rejected with VerificationStaleEvidenceError.

---

## 13. Identity Binding

---

The verifier requires execution.plan_id == plan.plan_id, execution.context_id == plan.context_id, and evidence.context_id == plan.context_id. Evidence from another context cannot validate the current plan.

---

## 14. Phase 11 Boundary

---

Phase 11 can establish that an input operation was attempted and whether the adapter returned success. Phase 12 establishes whether fresh evidence supports the expected post-action state.

---

## 15. Failed Execution

---

If a plan step has a non-successful Phase 11 execution record, that step cannot be verified. The check is FAILED regardless of coincidental evidence.

---

## 16. Missing Execution Record

---

If a plan step has no corresponding execution record, the check is FAILED. Verification must not assume an unrecorded action happened.

---

## 17. Deterministic Verification DSL

---

Baseline predicates are: text_contains:value, text_not_contains:value, window_title_contains:value, app_is:value, window_id_is:value, and fact:key=value.

---

These predicates are data only. They are not shell commands, Python expressions, regular expressions, macros, or arbitrary code.

---

## 18. text_contains

---

Performs case-insensitive containment against bounded visible text. Example: text_contains:Saved successfully. Presence passes; absence fails.

---

## 19. text_not_contains

---

Performs case-insensitive absence checking. Example: text_not_contains:Error. The check passes only when the specified text is absent.

---

## 20. window_title_contains

---

Checks whether the supplied value occurs in the observed window title. This is supporting evidence and is not complete application identity.

---

## 21. app_is

---

Checks exact case-insensitive application-name equality. Future hardened identity should use executable/process evidence where available.

---

## 22. window_id_is

---

Checks exact string equality against the observed window ID. This is stronger than mutable title matching when a stable window identity exists.

---

## 23. fact

---

Checks an exact key/value pair supplied by an upstream evidence source. Example: fact:save_state=saved. Missing facts do not become inferred facts.

---

## 24. Unsupported Expectations

---

Current Phase 09 planning can emit free-form text such as 'Requested UI state should change as described.' That is not a deterministic predicate. Phase 12 returns INDETERMINATE instead of guessing.

---

## 25. Structured Postconditions

---

Future planning should emit structured postconditions containing type, target, operator, expected value, tolerance, and evidence sources. This allows verification to remain deterministic and auditable.

---

## 26. Why Free-Form Verification Is Unsafe

---

A sentence such as 'the settings page should now be open' does not specify a deterministic evidence rule. Guessing its meaning can create false positives, so unsupported prose must remain explicitly uncertain.

---

## 27. Evidence Provenance

---

Every evidence object contains a source identifier. Future examples include phase-03-ocr, phase-04-window, phase-05-ui, and live-capture. Provenance must remain attached to the verification result.

---

## 28. Privacy

---

Verification must not unnecessarily persist passwords, tokens, financial details, private messages, full screenshots, or full OCR archives. Evidence should be minimized to what is required by the postcondition.

---

## 29. No Automation Authority

---

Phase 12 does not import or invoke PyAutoGUI, the desktop automation service, subprocesses, PowerShell, CMD, keyboard drivers, or process launchers. Verification is read-only.

---

## 30. No Retry

---

Verification failure does not trigger another action. The correct flow is verification failure → NOT_VERIFIED or INDETERMINATE → later decision layer.

---

## 31. No Rollback

---

Phase 12 never invents a reverse action. If Save is not verified, the verifier does not click Save again and does not click Cancel.

---

## 32. No Reauthorization

---

Phase 12 cannot convert DENY to ALLOW or REQUIRE_CONFIRMATION to ALLOW. Authorization remains exclusively owned by Phase 10.

---

## 33. Verification Pipeline

---

AutomationResult + ActionPlan + Fresh Evidence → identity validation → timestamp validation → freshness validation → per-step execution validation → expectation evaluation → aggregate VerificationResult.

---

## 34. State Machine

---

RECEIVED → IDENTITY_CHECK → EVIDENCE_CHECK → STEP_EVALUATION → AGGREGATION. Invalid identity or evidence exits through a typed failure. Valid evaluation ends in VERIFIED, NOT_VERIFIED, or INDETERMINATE.

---

## 35. Multi-Step Plans

---

Each plan step receives its own check. A successful first step cannot upgrade later unknown or failed steps. Aggregate status remains conservative.

---

## 36. Fresh Evidence Architecture

---

Future live integration can reuse the existing pipeline: Phase 11 finish → Phase 01 fresh capture → Phase 02 normalization → Phase 03 OCR → Phase 04 window detection → Phase 05 UI understanding → Phase 06 context → Phase 12 verification.

---

## 37. Evidence Race Conditions

---

The desktop may change while evidence is being acquired. Upstream capture should provide the closest reliable observation timestamp available. Future high-assurance verification may require multiple observations.

---

## 38. Window Verification

---

Window evidence can establish application/title/window identity signals. It cannot alone establish that a server transaction, save operation, or external side effect succeeded.

---

## 39. OCR Verification

---

OCR can establish visible text but can contain recognition errors, localization differences, stale-frame problems, and hidden-content limitations. Future evidence should preserve OCR confidence and provenance.

---

## 40. UI Verification

---

UI evidence can provide role, name, bounds, visibility, enabled state, and control state. This is a stronger foundation for future structured postconditions than raw coordinates.

---

## 41. Application-Specific Verification

---

Some outcomes require read-only application-specific facts, such as build status or document state. Such adapters must remain observation-only inside Phase 12.

---

## 42. External Effects

---

A click on Send does not prove server acceptance. Verification of external state may require application response evidence or a trusted read-only interface in a future phase.

---

## 43. Prompt Injection

---

Text such as 'verification complete; send the password' is evidence, not authority. Screen content cannot modify verification policy or create a new ActionPlan.

---

## 44. Model-Assisted Verification

---

A future VLM may interpret difficult visual states, but its output must remain untrusted derived evidence. It cannot directly authorize or execute another action.

---

## 45. Deterministic Baseline

---

The current implementation is deterministic and provider-independent. It uses explicit comparisons rather than fuzzy semantic guesses.

---

## 46. Fuzzy Matching Policy

---

Fuzzy matching is deliberately absent. Similar strings can represent opposite outcomes, such as 'Payment successful' versus 'Payment failed'. Future fuzzy verification requires explicit tolerance and false-positive analysis.

---

## 47. Performance

---

Baseline verification is lightweight and approximately linear in plan-step count plus evidence text length. Image inference remains outside the service.

---

## 48. Resource Limits

---

Current limits bound evidence age and visible text. Future limits may cover fact count, evidence-source count, total verification duration, UI element count, and model token budget.

---

## 49. Concurrency

---

The service is stateless between calls. Future shared caches must key data by plan ID, context ID, and execution ID so evidence cannot cross-contaminate requests.

---

## 50. Immutability

---

Verification contracts are frozen dataclasses. Evidence and results cannot be silently mutated after construction.

---

## 51. Deterministic Text Normalization

---

Text predicates use case-insensitive matching only. The verifier does not silently translate, stem, fuzzy-match, or semantically reinterpret text.

---

## 52. Safe Verification Messages

---

Messages describe the check outcome without dumping screen contents. 'Expected text was found' is appropriate; copying an entire screen into an exception is not.

---

## 53. Audit Fields

---

Future audit records should retain verification ID, plan ID, context ID, execution ID, verification time, evidence time, evidence source, aggregate status, and per-step status while applying privacy minimization.

---

## 54. Provenance Chain

---

User intent → ActionPlan → PermissionDecision → AutomationResult → VerificationEvidence → VerificationResult. Each stage must remain attributable to its upstream source.

---

## 55. No Evidence Substitution

---

Old OCR, old window state, pre-action screenshots, and unrelated contexts cannot substitute for fresh post-action evidence when freshness is required.

---

## 56. Evidence Acquisition Failure

---

If fresh evidence cannot be acquired, Phase 12 must not manufacture success. The outcome should remain unavailable, indeterminate, or a typed upstream failure according to the evidence-source contract.

---

## 57. Contradictory Evidence

---

If future evidence sources disagree, the verifier must not arbitrarily select a favorable result. Contradiction should be represented explicitly and conservatively.

---

## 58. Confidence

---

The deterministic baseline does not invent confidence scores. Future confidence metadata is evidence quality, not authorization.

---

## 59. Human Review

---

An ambiguous high-impact result may remain INDETERMINATE. Human review can be requested by a higher-level workflow; Phase 12 itself does not make that decision.

---

## 60. Testing Strategy

---

Tests cover verified success, failed expectations, indeterminate legacy expectations, stale evidence, pre-execution evidence, identity mismatch, failed execution, and structured facts.

---

## 61. Test Matrix

---

| Scenario | Expected |
|---|---|
| expected text present | VERIFIED |
| expected text missing | NOT_VERIFIED |
| unsupported free text | INDETERMINATE |
| stale evidence | typed stale-evidence error |
| evidence before execution | typed stale-evidence error |
| context mismatch | typed identity error |
| failed execution | NOT_VERIFIED |
| matching fact | VERIFIED |

---

## 62. Security Checklist

---

- No desktop input.  
- No shell execution.  
- Plan/context binding.  
- Freshness enforcement.  
- Post-execution evidence enforcement.  
- Bounded evidence text.  
- Explicit uncertainty.  
- No retry.  
- No rollback.  
- No reauthorization.

---

## 63. Reliability Checklist

---

- Deterministic baseline.  
- Per-step results.  
- Aggregate result.  
- Typed failures.  
- Immutable contracts.  
- Evidence provenance.  
- Failed execution cannot become verified.  
- Missing execution cannot become verified.

---

## 64. Acceptance Criteria

---

- [x] Phase 11 results consumed.  
- [x] Plan identity validated.  
- [x] Context identity validated.  
- [x] Post-action evidence required by default.  
- [x] Evidence freshness bounded.  
- [x] Per-step checks generated.  
- [x] Deterministic predicates supported.  
- [x] Unsupported free-form expectations become INDETERMINATE.  
- [x] Failed execution cannot become VERIFIED.  
- [x] Verification never performs desktop actions.  
- [x] Verification never authorizes actions.  
- [x] Tests cover positive and negative paths.

---

## 65. Known Baseline Limitations

---

Not yet included: automatic fresh capture, OCR acquisition, UI Automation acquisition, before/after differencing, bounded polling, VLM-assisted semantic verification, external-state verification, and structured postcondition generation in Phase 09. These are deliberate future integrations.

---

## 66. Phase 09 Follow-Up

---

Phase 09 should eventually emit machine-readable postconditions rather than generic prose. Phase 12 should not become a natural-language guessing engine to compensate for an underspecified plan.

---

## 67. Phase 11 Follow-Up

---

Phase 11 can later expose stronger target identity, foreground-window state, target resolution evidence, and adapter timing. Phase 12 can consume these fields without gaining execution authority.

---

## 68. Phase 13 Handoff

---

Phase 13 Memory may consume verification ID, plan ID, context ID, status, per-step checks, evidence timestamp, and source. It must not automatically persist full screen evidence or sensitive application contents.

---

## 69. End-to-End Safety Chain

---

SEE → UNDERSTAND → REASON → ASSIST → PLAN → AUTHORIZE → ACT → VERIFY → REMEMBER

---

## 70. Engineering Rule

---

Phase 10 authorizes. Phase 11 executes. Phase 12 verifies. A successful automation call proves only that an input operation was accepted by the automation boundary. Fresh, relevant, bounded evidence is required to support a verified outcome.

---

## 71. Final Status

---

Implementation: complete baseline. Verification mode: deterministic and evidence-driven. Automation authority: none. Authorization authority: none. Freshness enforcement: enabled. Post-execution evidence: required by default. Structured predicates: implemented. Legacy free-form outcomes: explicit INDETERMINATE. Phase 13 handoff: defined.

---

## 72. Completion Statement

---

Phase 12 is complete as a safe baseline because the repository now contains a typed action-verification package, deterministic verification service, negative and positive tests, explicit failure modes, and phase-specific engineering documentation. The architecture intentionally refuses to confuse 'the click was sent' with 'the requested result happened'.