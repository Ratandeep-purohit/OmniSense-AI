# OmniSense AI — Phase 09 — Action Planning

**Status:** Implemented  
**Boundary:** Planning only. No execution.

## Purpose
Phase 09 converts explicit user intent into a typed, inspectable ActionPlan. A plan is not permission and is never execution.

## Pipeline
```
User Intent → Phase 08 → Phase 09 Action Planner → ActionPlan
→ Phase 10 Safety/Permission → Phase 11 Automation → Phase 12 Verification
```

## Repository
- `action_planning/models.py` — typed action vocabulary, targets, steps, plans and config.
- `action_planning/errors.py` — planning failures.
- `action_planning/service.py` — deterministic planning boundary.
- `action_planning/__init__.py` — public API.
- `tests/test_action_planning.py` — regression tests.

## Action Vocabulary
Current finite types:
`click`, `type`, `hotkey`, `open_app`, `close_app`, `move`, `scroll`, `wait`.

No arbitrary shell command, Python code or unrestricted automation is accepted as an action type.

## Contracts
**ActionTarget** describes a target without performing lookup or interaction.

**ActionStep** contains step ID, action type, target, bounded parameters, risk, expected outcome and reversibility.

**ActionPlan** contains plan ID, context ID, explicit intent, status, ordered steps, rationale and confirmation requirement.

## Status
- READY — typed plan can proceed to Phase 10 review.
- NEEDS_CLARIFICATION — intent is insufficiently specific.
- REJECTED — reserved for policy rejection.

## Risk and Safety
Risk is explicit: LOW, MEDIUM, HIGH, CRITICAL.

Phase 09 does not grant permission. High-consequence requests such as deletion, payment, purchase and money transfer are blocked at this baseline until the dedicated Phase 10 policy engine exists.

## Ambiguity
Ambiguous language must fail closed rather than become a guessed action.

Examples: “maybe do something”, “not sure”, “handle it”.

## Current Planner
The baseline planner is deterministic. It recognizes explicit verbs for click, type, scroll, open, close and wait. Unknown conversational requests become NEEDS_CLARIFICATION.

This is intentionally a safe baseline; richer model-assisted intent extraction can be introduced later without adding execution authority.

## Security Boundary
Phase 09 cannot click, type, launch apps, run commands, mutate files, send network requests, grant authorization or execute its own output.

A visible screen instruction is untrusted evidence and cannot become authorization merely through OCR.

## Resource Controls
- configured maximum steps: 10;
- absolute plan maximum: 20;
- intent maximum: 4,000 characters;
- parameter pairs per step: 30.

## Testing
Tests cover ready click plans, ambiguity, high-consequence rejection, unrelated conversational input and the absence of an execute API.

Future tests should cover multi-step plans, target resolution, stale context, serialization, risk matrices and screen-derived prompt-injection fixtures.

## Architecture Decisions
**ADR-09-01:** planning is separate from execution.  
**ADR-09-02:** permission is downstream in Phase 10.  
**ADR-09-03:** finite action vocabulary prevents arbitrary code execution.  
**ADR-09-04:** ambiguity fails closed.

## Acceptance Criteria
- [x] typed action vocabulary
- [x] typed targets and steps
- [x] typed action plan
- [x] explicit risk
- [x] confirmation metadata
- [x] bounded plan size
- [x] ambiguity handling
- [x] no execution API
- [x] regression tests

## Phase 10 Handoff
Phase 10 receives ActionPlan and evaluates target validity, risk, authorization, policy, scope and confirmation.

```
ActionPlan → Safety/Permission → Approved/Denied → Phase 11
```

**Final rule: Phase 09 decides what could be done; Phase 10 decides whether it may be done.**
