"""Structured bounded observability without secrets or screenshots."""
from dataclasses import dataclass,asdict
from datetime import datetime,timezone
from collections import deque
import json,time
@dataclass(frozen=True,slots=True)
class Event:
    name:str; timestamp:str; trace_id:str; status:str; duration_ms:float=0.0; fields:tuple[tuple[str,str],...]=()
class EventLog:
    def __init__(self,max_events:int=5000): self._events=deque(maxlen=max_events)
    def emit(self,name,trace_id,status="ok",started=None,**fields):
        duration=0.0 if started is None else max(0.0,(time.perf_counter()-started)*1000)
        clean=tuple((str(k),self._redact(str(v))) for k,v in fields.items() if k not in {"text","screenshot","ocr","secret","token","password"})
        self._events.append(Event(name,datetime.now(timezone.utc).isoformat(),trace_id,status,duration,clean))
    @staticmethod
    def _redact(value): return "[REDACTED]" if len(value)>256 else value
    def snapshot(self): return tuple(self._events)
    def jsonl(self): return "\n".join(json.dumps(asdict(e)) for e in self._events)
