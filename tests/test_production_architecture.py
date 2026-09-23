import pytest
from omnisense_ai.capabilities import Capability,CapabilityManager
from omnisense_ai.recovery import RecoveryAction,RecoveryEngine
from omnisense_ai.observability import EventLog
from omnisense_ai.compatibility import check_windows_compatibility
from omnisense_ai.e2e import WindowsE2EHarness

def test_capability_grant_and_revoke():
    m=CapabilityManager(ttl_seconds=1); m.grant(Capability.EXECUTE,"session")
    assert m.has(Capability.EXECUTE); m.revoke(Capability.EXECUTE); assert not m.has(Capability.EXECUTE)

def test_recovery_never_silently_retries_mutation():
    assert RecoveryEngine(2).decide(attempt=1,error="desktop action failed").action is RecoveryAction.ASK_USER

def test_observability_redacts_sensitive_fields():
    log=EventLog(); log.emit("action","trace",token="secret",message="ok")
    data=log.jsonl(); assert "secret" not in data and "ok" in data

def test_e2e_is_opt_in():
    with pytest.raises(RuntimeError): WindowsE2EHarness().require_enabled()

def test_compatibility_report():
    r=check_windows_compatibility(); assert r.os_version and r.python_version and r.architecture
