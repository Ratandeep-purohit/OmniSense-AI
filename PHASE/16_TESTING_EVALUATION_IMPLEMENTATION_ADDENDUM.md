# Phase 16 — Testing & Evaluation — Implementation Addendum

## 1. Purpose

This addendum is the implementation-specific companion to the existing Phase 16 specification.

Important repository rule: the pre-existing PHASE/16_TESTING_EVALUATION.md was not replaced. This addendum records the actual implementation delivered for the current architecture.

Phase 16 is a cross-cutting quality phase. It introduces a reusable evaluation boundary while keeping pytest as the primary repository test runner.

Core principle:

Test the capability, test the boundary, and test the failure.

---

## 2. Actual Repository Mapping

Implemented files:

src/omnisense_ai/evaluation/
- __init__.py
- errors.py
- models.py
- service.py

tests/
- test_evaluation.py

The evaluation package is a genuine architectural responsibility, so it is a new source package rather than a phase-numbered directory.

---

## 3. Architectural Position

The current lifecycle is:

Capture
→ Visual Processing
→ OCR / Window Detection
→ UI Understanding
→ Context
→ AI / VLM
→ Assistant
→ Action Planning
→ Security
→ Safety / Permission
→ Desktop Automation
→ Verification
→ Memory

Phase 16 sits across this pipeline.

It observes and evaluates contracts. It does not become an authority layer.

Critical invariant:

Evaluation can observe authorization.
Evaluation cannot grant authorization.

---

## 4. Scope

Phase 16 implementation covers:

1. Evaluation configuration.
2. Bounded evaluation cases.
3. Deterministic case execution.
4. PASS / FAIL / ERROR classification.
5. Suite aggregation.
6. Fail-fast behavior.
7. Explicit skipped-case accounting.
8. Critical-case metadata.
9. Bounded diagnostics.
10. Lifecycle controls.
11. Unit tests for the evaluation infrastructure.
12. Phase 17 integration handoff requirements.

Out of scope:

- real desktop actions during ordinary tests
- screenshot archival
- automatic memory writes
- network-based evaluation
- automatic model training
- security bypasses
- permission bypasses
- packaging-specific smoke execution

---

## 5. EvaluationConfig Contract

EvaluationConfig is immutable and provides:

| Field | Default | Boundary |
|---|---:|---|
| enabled | True | evaluation availability |
| max_cases | 500 | suite cardinality |
| max_case_name_length | 120 | IDs/names |
| max_message_length | 1000 | diagnostics |
| fail_fast | False | suite execution policy |

Invalid bounds are rejected during configuration construction.

This prevents evaluation infrastructure from becoming an unbounded resource consumer.

---

## 6. EvaluationCase Contract

Each case contains:

- case_id
- name
- callable check
- tags
- critical flag

The check is intentionally a zero-argument callable.

This keeps the runner independent from a particular test framework and allows future deterministic scenario harnesses to reuse it.

The callable itself is responsible for assertions.

A case does not receive desktop authority from the evaluation service.

---

## 7. EvaluationResult Contract

Every executed case produces:

- case_id
- name
- outcome
- duration_ms
- bounded message
- tags
- critical
- timezone-aware completed_at

Diagnostic text is truncated to max_message_length.

The framework does not store screenshots, OCR archives, credentials, prompts, or arbitrary application state.

---

## 8. Outcome Model

The implementation distinguishes:

PASS
- check completed successfully.

FAIL
- check raised AssertionError.

ERROR
- check raised an unexpected exception.

This distinction is important.

A FAIL generally means the product behavior violated an expected contract.

An ERROR means the evaluation itself encountered an unexpected runtime condition.

Neither is silently converted into PASS.

---

## 9. Suite Report

EvaluationReport aggregates:

- suite_name
- generated_at
- status
- results
- passed
- failed
- errored
- skipped

Status rules:

- FAILED if any executed case failed or errored.
- SKIPPED if fail-fast left cases unexecuted and all executed cases passed.
- PASSED when all supplied cases executed and passed.

Skipped is never silently counted as passed.

---

## 10. Fail-Fast

Default behavior is fail-fast disabled.

When enabled, the runner stops after the first non-PASS result.

Remaining cases are counted as skipped:

Case A → PASS
Case B → FAIL
Case C → SKIPPED
Case D → SKIPPED

This preserves accurate release evidence.

---

## 11. Critical Cases

EvaluationCase supports critical=True.

This is metadata only.

It does not:

- grant permission
- bypass security
- change automation behavior
- alter Phase 10 decisions

It exists so future release gates can identify scenarios such as:

- stale-context rejection
- unauthorized execution rejection
- security redaction
- plan/context mismatch
- verification freshness

---

## 12. Lifecycle

EvaluationService has three effective states:

Created
→ Operational

Created
→ Disabled

Operational
→ Closed

Disabled evaluation rejects operations with EvaluationDisabledError.

Closed evaluation rejects operations with EvaluationInputError.

There is no implicit reopening.

---

## 13. Thread Safety

EvaluationService owns an RLock.

The suite runner serializes suite execution under the service lock.

The current implementation intentionally avoids background workers, queues, persistence, and asynchronous scheduling.

This keeps behavior deterministic and makes Phase 16 suitable for normal development tests.

Future parallel evaluation requires an explicit concurrency design.

---

## 14. Timing

Case duration uses time.perf_counter().

This is monotonic elapsed-time measurement.

It is not used as a correctness assertion against a fixed machine speed.

Reports use timezone-aware UTC timestamps for completion and generation metadata.

---

## 15. Resource Bounds

The implementation bounds:

- number of cases per suite
- case identifier length
- case name length
- suite name length
- diagnostic message length

The runner has no persistent result store and no unbounded internal history.

This is deliberate.

Evaluation infrastructure should not become another memory-retention path.

---

## 16. Error Boundary

Typed evaluation errors:

- EvaluationError
- EvaluationInputError
- EvaluationResourceError
- EvaluationDisabledError

Application check exceptions are classified into result outcomes rather than being silently swallowed.

AssertionError becomes FAIL.

Other exceptions become ERROR.

The diagnostic contains only a bounded exception type/message representation.

---

## 17. Security Boundary

Phase 15 remains authoritative for security validation.

Phase 16 does not:

- sanitize credentials itself as a substitute for Phase 15
- authorize actions
- execute desktop operations
- launch subprocesses
- send network requests

Security scenarios should call the actual Phase 15 boundary under test.

The evaluator must not create a second security implementation that can drift from production behavior.

---

## 18. Automation Boundary

Ordinary Phase 16 tests must use inert or mocked automation backends.

A unit test must never unexpectedly:

- move the mouse
- click
- type
- press keys
- open applications
- close applications

Real PyAutoGUI testing belongs to an explicitly controlled OS integration tier.

The rule remains:

Phase 10 authorizes.
Phase 11 executes.
Phase 12 verifies.
Phase 16 evaluates.

---

## 19. Memory Boundary

Evaluation does not write to Phase 13 memory.

There is no hidden call to remember(), recall(), or any persistence backend.

Evaluation artifacts are not user memory.

Future diagnostic persistence would require a separate product and privacy decision.

---

## 20. Performance Boundary

Evaluation uses lightweight timing through perf_counter().

It does not require exact millisecond thresholds.

Phase 14 remains responsible for performance observation and percentile reporting.

Future regression gates may compare:

- p50
- p95
- p99
- failure rate
- stage budget status

against platform-appropriate baselines.

---

## 21. Required Cross-Phase Scenarios

Phase 16 inherits the following scenario set from Phase 15:

1. Prompt injection inside OCR text.
2. Oversized OCR output.
3. Secret-bearing model output.
4. Malformed action target.
5. Stale context.
6. Unauthorized execution attempt.
7. Sensitive verification evidence.
8. Sensitive memory request.
9. Disabled security.
10. Closed security.
11. Malformed future integration response.
12. Future SSRF boundary.

The important assertion is not only that the scenario fails safely.

The test must also prove that no unsafe fallback path executes.

---

## 22. Negative Testing Policy

Every major phase must have negative tests.

Examples:

- invalid types
- empty identifiers
- oversized values
- stale timestamps
- mismatched IDs
- denied permissions
- unsupported actions
- malformed URLs
- credential-bearing URLs
- disabled services
- closed services
- missing execution records
- failed execution records
- unsupported verification expectations
- expired memory
- unsafe metadata

Happy-path-only testing is insufficient for OmniSense.

---

## 23. Test Data Policy

Use synthetic data.

Preferred fixtures:

- ctx-test-001
- plan-test-001
- synthetic OCR text
- synthetic window metadata
- fake model output
- deterministic timestamps
- fake execution results
- fake verification evidence

Do not use:

- real passwords
- real API keys
- production credentials
- private customer records
- real screenshots containing sensitive data

A test fixture should contain the minimum information required to prove the behavior.

---

## 24. Test Tier Model

Tier 0 — Unit

Pure in-process tests with no external state.

Tier 1 — Cross-phase contract

Multiple real components connected with deterministic fixtures.

Tier 2 — Windows OS integration

Controlled real capture/window/optional automation behavior.

Tier 3 — Release smoke

Packaged application validation.

Phase 16 implements the foundation for these tiers.

Phase 18 owns final packaging smoke execution.

---

## 25. Evaluation vs pytest

Pytest remains the repository's primary test runner:

python -m pytest

The Phase 16 EvaluationService solves a different problem.

Pytest answers:

Did the repository test pass?

EvaluationService answers:

Can a reusable application scenario be represented, executed, classified, bounded, and aggregated as runtime data?

This distinction is useful for future local diagnostics, integration harnesses, release smoke tests, and scenario dashboards.

---

## 26. Current Test Coverage

tests/test_evaluation.py covers:

- successful case
- assertion failure
- unexpected exception
- suite aggregation
- fail-fast
- skipped count
- case/suite bounds
- disabled lifecycle
- closed lifecycle
- invalid case contracts
- critical metadata
- timezone-aware report generation

These tests validate the evaluation infrastructure itself.

They do not pretend to be the complete Phase 17 system integration suite.

---

## 27. Regression Workflow

For future bugs:

1. Reproduce.
2. Add a failing regression test.
3. Fix the smallest correct boundary.
4. Run focused tests.
5. Run the complete pytest suite.
6. Review security and authority boundaries.
7. Commit.

Do not weaken tests merely to make a build green.

---

## 28. Full Suite Gate

The project-level gate remains:

python -m pytest

Release evidence should be interpreted as:

- all collected tests pass
- no unexpected errors
- critical safety/security scenarios pass
- known skips are intentional
- performance regressions are reviewed

Do not hardcode a total test count as the quality criterion because the suite is expected to grow.

---

## 29. CI Readiness

A future CI pipeline should:

1. install the supported Python version
2. install development dependencies
3. run unit tests
4. run deterministic integration tests
5. publish test results
6. fail on unexpected failures
7. run platform-specific suites separately where required

No CI job should silently enable real desktop automation.

---

## 30. Performance Evaluation Rules

Do not claim a fixed latency from one developer laptop.

For performance regression:

- use synthetic workloads
- use platform-specific baselines
- compare percentiles
- track failures separately
- avoid exact timing assertions for ordinary unit tests

Phase 14 remains the source of truth for performance telemetry semantics.

---

## 31. Concurrency Evaluation — Future

Future concurrency tests should cover:

- simultaneous case execution
- close during contention
- bounded worker counts
- deterministic cleanup
- no cross-case state leakage

Do not introduce uncontrolled thread creation merely to test concurrency.

---

## 32. Fuzz / Property Testing — Future

Future fuzzing may target:

- identifiers
- metadata
- URLs
- action-plan limits
- memory retention
- verification aggregation

Every fuzz harness must define:

- input size limits
- execution timeouts
- crash handling
- artifact retention
- privacy rules

Fuzzing is intentionally not a prerequisite for the current Phase 16 implementation.

---

## 33. Model Evaluation — Future

Unit tests cannot fully measure Phase 07 model quality.

Future model evaluation may measure:

- grounding
- hallucination
- instruction following
- prompt-injection resistance
- action-plan validity
- clarification quality
- refusal correctness

Datasets must be versioned and intentionally selected.

Runtime screen data must not silently become model-training or evaluation data.

---

## 34. Human Evaluation — Future

Some assistant behaviors require human review.

Potential review dimensions:

- factual grounding
- clarity
- appropriate uncertainty
- useful clarification
- appropriate refusal
- action explanation
- privacy handling

Human review is an evaluation input, not an authorization mechanism.

---

## 35. Observability Evaluation

Future observability tests should verify:

- event names
- correlation IDs
- status
- bounded counts
- bounded durations
- typed error categories

They should also verify what is not emitted:

- screenshots
- raw OCR archives
- passwords
- tokens
- cookies
- authorization headers
- private prompts

Diagnostic completeness must not override privacy.

---

## 36. Failure Injection

Future integration tests should deliberately inject:

- capture failure
- OCR timeout
- VLM timeout
- malformed model output
- stale context
- denied permission
- automation backend failure
- cancellation
- verification mismatch
- memory backend failure
- security rejection

Expected behavior is controlled failure.

Silent unsafe fallback is a regression.

---

## 37. Acceptance Criteria

- [x] Dedicated evaluation package exists.
- [x] Configuration is immutable and bounded.
- [x] Evaluation cases are typed.
- [x] PASS/FAIL/ERROR are distinct.
- [x] Suite aggregation exists.
- [x] Fail-fast behavior is explicit.
- [x] Skipped cases are counted.
- [x] Critical metadata is preserved.
- [x] Disabled lifecycle is deterministic.
- [x] Closed lifecycle is deterministic.
- [x] Diagnostic messages are bounded.
- [x] No desktop authority was added.
- [x] No memory side effect was added.
- [x] No network dependency was added.
- [x] Evaluation framework tests exist.
- [x] Phase 15 handoff scenarios are documented.
- [x] Phase 17 integration requirements are defined.

---

## 38. Definition of Done

Phase 16 is complete for the current architecture when:

1. A reusable evaluation boundary exists.
2. Unit tests remain the primary regression mechanism.
3. Cross-phase expectations are explicitly documented.
4. Safety and security failures are testable.
5. Evaluation cannot grant authority.
6. Evaluation cannot silently persist user data.
7. Full pytest remains the release-quality baseline.
8. Phase 17 has a concrete integration handoff.

---

## 39. Phase 17 Handoff

Phase 17 must connect:

Capture
→ Visual Processing
→ OCR / Window Detection
→ UI Understanding
→ Context
→ AI / VLM
→ Assistant
→ Action Planning
→ Security
→ Safety / Permission
→ Desktop Automation
→ Verification
→ Memory

Integration gates:

- context identity remains consistent
- stale context is rejected
- screen text remains untrusted
- plans require explicit authorization
- automation executes only approved steps
- verification requires valid post-execution evidence
- memory remains explicit
- security remains fail-closed
- performance remains observational

Phase 17 should be the first phase where the full architecture is tested as one controlled pipeline.

---

## 40. ADR-16-001 — Reusable Evaluation Boundary

Decision:

Create omnisense_ai.evaluation instead of hiding all runtime evaluation behavior inside pytest.

Reason:

Future local diagnostics and packaged-app evaluation require a bounded application-level contract.

---

## 41. ADR-16-002 — Pytest Remains Primary

Decision:

Keep pytest as the repository test runner.

Reason:

The project already has a stable pytest suite, fixtures, optional dependency handling, and normal developer workflow.

---

## 42. ADR-16-003 — No Real Desktop Actions in Unit Tests

Decision:

Unit tests use inert or mocked automation.

Reason:

A test must never unexpectedly affect the user's desktop.

---

## 43. ADR-16-004 — Failure and Error Are Different

Decision:

Assertion failures and unexpected exceptions have separate outcomes.

Reason:

Release diagnosis needs to distinguish product-contract failures from evaluator/runtime failures.

---

## 44. ADR-16-005 — Evaluation Data Is Not Memory

Decision:

No implicit Phase 13 memory writes.

Reason:

Testing infrastructure must not become a hidden user-data retention path.

---

## 45. Final Phase Rule

Unit tests prove components.

Integration tests prove boundaries.

Evaluation proves scenarios.

Security limits trust.

Safety limits authority.

Automation executes.

Verification proves outcomes.

Phase 16 makes the architecture measurable and regression-resistant without creating another authority path.

