"""Controlled screen capture service."""
from __future__ import annotations
import logging, threading, time
from collections.abc import Sequence
from ..config import CaptureConfig
from .backend import ScreenCaptureBackend
from .errors import CaptureBackendError,CaptureNotActiveError,CapturePermissionError,CaptureRateLimitError,InvalidCaptureRegionError,MonitorNotFoundError
from .models import CaptureRegion,CaptureState,MonitorInfo,ScreenFrame
class ScreenCaptureService:
    def __init__(self,backend:ScreenCaptureBackend,config:CaptureConfig,logger:logging.Logger|None=None):
        self._backend=backend; self._config=config; self._logger=logger or logging.getLogger("omnisense_ai"); self._state=CaptureState.STOPPED; self._lock=threading.RLock(); self._last_capture_at=None; self._closed=False
    @property
    def state(self):
        with self._lock: return self._state
    def enumerate_monitors(self)->Sequence[MonitorInfo]:
        with self._lock:
            if self._closed: raise CaptureBackendError("Screen capture service is closed.")
            return tuple(self._backend.enumerate_monitors())
    def start(self):
        with self._lock:
            if not self._config.is_enabled: raise CapturePermissionError("Screen capture is disabled by configuration.")
            if self._closed: raise CaptureBackendError("Screen capture service has been closed.")
            if self._state is CaptureState.RUNNING: return
            try: self._backend.open()
            except AttributeError: pass
            except Exception as exc: raise CaptureBackendError("Unable to open screen capture backend.") from exc
            self._state=CaptureState.RUNNING; self._last_capture_at=None; self._logger.info("Screen capture started.")
    def stop(self):
        with self._lock:
            if self._state is CaptureState.STOPPED: return
            self._state=CaptureState.STOPPED; self._last_capture_at=None
            try: self._backend.close()
            finally: self._logger.info("Screen capture stopped.")
    def pause(self):
        with self._lock: self._ensure_running(); self._state=CaptureState.PAUSED; self._logger.info("Screen capture paused.")
    def resume(self):
        with self._lock:
            if self._state is not CaptureState.PAUSED: raise CaptureNotActiveError("Screen capture is not paused.")
            self._state=CaptureState.RUNNING; self._last_capture_at=None; self._logger.info("Screen capture resumed.")
    def capture_selected_monitor(self):
        with self._lock:
            self._ensure_running(); monitor=self._select_monitor(self._config.monitor_id); self._enforce_rate_limit(); return self._capture(self._backend.capture_monitor,monitor)
    def capture_region(self,region:CaptureRegion,monitor_id:str|None=None):
        with self._lock:
            self._ensure_running(); monitor=self._select_monitor(monitor_id or self._config.monitor_id); self._validate_region(monitor,region); self._enforce_rate_limit(); return self._capture(self._backend.capture_region,monitor,region)
    def capture_configured_region_or_monitor(self): return self.capture_selected_monitor() if self._config.region is None else self.capture_region(CaptureRegion(*self._config.region))
    def close(self):
        with self._lock:
            if self._closed: return
            self._state=CaptureState.STOPPED; self._last_capture_at=None; self._closed=True; self._backend.close(); self._logger.info("Screen capture service closed.")
    def _ensure_running(self):
        if self._state is CaptureState.STOPPED: raise CaptureNotActiveError("Screen capture is not started.")
        if self._state is CaptureState.PAUSED: raise CaptureNotActiveError("Screen capture is paused.")
    def _select_monitor(self,monitor_id):
        monitors=list(self.enumerate_monitors())
        if monitor_id=="primary":
            for m in monitors:
                if m.is_primary:return m
            if monitors:return monitors[0]
        for m in monitors:
            if m.id==monitor_id:return m
        raise MonitorNotFoundError(f"Monitor '{monitor_id}' was not found.")
    @staticmethod
    def _validate_region(monitor,region):
        if not monitor.contains_region(region): raise InvalidCaptureRegionError("Capture region must be inside the selected monitor.")
    def _enforce_rate_limit(self):
        now=time.monotonic()
        if self._last_capture_at is not None:
            minimum=max(1.0/self._config.max_fps,self._config.interval_ms/1000.0)
            if now-self._last_capture_at<minimum: raise CaptureRateLimitError("Capture request exceeds the configured frame-rate/interval limit.")
        self._last_capture_at=now
    def _capture(self,operation,*args):
        try: frame=operation(*args)
        except CaptureBackendError: raise
        except Exception as exc: raise CaptureBackendError("Screen capture backend failed.") from exc
        if frame.monitor_id!=args[0].id: raise CaptureBackendError("Capture backend returned a frame for the wrong monitor.")
        return frame
