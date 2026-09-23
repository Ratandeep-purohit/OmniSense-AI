# OmniSense AI Production Engineering

Control plane: AI/VLM → Intent → Action Graph → Preconditions → Safety → Capability → Automation → Temporal Verification → Observability.

No downstream component accepts arbitrary shell commands, arbitrary executable paths, or model-generated code as execution authority.

Windows-owned discovery sources produce canonical application identities. Launch targets are revalidated immediately before execution. Verification consumes the same identity rather than a hard-coded application allowlist.

Semantic targeting uses Microsoft UI Automation through pywinauto's UIA backend when installed. Coordinates are a weaker fallback and cannot alone prove application identity.

A failed mutation is never silently retried. Recovery can refresh context or construct a new plan; a new mutation must cross safety and capability boundaries again.

A release is incomplete until installer, clean-machine launch, update, uninstall, diagnostics and the application compatibility matrix are validated on Windows.
