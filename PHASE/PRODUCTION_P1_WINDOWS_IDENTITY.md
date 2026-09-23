# Production P1 — Windows Foundation & Identity

## Objective

Establish a real Windows identity boundary that can distinguish:

1. a logical application discovered from Windows-owned launch metadata;
2. a concrete process instance;
3. a concrete top-level window bound to that process instance.

PID or process name alone is never treated as sufficient identity because Windows can reuse PIDs and applications can spawn helper processes.

## Implemented

### Logical application identity
`ApplicationIdentity` contains:

- canonical `application_id`
- display name
- trusted launch target
- discovery source
- known process names
- executable path when known
- AUMID when applicable
- adapter identifier
- aliases

### Process identity

`ProcessIdentity` binds:

- PID
- full executable path
- process name
- Windows process creation timestamp
- session ID

Process equality requires PID + creation time + normalized executable path.

### Window identity

`WindowIdentity` binds:

- HWND
- process instance identity
- title
- Win32 class name
- current visibility

Window equality requires HWND plus the same process instance.

### Runtime Windows API

`ApplicationIdentityService` uses read-only Win32 APIs:

- `OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION)`
- `QueryFullProcessImageNameW`
- `GetProcessTimes`
- `ProcessIdToSessionId`
- `IsWindow`
- `GetWindowThreadProcessId`
- `GetWindowTextW`
- `GetClassNameW`
- `IsWindowVisible`

It does not launch, terminate, focus, inject into, or modify processes.

## Security boundary

The identity service is observation-only. It produces evidence for later layers:

`Discovery → Identity → Adapter/UIA → Action Authorization → Execution → Verification`

No identity result grants execution permission.

## Failure behavior

- non-Windows runtime: explicit `ApplicationIdentityError`
- invalid PID/HWND: validation error
- inaccessible process: identity error
- exited/reused PID during comparison: comparison returns `False`
- invalid/empty executable metadata: identity is rejected

## Tests

Portable tests cover:

- PID reuse protection
- executable/creation-time validation
- HWND + process-instance binding
- logical identity conversion
- non-Windows behavior

Windows E2E validation must additionally prove that a live process can be resolved to its executable path and creation time and that a real HWND is bound to that exact process instance.

## Acceptance criteria

P1 is complete only when:

- [x] logical application identity contract exists
- [x] process-instance identity exists
- [x] HWND identity is process-bound
- [x] Win32 implementation reads real runtime identity
- [x] PID reuse cannot produce a positive identity match
- [x] service is observation-only
- [x] unit tests cover identity semantics
- [ ] Windows smoke/E2E validation has been executed on the target environment

The final unchecked item is an environment validation item, not a code placeholder.
