import re

import pytest

from omnisense_ai.telemetry import TelemetryEvent, new_operation


def test_operation_context_has_unique_correlation_id() -> None:
    first = new_operation("foundation")
    second = new_operation("foundation")

    assert first.component == "foundation"
    assert first.operation_id != second.operation_id
    assert re.fullmatch(r"[0-9a-f]{32}", first.operation_id)


def test_telemetry_event_contains_only_safe_metadata() -> None:
    context = new_operation("foundation")
    event = TelemetryEvent.create(context, "startup", success=True)

    assert event.operation_id == context.operation_id
    assert event.component == "foundation"
    assert event.event == "startup"
    assert event.success is True


def test_empty_component_and_event_are_rejected() -> None:
    with pytest.raises(ValueError):
        new_operation(" ")
    context = new_operation("foundation")
    with pytest.raises(ValueError):
        TelemetryEvent.create(context, " ", success=False)
