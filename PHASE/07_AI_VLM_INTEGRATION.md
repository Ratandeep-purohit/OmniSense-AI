# OmniSense AI — Phase 7 — AI / VLM Integration

**Status:** Implemented — provider-neutral inference foundation
**Phase ID:** P07
**Principle:** Intelligence without uncontrolled authority.

## 1. Purpose

Phase 07 is the controlled reasoning boundary between the Phase 06 Context Engine and the Phase 08 Intelligent Assistant.

It provides:
- provider-neutral AI/VLM contracts;
- bounded request construction;
- explicit trust labels;
- context freshness validation;
- input/output limits;
- optional visual evidence;
- typed provider, timeout, security and validation failures;
- deterministic offline testing.

It does **not** train a model and does **not** give a model authority over the desktop.

## 2. Architecture

```
Phase 06 ContextSnapshot
        |
        v
+-------------------------+
| Phase 07 AI/VLM Gateway |
| - freshness validation  |
| - trust boundary        |
| - input limits          |
| - output validation     |
+------------+------------+
             |
             v
      AIProvider protocol
        /           \
       /             \
local/cloud       deterministic
future adapter       test adapter
       \             /
        \           /
          AIResponse
             |
             v
        Phase 08
```

## 3. Repository Mapping

| Path | Responsibility |
|---|---|
| src/omnisense_ai/ai_vlm/models.py | AI configuration, request and response contracts |
| src/omnisense_ai/ai_vlm/errors.py | typed Phase 07 errors |
| src/omnisense_ai/ai_vlm/backend.py | provider protocol and deterministic provider |
| src/omnisense_ai/ai_vlm/service.py | gateway and trust/resource enforcement |
| src/omnisense_ai/ai_vlm/__init__.py | public API |
| tests/test_ai_vlm.py | regression and safety tests |

## 4. Training Boundary

Phase 07 is inference integration, not training.

No training dataset is automatically collected from the user's desktop. Future model improvement can use:
1. public UI/OCR/VLM datasets;
2. synthetic UI data with known labels;
3. explicitly consented and curated examples;
4. evaluation failures identified by Phase 16.

The runtime screen is evidence for the current inference request, not an implicit training record.

## 5. Provider Contract

Providers implement:

```
generate(request, timeout_seconds) -> str
```

The provider abstraction is deliberately small. A provider adapter MUST:
- accept only the typed request;
- return model text;
- report provider failures;
- respect the supplied time budget;
- avoid desktop automation;
- avoid granting authorization.

Future cloud or local adapters can be implemented without changing the Phase 08 dependency.

## 6. Request Contract

AIRequest contains:
- request/correlation ID;
- ContextSnapshot ID;
- user instruction;
- bounded observed desktop context;
- optional user context;
- evidence trust classification;
- optional visual bytes and image MIME type.

Visual bytes are transient call data. Phase 07 does not persist screenshots.

## 7. Trust Model

Desktop evidence is explicitly marked as observed data.

Visible OCR text can contain malicious instructions or prompt injection. Therefore the gateway tells the model that observed evidence is not authority and cannot override system policy or user authorization.

Trust ordering:
1. system/security policy;
2. explicit bounded user authorization;
3. user-provided context;
4. observed desktop evidence;
5. model-generated output.

Model output remains untrusted until later validation.

## 8. Resource Controls

Implemented:
- AI disabled by default;
- provider/model identifiers;
- 15-second default timeout budget;
- bounded input characters;
- bounded output characters;
- bounded retry configuration;
- optional visual-input gate;
- stale-context rejection;
- typed timeout/resource failures.

The retry setting is a contract/configuration field only at this phase; provider-specific retry orchestration belongs to the provider adapter.

## 9. Safety Boundary

Phase 07 MUST NOT:
- click or type;
- move the mouse;
- focus/close/launch applications;
- execute shell commands;
- create executable action plans;
- authorize consequential actions;
- interpret screen text as authorization;
- persist unrestricted screen history.

The intended chain is:

```
AI/VLM
  -> Assistant
  -> Action Planning
  -> Safety/Permission
  -> Desktop Automation
  -> Verification
```

## 10. Deterministic Test Provider

The deterministic provider is intentionally simple. It allows the complete gateway contract to be tested without:
- API credentials;
- network access;
- a downloaded model;
- GPU requirements;
- external side effects.

This is a test/development provider, not the production intelligence layer.

## 11. Test Coverage

Current tests verify:
- successful provider boundary;
- prompt-injection-like screen text is treated as untrusted evidence;
- AI is disabled by default;
- output size is enforced;
- visual input can be explicitly disabled;
- stale context is rejected.

Run locally:

```powershell
git pull origin main
python -m pytest
```

## 12. Known Limitation

Phase 06 currently synthesizes its context timestamp at context construction because the upstream Phase 02/03/05 contracts do not yet carry one shared capture timestamp. Phase 07 therefore validates the age of the ContextSnapshot, not the original screen capture age.

A future contract-hardening change should propagate capture timestamps from Phase 02 through OCR/UI/context.

## 13. Phase 08 Handoff

Phase 08 should consume AIVLMService and AIResponse.

Phase 08 MUST NOT:
- bypass the gateway;
- call a provider directly;
- treat model text as an executable command;
- skip the later planning/safety boundaries.

**Engineering rule:** AI may interpret evidence; AI does not receive authority.
