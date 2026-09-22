"""Validated screen capture data contracts."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from .errors import InvalidCaptureRegionError
class CaptureState(str, Enum): STOPPED="stopped"; RUNNING="running"; PAUSED="paused"
class FrameSource(str, Enum): MONITOR="monitor"; REGION="region"
class PixelFormat(str, Enum): BGRA="BGRA"
@dataclass(frozen=True, slots=True)
class CaptureRegion:
    x:int; y:int; width:int; height:int
    def __post_init__(self):
        if self.width<=0 or self.height<=0: raise InvalidCaptureRegionError("Capture region width and height must be positive.")
    @property
    def right(self): return self.x+self.width
    @property
    def bottom(self): return self.y+self.height
@dataclass(frozen=True, slots=True)
class MonitorInfo:
    id:str; x:int; y:int; width:int; height:int; is_primary:bool=False; scale_factor:float|None=None; name:str|None=None
    def __post_init__(self):
        if not self.id.strip(): raise ValueError("Monitor id must not be empty.")
        if self.width<=0 or self.height<=0: raise ValueError("Monitor width and height must be positive.")
        if self.scale_factor is not None and self.scale_factor<=0: raise ValueError("Monitor scale factor must be positive when provided.")
    @property
    def region(self): return CaptureRegion(self.x,self.y,self.width,self.height)
    def contains_region(self, region): return region.x>=self.x and region.y>=self.y and region.right<=self.x+self.width and region.bottom<=self.y+self.height
@dataclass(frozen=True, slots=True)
class ScreenFrame:
    data:bytes; width:int; height:int; pixel_format:str; monitor_id:str; source:FrameSource; captured_at:datetime=field(default_factory=lambda:datetime.now(timezone.utc)); region:CaptureRegion|None=None
    def __post_init__(self):
        if not self.data: raise ValueError("Screen frame data must not be empty.")
        if self.width<=0 or self.height<=0: raise ValueError("Screen frame width and height must be positive.")
        if not self.pixel_format.strip(): raise ValueError("Screen frame pixel format must not be empty.")
        if not self.monitor_id.strip(): raise ValueError("Screen frame monitor id must not be empty.")
        if self.captured_at.tzinfo is None: raise ValueError("Screen frame timestamp must be timezone-aware.")
        if self.region is not None and (self.region.width!=self.width or self.region.height!=self.height): raise ValueError("Screen frame dimensions must match the capture region dimensions.")
        if self.pixel_format.upper()==PixelFormat.BGRA.value and len(self.data)!=self.width*self.height*4: raise ValueError(f"BGRA frame data must contain exactly {self.width*self.height*4} bytes.")
