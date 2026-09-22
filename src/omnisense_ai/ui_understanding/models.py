"""Validated contracts for Phase 5 UI and visual understanding."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class UIElementType(StrEnum):
    TEXT = "text"
    LABEL = "label"
    BUTTON = "button"
    INPUT = "input"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    LINK = "link"
    MENU = "menu"
    TAB = "tab"
    TABLE = "table"
    ICON = "icon"
    IMAGE = "image"
    REGION = "region"
    UNKNOWN = "unknown"


class UIConfidenceLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class UIElementState(StrEnum):
    UNKNOWN = "unknown"
    ENABLED = "enabled"
    DISABLED = "disabled"
    SELECTED = "selected"
    FOCUSED = "focused"


@dataclass(frozen=True, slots=True)
class UIBox:
    left: int
    top: int
    width: int
    height: int

    def __post_init__(self) -> None:
        if self.left < 0 or self.top < 0:
            raise ValueError("UI box origin must not be negative.")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("UI box dimensions must be positive.")

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height

    @property
    def area(self) -> int:
        return self.width * self.height

    def intersection_area(self, other: "UIBox") -> int:
        left = max(self.left, other.left)
        top = max(self.top, other.top)
        right = min(self.right, other.right)
        bottom = min(self.bottom, other.bottom)
        return max(0, right - left) * max(0, bottom - top)

    def iou(self, other: "UIBox") -> float:
        intersection = self.intersection_area(other)
        union = self.area + other.area - intersection
        return intersection / union if union else 0.0


@dataclass(frozen=True, slots=True)
class UIElement:
    element_id: str
    element_type: UIElementType
    box: UIBox
    text: str = ""
    confidence: float = 0.0
    confidence_level: UIConfidenceLevel = UIConfidenceLevel.LOW
    state: UIElementState = UIElementState.UNKNOWN
    source: tuple[str, ...] = field(default_factory=tuple)
    parent_id: str | None = None
    related_ids: tuple[str, ...] = field(default_factory=tuple)
    interactable_observation: bool = False

    def __post_init__(self) -> None:
        if not self.element_id.strip():
            raise ValueError("UI element ID is required.")
        if not 0 <= self.confidence <= 1:
            raise ValueError("UI confidence must be within 0..1.")
        if any(not item.strip() for item in self.source):
            raise ValueError("UI provenance entries must not be empty.")
        if len(self.text) > 4096:
            raise ValueError("UI element text exceeds the supported limit.")


@dataclass(frozen=True, slots=True)
class UIRelationship:
    source_id: str
    target_id: str
    relation: str
    confidence: float

    def __post_init__(self) -> None:
        if not self.source_id or not self.target_id:
            raise ValueError("UI relationship endpoints are required.")
        if self.source_id == self.target_id:
            raise ValueError("UI relationship cannot point to itself.")
        if not self.relation.strip():
            raise ValueError("UI relationship type is required.")
        if not 0 <= self.confidence <= 1:
            raise ValueError("Relationship confidence must be within 0..1.")


@dataclass(frozen=True, slots=True)
class UIUnderstandingConfig:
    min_element_confidence: float = 0.45
    max_elements: int = 2_000
    max_relationships: int = 5_000
    max_text_length: int = 20_000
    association_distance_px: int = 160

    def __post_init__(self) -> None:
        if not 0 <= self.min_element_confidence <= 1:
            raise ValueError("Minimum element confidence must be within 0..1.")
        if self.max_elements <= 0 or self.max_elements > 20_000:
            raise ValueError("Maximum UI element count is out of bounds.")
        if self.max_relationships <= 0 or self.max_relationships > 100_000:
            raise ValueError("Maximum UI relationship count is out of bounds.")
        if self.max_text_length <= 0 or self.max_text_length > 1_000_000:
            raise ValueError("Maximum UI text length is out of bounds.")
        if self.association_distance_px < 0 or self.association_distance_px > 10_000:
            raise ValueError("Association distance is out of bounds.")


@dataclass(frozen=True, slots=True)
class UIUnderstandingResult:
    elements: tuple[UIElement, ...]
    relationships: tuple[UIRelationship, ...]
    window_id: int | None
    monitor_id: str | None
    source_sequence: int
    source_types: tuple[str, ...]
    truncated: bool = False

    def __post_init__(self) -> None:
        if self.source_sequence < 1:
            raise ValueError("UI source sequence must be >= 1.")
        if any(not item.strip() for item in self.source_types):
            raise ValueError("UI source types must not be empty.")
