# OmniSense AI — Phase 13 — Memory

Phase ID: P13
Status: Implementation complete; local validation pending
Principle: Intelligence without uncontrolled authority.

## 1. Executive Summary

Phase 13 introduces the first explicit memory boundary in OmniSense AI.
The purpose is to retain useful user-approved information without becoming a screen recorder, conversation archive, training-data collector, or authorization store.

Implemented:
- typed memory contracts
- explicit enablement
- bounded storage
- bounded keys, values, queries and results
- configurable retention
- sensitivity policy
- provenance
- deterministic recall
- update-by-kind-and-key
- individual deletion
- clear operation
- automatic expiry
- backend protocol
- deterministic in-memory backend
- thread-safe service operations
- typed failures
- no screenshot persistence
- no OCR-stream persistence
- no automation authority

## 2. Phase Position

Phase 06 Context -> Phase 07 AI/VLM -> Phase 08 Assistant -> Phase 09 Planning -> Phase 10 Safety -> Phase 11 Automation -> Phase 12 Verification -> Phase 13 Memory

The execution safety chain remains:

AI -> Plan -> Authorize -> Execute -> Verify

Memory is informational. It is never an authorization source.

## 3. Core Invariants

### P13-I01 — Disabled by default
Memory MUST be disabled unless explicitly enabled by configuration.

### P13-I02 — Memory is not authority
Memory MUST NOT authorize clicking, typing, launching, closing, deleting, sending, purchasing, changing settings, bypassing confirmation, or bypassing Phase 10.

### P13-I03 — Bounded storage
The service MUST enforce entry, key, value, query and result limits.

### P13-I04 — Explicit sensitivity
Sensitive memory MUST be rejected unless policy explicitly permits it.

### P13-I05 — Retention
Every entry has an expiry timestamp and expired entries are excluded from recall.

### P13-I06 — Explicit deletion
An individual memory can be forgotten and the active memory set can be cleared.

### P13-I07 — No screenshot archive
Phase 13 MUST NOT store raw screen frames.

### P13-I08 — No OCR archive
Phase 13 MUST NOT automatically persist the OCR stream.

### P13-I09 — Provenance
Memory MAY retain bounded provenance labels.

### P13-I10 — No hidden training
Memory MUST NOT silently become model-training data.

### P13-I11 — Deterministic baseline
The initial recall algorithm is deterministic substring matching.

### P13-I12 — Stable boundary
Downstream components consume public memory contracts rather than backend internals.

## 4. Scope

### In scope
- memory data contracts
- configuration
- remember
- recall
- update
- forget
- clear
- retention
- sensitivity
- provenance
- backend abstraction
- in-memory storage
- tests
- documentation

### Out of scope
- vector databases
- embeddings
- semantic retrieval
- automatic desktop recording
- automatic conversation recording
- model fine-tuning
- automatic memory extraction from every screen
- encrypted persistent database
- cloud synchronization
- cross-device memory
- memory-based authorization
- autonomous deletion decisions
- desktop automation

## 5. Repository Layout

src/omnisense_ai/memory/
  __init__.py
  backend.py
  errors.py
  models.py
  service.py

tests/test_memory.py
PHASE/13_MEMORY.md

## 6. Component Responsibilities

models.py owns immutable contracts.
errors.py owns memory-specific failures.
backend.py owns the storage protocol and deterministic in-memory implementation.
service.py owns policy enforcement, validation, retention, updates, deletion and concurrency.
__init__.py defines the public package surface.
test_memory.py verifies the public behavior.

## 7. Architecture

```
Explicit request
      |
      v
MemoryService
      |
      +--> validation
      +--> sensitivity policy
      +--> retention
      +--> capacity
      +--> concurrency
      |
      v
MemoryBackend
      |
      v
MemoryEntry
```

The service is the policy enforcement point. A backend is storage only.

## 8. Trust Model

| Source | Trust | Rule |
|---|---|---|
| User-approved memory | High within scope | Store after validation |
| Assistant suggestion | Low | Never silently persist |
| OCR | Low | Never automatically persist |
| Screen pixels | Low | Never automatically persist |
| Window metadata | Low/Medium | Context only |
| AI/VLM output | Low | Not authority |
| Existing memory | Informational | Not authorization |
| Security policy | Highest | Cannot be overridden |

## 9. Memory Kinds

MemoryKind has four values:

- preference — stable user preference
- fact — bounded factual item
- task — task-related datum
- episode — concise retained event

An episode is not an automatic activity log. It must be explicitly created.

## 10. Sensitivity

MemorySensitivity has:

- normal
- sensitive

Sensitive storage defaults to disabled.

Potential sensitive data includes passwords, authentication tokens, private keys, financial credentials and private identifiers.

Even when explicitly enabled, Phase 13 is not a secret vault. A future secret-storage subsystem requires separate encryption and access controls.

## 11. Configuration Contract

Default configuration:

enabled = False
max_entries = 1000
max_key_length = 256
max_value_length = 4096
max_query_length = 512
max_results = 20
retention_seconds = 30 days
allow_sensitive = False

Configuration bounds are validated at object construction.

## 12. MemoryEntry Contract

Fields:

- memory_id
- kind
- key
- value
- created_at
- updated_at
- expires_at
- sensitivity
- source
- status
- provenance

All timestamps MUST be timezone-aware.

memory_id is generated by the service in the form mem-<uuid>.
key and value are trimmed before storage.
source defaults to user.
provenance is a tuple of non-empty labels.

## 13. Memory Status

MemoryStatus values:

- active
- expired
- deleted

The current in-memory backend physically removes expired and deleted entries.

## 14. Remember Operation

The remember pipeline is:

1. verify service is enabled
2. validate timestamp
3. validate key
4. validate value
5. validate source
6. enforce sensitivity policy
7. validate provenance
8. purge expired entries
9. locate same kind and key
10. update existing entry or allocate a new ID
11. enforce capacity for a new entry
12. store the immutable entry
13. return the entry

## 15. Update Semantics

Same kind plus same key means update.

The memory_id is preserved.
The original created_at is preserved.
updated_at becomes the current timestamp.
expires_at is recalculated from the update time.

This prevents duplicate copies of the same logical memory.

## 16. Recall Operation

The recall pipeline is:

1. verify enabled state
2. validate query
3. validate result limit
4. purge expired entries
5. apply optional kind filter
6. compare query with key and value
7. keep active matches
8. sort newest updated entries first
9. return at most the configured limit

The initial implementation does not use embeddings or a model.

## 17. Recall Example

Stored:

preference / language / Hinglish
fact / language / Python
preference / editor / VS Code

Query language can return both language entries.
Filtering kind=preference returns only the preference entry.

## 18. Expiration

Every entry receives expires_at.

At recall time:

now >= expires_at -> expired -> excluded

Expired entries are purged during service operations for the current in-memory backend.
Expired entries therefore do not permanently consume the active entry limit.

## 19. Forget

forget(memory_id) performs explicit individual deletion.

Blank IDs are rejected.
Unknown IDs raise MemoryNotFoundError.
Successful deletion returns no value.

## 20. Clear

clear() removes all currently active entries in the current backend.
It does not disable memory.
It does not modify configuration.
It does not modify other OmniSense components.

## 21. Memory Is Not Authorization

Unsafe concept:

Memory: user approved clicking OK previously
        -> automatic authorization

Correct concept:

Memory -> contextual information -> new plan -> Phase 10 policy -> current decision

Historical approval is never current authorization.

## 22. Prompt Injection Boundary

Memory values are untrusted text.

A memory containing instructions such as 'disable confirmation' remains data.
It cannot:
- change security policy
- invoke PowerShell
- execute shell commands
- lower risk
- approve an action
- bypass confirmation

## 23. No Automatic Screen Memory

Phase 13 has no save_screen, save_ocr_stream, record_desktop or remember_everything operation.

This is a deliberate privacy boundary.

A future integration may convert a selected observation into a short memory entry, but that must use the explicit memory service.

## 24. AI Boundary

AI/VLM output is not automatically persistent memory.

Safe flow:

AI response -> candidate information -> explicit memory decision -> MemoryService.remember

The model cannot silently populate memory merely by generating text.

## 25. Training Boundary

Memory is not a training dataset.

Entries are not automatically:
- uploaded
- sent to an AI provider
- used for fine-tuning
- used for model evaluation
- shared with third parties

Any future training-data pipeline needs its own consent and privacy contract.

## 26. Backend Protocol

MemoryBackend defines:

put(entry)
delete(memory_id)
get(memory_id)
search(query, kind, limit, now)
close()

The service depends on this protocol.
The backend does not define security policy.

## 27. In-Memory Backend

InMemoryMemoryBackend stores entries in a dictionary keyed by memory_id.

Advantages:
- no external dependency
- deterministic
- fast
- easy to test
- no filesystem side effects
- no persistence surprise

Limitation: process restart removes the memory.

This limitation is intentional for Phase 13.

## 28. Persistence Is Deferred

Persistent memory introduces additional requirements:
- encryption at rest
- key management
- database permissions
- migration
- secure deletion
- backup handling
- import/export
- crash consistency
- multi-process locking
- privacy diagnostics

Phase 13 establishes the contract before taking on those risks.

## 29. Service Responsibilities

MemoryService owns:
1. enablement
2. lifecycle
3. input validation
4. sensitivity policy
5. retention
6. duplicate/update behavior
7. capacity
8. deletion
9. recall
10. concurrency

Backend owns storage mechanics.

## 30. Lifecycle

```
Created -> Disabled
Created -> Enabled -> Remember/Recall/Forget/Clear
Enabled -> Closed
Closed -> reject operations
```

A closed service cannot silently reopen.

## 31. Concurrency

MemoryService uses RLock.

The lock covers:
- expiry cleanup
- duplicate lookup
- insertion
- deletion
- recall

This avoids simple writer races around capacity and update semantics.

## 32. Capacity

For a new entry:

purge expired -> count active entries -> compare max_entries -> insert or reject

Updating an existing key does not consume another slot.

## 33. Validation

The service rejects:
- blank keys
- blank values
- blank source
- oversized keys
- oversized values
- oversized queries
- invalid result limits
- naive timestamps
- empty provenance labels

Validation occurs before storage.

## 34. Error Taxonomy

MemoryDisabledError: service disabled or closed.
MemoryInputError: input contract violation.
MemoryResourceError: resource limit exceeded.
MemorySecurityError: security policy rejection.
MemoryNotFoundError: requested memory does not exist.

Public code should use these errors rather than backend-specific exceptions.

## 35. Privacy Minimization

Prefer:

preferred_editor = VS Code

over:

entire screenshot of the editor

Memory should retain the smallest useful representation.

## 36. Provenance

Provenance is descriptive metadata.

Example:
provenance = (user_message,)

Possible future labels:
- user_message
- explicit_setting
- approved_summary
- application_state

Provenance does not increase authority.

## 37. Data Flow

```
Explicit request
   -> validate
   -> sensitivity policy
   -> retention policy
   -> backend
   -> MemoryEntry
```

Recall:

```
Query
   -> validate
   -> purge expired
   -> backend search
   -> bounded results
   -> MemoryResult
```

## 38. State Model

Service states:
- disabled
- enabled
- closed

Entry states:
- active
- expired
- deleted

State transitions are explicit and testable.

## 39. Functional Requirements

| ID | Requirement | Enforcement |
|---|---|---|
| P13-FR-001 | Disabled by default | MemoryService |
| P13-FR-002 | Explicit enablement | MemoryService |
| P13-FR-003 | Entry count bounded | MemoryService |
| P13-FR-004 | Key length bounded | MemoryService |
| P13-FR-005 | Value length bounded | MemoryService |
| P13-FR-006 | Query length bounded | MemoryService |
| P13-FR-007 | Result count bounded | MemoryService |
| P13-FR-008 | Sensitive storage denied by default | MemoryService |
| P13-FR-009 | Sensitive storage can be explicitly enabled | MemoryService |
| P13-FR-010 | Expiry assigned to every entry | MemoryService |
| P13-FR-011 | Expired entries excluded | Backend/Service |
| P13-FR-012 | Same kind/key updates | MemoryService |
| P13-FR-013 | Individual deletion | MemoryService |
| P13-FR-014 | Clear operation | MemoryService |
| P13-FR-015 | Provenance preserved | MemoryEntry |
| P13-FR-016 | Timestamps timezone-aware | Models |
| P13-FR-017 | Deterministic recall | Backend |
| P13-FR-018 | Kind filtering | Backend |
| P13-FR-019 | Replaceable backend | Protocol |
| P13-FR-020 | No execution authority | Architecture |
| P13-FR-021 | No screenshot archive | Architecture |
| P13-FR-022 | No automatic OCR persistence | Architecture |
| P13-FR-023 | No automatic AI persistence | Architecture |
| P13-FR-024 | Cannot bypass Phase 10 | Architecture |
| P13-FR-025 | Synchronized operations | RLock |
| P13-FR-026 | Closed lifecycle enforced | Service |
| P13-FR-027 | Missing ID typed failure | Service |
| P13-FR-028 | Backend hidden behind contract | Protocol |
| P13-FR-029 | Configuration validated | MemoryConfig |
| P13-FR-030 | No automatic training path | Architecture |

## 40. Non-Functional Requirements

NFR-001 Determinism: same state and query produce the same ordered result.
NFR-002 Bounded resources: limits are enforced before storage or return.
NFR-003 Privacy: default behavior minimizes retained information.
NFR-004 Testability: behavior works without a real desktop.
NFR-005 Dependency minimization: Phase 13 uses standard-library mechanisms.
NFR-006 Replaceability: storage remains behind MemoryBackend.
NFR-007 Failure clarity: expected failures use typed exceptions.
NFR-008 No authority escalation: memory cannot create an automation path.

## 41. API Contract

remember(kind, key, value, source, sensitivity, provenance, now) -> MemoryEntry
recall(query, kind, limit, now) -> MemoryResult
forget(memory_id) -> None
clear() -> None
close() -> None

All public operations enforce service state and policy.

## 42. Example

```python
config = MemoryConfig(enabled=True)
memory = MemoryService(config)
memory.remember(
    kind=MemoryKind.PREFERENCE,
    key='language',
    value='Hinglish',
    provenance=('user_message',),
)
result = memory.recall('language')
```

The example stores one explicit fact. It performs no desktop action.

## 43. Failure Matrix

| Condition | Result |
|---|---|
| memory disabled | MemoryDisabledError |
| blank key | MemoryInputError |
| blank value | MemoryInputError |
| oversized key | MemoryResourceError |
| oversized value | MemoryResourceError |
| oversized query | MemoryResourceError |
| invalid result limit | MemoryInputError |
| sensitive memory denied | MemorySecurityError |
| capacity exhausted | MemoryResourceError |
| unknown memory ID | MemoryNotFoundError |
| naive timestamp | MemoryInputError |
| closed service | MemoryDisabledError |

## 44. Security Threat Model

### Memory injection
An attacker places instructions in a memory value.
Mitigation: memory is data and has no execution parser.

### Memory flooding
An attacker creates many entries.
Mitigation: max entries and bounded text.

### Sensitive-data capture
A caller tries to store secrets.
Mitigation: sensitive classification and deny-by-default.

### Stale authorization
Old memory claims an action was approved.
Mitigation: memory has no authorization interface.

### Privacy overcollection
The system stores every observation.
Mitigation: no screen or OCR archive interface exists.

### Backend bypass
A backend tries to change policy.
Mitigation: service owns policy; backend owns storage.

## 45. Performance

Current backend complexity:
- get/delete/put by ID: O(1) average
- recall: O(n)
- expiry purge: O(n)

With the default 1000-entry bound this is intentionally small and predictable.

## 46. Resource Budget

Default limits:
- entries <= 1000
- key <= 256 characters
- value <= 4096 characters
- query <= 512 characters
- results <= 20
- retention = 30 days

Limits are configuration-controlled within hard safety bounds.

## 47. No Screenshot Retention

Phase 13 stores no frame bytes, image files, video, UI screenshots or OCR screenshots.

The observation pipeline and memory pipeline remain separate.

## 48. No Automatic Conversation Archive

Phase 13 is not a general chat-history database.
An episode must be explicitly constructed and stored.

## 49. Future Semantic Retrieval

Embeddings and vector retrieval are deferred.

Future architecture may be:
query -> keyword filter -> semantic candidates -> policy filter -> freshness filter -> bounded results

Semantic retrieval must remain informational.

## 50. Future Memory Consolidation

A future consolidation flow may be:
multiple short-lived facts -> candidate summary -> user-visible review -> explicit save

Permanent preference inference must not silently occur from arbitrary activity.

## 51. Future User Controls

A production UI should eventually expose:
- memory enabled/disabled
- memory list
- search
- edit
- forget
- clear all
- retention settings
- sensitive-memory policy
- export/import

These controls are future integration work.

## 52. Phase 06 Integration

Phase 06 provides current desktop context.
Phase 13 does not automatically persist that context.

Future safe flow:
Context -> explicit extraction -> user-approved candidate -> MemoryService.remember

## 53. Phase 07 Integration

AI/VLM output is candidate information only.
It must not silently populate memory.

## 54. Phase 08 Integration

The assistant may use recalled memory as context.
It must not describe memory as proof of current permission.

## 55. Phase 09 Integration

Planning may use memory to understand preferences and intent.
Every action plan still requires current Phase 10 evaluation.

## 56. Phase 10 Integration

Phase 10 remains the sole safety/permission decision point for desktop actions.
Memory cannot change ALLOW, DENY, REQUIRE_CONFIRMATION or REQUIRE_CLARIFICATION.

## 57. Phase 11 Integration

Desktop automation must never use memory as a substitute for authorization.

## 58. Phase 12 Integration

Verification results may eventually become short episode memories only through an explicit policy.
Verification must not automatically create an unlimited activity archive.

## 59. Phase 14 Handoff

Performance work can evaluate recall latency, purge cost, concurrent access and larger backends while preserving limits.

## 60. Phase 15 Handoff

Security work can add encryption, OS-protected storage, secret detection and secure deletion.
Those changes must preserve explicit consent and bounded retention.

## 61. Phase 16 Handoff

Testing work can add property tests, concurrency stress, fuzzing, persistence tests and privacy regression tests.

## 62. Phase 17 Handoff

Integration can connect:

Context -> Assistant -> Memory
Memory -> Assistant -> Planner
Planner -> Safety -> Automation

The authorization boundary must remain intact.

## 63. Testing Strategy

Unit tests cover models, service policy and backend behavior.
Security tests cover disabled defaults, sensitivity and limits.
Lifecycle tests cover close and post-close operations.
Retention tests cover expiry and capacity reuse.
CRUD tests cover remember, recall, update, forget and clear.

## 64. Implemented Test Matrix

| Test | Expected |
|---|---|
| disabled by default | pass |
| remember and recall | pass |
| update same key | pass |
| kind filtering | pass |
| result limit | pass |
| sensitive default denial | pass |
| sensitive explicit enable | pass |
| retention expiry | pass |
| max entries | pass |
| forget | pass |
| unknown ID | pass |
| clear | pass |
| provenance | pass |
| expired slot reuse | pass |

## 65. Acceptance Criteria

Phase 13 is accepted when:
- memory package exists
- public contracts are typed
- disabled-by-default is enforced
- sensitive storage is denied by default
- storage is bounded
- retention is enforced
- explicit deletion works
- deterministic recall works
- tests pass
- no automation authority exists
- no screenshot archive exists
- no automatic training-data path exists
- documentation matches implementation

## 66. Definition of Done

Code:
- models implemented
- errors implemented
- backend protocol implemented
- in-memory backend implemented
- service implemented
- package exports implemented
- tests implemented

Security:
- disabled by default
- sensitivity gate
- bounded input
- bounded results
- no automation API
- no screenshot storage
- no automatic training path

Engineering:
- timezone-aware timestamps
- deterministic baseline
- explicit lifecycle
- synchronization
- typed failures
- backend abstraction

## 67. ADR-13-001 — Memory Disabled by Default

Decision: memory defaults to disabled.
Reason: memory can contain private information and should never silently become persistent state.
Consequence: integrations must explicitly opt in.

## 68. ADR-13-002 — In-Memory Backend First

Decision: begin with in-memory storage.
Reason: establish contracts before persistence security complexity.
Consequence: memory does not survive process restart in this phase.

## 69. ADR-13-003 — Deterministic Search

Decision: use substring matching for the baseline.
Reason: inspectable and easy to test.
Consequence: semantic retrieval is deferred.

## 70. ADR-13-004 — Memory Is Not Authorization

Decision: memory cannot authorize desktop actions.
Reason: historical information must not replace current authorization.
Consequence: Phase 10 remains authoritative.

## 71. ADR-13-005 — Sensitive Memory Requires Explicit Policy

Decision: sensitive memory is disabled by default.
Reason: reduce accidental secret retention.
Consequence: sensitive values are not silently captured.

## 72. Operational Guidance

Development default:
MemoryConfig(enabled=False)

Controlled tests may use MemoryConfig(enabled=True) with InMemoryMemoryBackend.

Production persistence should not be added by simply swapping the backend. Define encryption, deletion, migration, recovery and access controls first.

## 73. Troubleshooting

MemoryDisabledError: inspect MemoryConfig.enabled and service lifecycle.
MemorySecurityError: inspect allow_sensitive; do not enable it merely to hide the error.
MemoryResourceError: inspect entry, key, value, query and result limits.
MemoryNotFoundError: verify the memory ID.

## 74. Review Checklist

Architecture:
- memory isolated from automation
- backend replaceable
- service owns policy
- immutable contracts

Privacy:
- disabled by default
- no screenshots
- no automatic OCR persistence
- no automatic conversation archive
- sensitive denied by default
- retention exists
- deletion exists

Security:
- memory cannot authorize
- memory cannot execute
- memory cannot bypass Phase 10
- memory cannot become training data automatically

Reliability:
- limits enforced
- expiry enforced
- lock present
- typed errors
- closed lifecycle

## 75. Final Architecture Rule

SEE -> UNDERSTAND -> REASON -> ASSIST -> PLAN -> AUTHORIZE -> ACT -> VERIFY -> REMEMBER

Memory can be consulted earlier as context, but its semantics remain informational.

Phase 10 authorizes.
Phase 11 executes.
Phase 12 verifies.
Phase 13 remembers — explicitly, boundedly, and without authority.

## 76. Phase Completion Statement

Phase 13 establishes a controlled foundation for future persistent and intelligent memory.

It intentionally does less rather than silently collecting everything.

Future phases may make memory smarter.
They must not make memory more authoritative.

Phase 13 principle:

Remember useful information. Never remember permission.