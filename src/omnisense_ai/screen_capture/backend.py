"""Screen capture backend interfaces and the mss implementation."""
from __future__ import annotations
from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Protocol
from .errors import CaptureBackendError
from .models import CaptureRegion, FrameSource, MonitorInfo, PixelFormat, ScreenFrame
class ScreenCaptureBackend(Protocol):
    def open(self)->None: ...
    def enumerate_monitors(self)->Sequence[MonitorInfo]: ...
    def capture_monitor(self, monitor:MonitorInfo)->ScreenFrame: ...
    def capture_region(self, monitor:MonitorInfo, region:CaptureRegion)->ScreenFrame: ...
    def close(self)->None: ...
class MssScreenCaptureBackend:
    def __init__(self):
        try: import mss
        except ImportError as exc: raise CaptureBackendError("mss is required for real screen capture.") from exc
        self._mss_module=mss; self._capture=None; self.open()
    def open(self):
        if self._capture is not None: return
        try: self._capture=self._mss_module.mss()
        except Exception as exc: raise CaptureBackendError("Unable to initialize screen capture backend.") from exc
    def _require_open(self):
        if self._capture is None: raise CaptureBackendError("Screen capture backend is closed.")
        return self._capture
    def enumerate_monitors(self)->Sequence[MonitorInfo]:
        try:
            raw=self._require_open().monitors
            return [MonitorInfo(id=str(i),x=int(m["left"]),y=int(m["top"]),width=int(m["width"]),height=int(m["height"]),is_primary=i==1,name=f"Monitor {i}") for i,m in enumerate(raw[1:],1)]
        except CaptureBackendError: raise
        except Exception as exc: raise CaptureBackendError("Unable to enumerate monitors.") from exc
    def capture_monitor(self, monitor): return self.capture_region(monitor,monitor.region)
    def capture_region(self, monitor, region):
        try:
            s=self._require_open().grab({"left":region.x,"top":region.y,"width":region.width,"height":region.height})
            return ScreenFrame(bytes(s.raw),int(s.width),int(s.height),PixelFormat.BGRA.value,monitor.id,FrameSource.REGION if region!=monitor.region else FrameSource.MONITOR,datetime.now(timezone.utc),region)
        except CaptureBackendError: raise
        except Exception as exc: raise CaptureBackendError("Screen capture backend failed.") from exc
    def close(self):
        capture,self._capture=self._capture,None
        if capture is not None:
            try: capture.close()
            except Exception as exc: raise CaptureBackendError("Unable to close screen capture backend.") from exc
