"""Structured screen capture data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from .errors import InvalidCaptureRegionError


class CaptureState(str, Enum):
    """Lifecycle states for controlled screen capture."""

    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


class FrameSource(str, Enum):
    """Where a captured frame came from."""

    MONITOR = "monitor"
    REGION = "region"


@dataclass(frozen=True, slots=True)
class CaptureRegion:
    """A rectangular screen region."""

    x: int
    y: int
    width: int
    height: int

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise InvalidCaptureRegionError("Capture region width and height must be positive.")

    @property
    def right(self) -> int:
        """Return the right edge of the region."""

        return self.x + self.width

    @property
    def bottom(self) -> int:
        """Return the bottom edge of the region."""

        return self.y + self.height


@dataclass(frozen=True, slots=True)
class MonitorInfo:
    """Metadata for one available monitor."""

    id: str
    x: int
    y: int
    width: int
    height: int
    is_primary: bool = False
    scale_factor: float | None = None
    name: str | None = None

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Monitor id must not be empty.")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Monitor width and height must be positive.")
        if self.scale_factor is not None and self.scale_factor <= 0:
            raise ValueError("Monitor scale factor must be positive when provided.")

    @property
    def region(self) -> CaptureRegion:
        """Return a region covering this monitor."""

        return CaptureRegion(self.x, self.y, self.width, self.height)

    def contains_region(self, region: CaptureRegion) -> bool:
        """Return whether the supplied region is inside this monitor."""

        return (
            region.x >= self.x
            and region.y >= self.y
            and region.right <= self.x + self.width
            and region.bottom <= self.y + self.height
        )


@dataclass(frozen=True, slots=True)
class ScreenFrame:
    """An in-memory screen frame plus safe metadata."""

    data: bytes
    width: int
    height: int
    pixel_format: str
    monitor_id: str
    source: FrameSource
    captured_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    region: CaptureRegion | None = None

    def __post_init__(self) -> None:
        if not self.data:
            raise ValueError("Screen frame data must not be empty.")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Screen frame width and height must be positive.")
        if not self.pixel_format.strip():
            raise ValueError("Screen frame pixel format must not be empty.")
        if not self.monitor_id.strip():
            raise ValueError("Screen frame monitor id must not be empty.")
        if self.region is not None and (
            self.region.width != self.width or self.region.height != self.height
        ):
            raise ValueError("Screen frame dimensions must match the capture region dimensions.")
