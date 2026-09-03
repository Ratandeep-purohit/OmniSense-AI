"""Minimal Phase 0 application entry point and health check."""

from __future__ import annotations

from dataclasses import dataclass

from .config import AppConfig, load_config
from .logging_config import configure_logging


@dataclass(frozen=True, slots=True)
class HealthStatus:
    """The minimal health response exposed by the Phase 0 foundation."""

    status: str
    environment: str


def health_check(config: AppConfig | None = None) -> HealthStatus:
    """Return a deterministic health result without starting future-phase services."""

    active_config = load_config() if config is None else config
    return HealthStatus(status="ok", environment=active_config.environment)


def main() -> int:
    """Start the Phase 0 foundation and report its health."""

    config = load_config()
    logger = configure_logging(config.log_level)
    status = health_check(config)
    logger.info("OmniSense AI Phase 0 foundation started in %s environment.", status.environment)
    return 0
