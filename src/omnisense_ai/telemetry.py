"""Bounded, in-process telemetry primitives for the foundation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class OperationContext:
    """Correlation metadata that contains no screen content or secrets."""

    operation_id: str
    component: str

    @classmethod
    def create(cls, component: str) -> "OperationContext":
        normalized = component.strip()
        if not normalized:
            raise ValueError("Telemetry component must not be empty.")
        return cls(operation_id=uuid4().hex, component=normalized)


@dataclass(frozen=True, slots=True)
class TelemetryEvent:
    timestamp: datetime
    operation_id: str
    component: str
    event: str
    success: bool

    @classmethod
    def create(
        cls,
        context: OperationContext,
        event: str,
        *,
        success: bool,
    ) -> "TelemetryEvent":
        normalized = event.strip()
        if not normalized:
            raise ValueError("Telemetry event must not be empty.")
        return cls(
            timestamp=datetime.now(timezone.utc),
            operation_id=context.operation_id,
            component=context.component,
            event=normalized,
            success=success,
        )


def new_operation(component: str) -> OperationContext:
    """Create a correlation context for one bounded operation."""
    return OperationContext.create(component)
