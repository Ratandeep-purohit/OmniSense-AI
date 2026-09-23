"""Capability-based session authority, separate from action planning."""
from dataclasses import dataclass
from datetime import datetime,timezone,timedelta
from threading import RLock
class Capability:
    OBSERVE="desktop.observe"; EXECUTE="desktop.execute"; UIA="desktop.uia"; MEMORY="memory.write"
@dataclass(frozen=True,slots=True)
class CapabilityGrant:
    capability:str; grant_id:str; issued_at:datetime; expires_at:datetime; source:str="user"
    def active(self,now=None): return (now or datetime.now(timezone.utc)) < self.expires_at
class CapabilityManager:
    def __init__(self,ttl_seconds:float=3600): self._ttl=ttl_seconds; self._grants={}; self._lock=RLock()
    def grant(self,capability,grant_id,*,source="user"):
        now=datetime.now(timezone.utc); g=CapabilityGrant(capability,grant_id,now,now+timedelta(seconds=self._ttl),source)
        with self._lock:self._grants[capability]=g
        return g
    def revoke(self,capability):
        with self._lock:self._grants.pop(capability,None)
    def has(self,capability,now=None):
        with self._lock:
            g=self._grants.get(capability)
            return bool(g and g.active(now))
    def active(self):
        now=datetime.now(timezone.utc)
        with self._lock:return tuple(g for g in self._grants.values() if g.active(now))
