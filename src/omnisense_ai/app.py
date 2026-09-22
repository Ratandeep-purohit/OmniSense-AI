"""Phase 0 application bootstrap, lifecycle, and health checks."""

from __future__ import annotations

from dataclasses import dataclass

from .config import AppConfig, load_config
from .logging_config import configure_logging
from .runtime import ApplicationRuntime, RuntimeSnapshot


@dataclass(frozen=True, slots=True)
class HealthStatus:
    """Deterministic health response for the foundation."""

    status: str
    environment: str
    runtime_state: str
    generation: int


def health_check(
    config: AppConfig | None = None,
    runtime: ApplicationRuntime | None = None,
) -> HealthStatus:
    """Return health without starting future-phase services."""

    active_config = load_config() if config is None else config
    snapshot = runtime.snapshot() if runtime is not None else RuntimeSnapshot(
        state="created",
        environment=active_config.environment,
        generation=0,
    )
    return HealthStatus(
        status="ok" if snapshot.state != "failed" else "degraded",
        environment=active_config.environment,
        runtime_state=snapshot.state.value if hasattr(snapshot.state, "value") else str(snapshot.state),
        generation=snapshot.generation,
    )


def bootstrap(config: AppConfig | None = None) -> tuple[ApplicationRuntime, HealthStatus]:
    """Create and start the Phase 0 runtime only."""

    active_config = load_config() if config is None else config
    runtime = ApplicationRuntime(active_config)
    runtime.start()
    return runtime, health_check(active_config, runtime)


def main() -> int:
    """Start the foundation and report its health."""

    config = load_config()
    logger = configure_logging(config.log_level)
    runtime, status = bootstrap(config)
    logger.info(
        "OmniSense AI foundation started: environment=%s state=%s generation=%d",
        status.environment,
        status.runtime_state,
        status.generation,
    )
    runtime.stop()
    return 0
