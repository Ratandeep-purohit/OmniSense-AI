"""Centralized, environment-based configuration for OmniSense AI."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import os

from .errors import ConfigurationError

_VALID_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})
_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES = frozenset({"0", "false", "no", "off"})
_MIN_CAPTURE_INTERVAL_MS = 100
_MAX_CAPTURE_FPS = 10.0
_MAX_ENVIRONMENT_LENGTH = 64
_MAX_MONITOR_ID_LENGTH = 64


@dataclass(frozen=True, slots=True)
class CaptureConfig:
    """Non-sensitive configuration for controlled screen capture."""

    is_enabled: bool
    monitor_id: str
    interval_ms: int
    max_fps: float
    region: tuple[int, int, int, int] | None


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Validated, immutable application configuration."""

    environment: str
    log_level: str
    capture: CaptureConfig


def load_config(environment: Mapping[str, str] | None = None) -> AppConfig:
    """Load and validate non-sensitive settings from the process environment."""

    source = os.environ if environment is None else environment
    app_environment = source.get("OMNISENSE_ENVIRONMENT", "development").strip() or "development"
    if len(app_environment) > _MAX_ENVIRONMENT_LENGTH:
        raise ConfigurationError("OMNISENSE_ENVIRONMENT is too long.")

    log_level = source.get("OMNISENSE_LOG_LEVEL", "INFO").strip().upper() or "INFO"
    if log_level not in _VALID_LOG_LEVELS:
        raise ConfigurationError(
            "OMNISENSE_LOG_LEVEL must be one of: " + ", ".join(sorted(_VALID_LOG_LEVELS))
        )

    monitor_id = source.get("OMNISENSE_CAPTURE_MONITOR_ID", "primary").strip() or "primary"
    if len(monitor_id) > _MAX_MONITOR_ID_LENGTH:
        raise ConfigurationError("OMNISENSE_CAPTURE_MONITOR_ID is too long.")

    return AppConfig(
        environment=app_environment,
        log_level=log_level,
        capture=CaptureConfig(
            is_enabled=_parse_bool(source.get("OMNISENSE_CAPTURE_ENABLED", "false")),
            monitor_id=monitor_id,
            interval_ms=_parse_positive_int(
                source.get("OMNISENSE_CAPTURE_INTERVAL_MS", "1000"),
                "OMNISENSE_CAPTURE_INTERVAL_MS",
                minimum=_MIN_CAPTURE_INTERVAL_MS,
            ),
            max_fps=_parse_max_fps(source.get("OMNISENSE_CAPTURE_MAX_FPS", "1")),
            region=_parse_region(source.get("OMNISENSE_CAPTURE_REGION", "")),
        ),
    )


def get_environment_secret(name: str, environment: Mapping[str, str] | None = None) -> str | None:
    """Return a secret from the environment without logging or persisting it."""

    if not name or not name.strip():
        raise ValueError("Secret environment-variable name must not be empty.")
    source = os.environ if environment is None else environment
    return source.get(name)


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise ConfigurationError("OMNISENSE_CAPTURE_ENABLED must be a boolean value.")


def _parse_positive_int(value: str, name: str, *, minimum: int) -> int:
    try:
        parsed = int(value.strip())
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer.") from exc
    if parsed < minimum:
        raise ConfigurationError(f"{name} must be at least {minimum}.")
    return parsed


def _parse_max_fps(value: str) -> float:
    try:
        parsed = float(value.strip())
    except ValueError as exc:
        raise ConfigurationError("OMNISENSE_CAPTURE_MAX_FPS must be a number.") from exc
    if parsed <= 0 or parsed > _MAX_CAPTURE_FPS:
        raise ConfigurationError(
            f"OMNISENSE_CAPTURE_MAX_FPS must be greater than 0 and at most {_MAX_CAPTURE_FPS:g}."
        )
    return parsed


def _parse_region(value: str) -> tuple[int, int, int, int] | None:
    normalized = value.strip()
    if not normalized:
        return None
    parts = [part.strip() for part in normalized.split(",")]
    if len(parts) != 4:
        raise ConfigurationError("OMNISENSE_CAPTURE_REGION must use x,y,width,height format.")
    try:
        x, y, width, height = (int(part) for part in parts)
    except ValueError as exc:
        raise ConfigurationError("OMNISENSE_CAPTURE_REGION values must be integers.") from exc
    if width <= 0 or height <= 0:
        raise ConfigurationError("OMNISENSE_CAPTURE_REGION width and height must be positive.")
    return (x, y, width, height)
