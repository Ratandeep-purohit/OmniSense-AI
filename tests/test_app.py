from omnisense_ai.app import HealthStatus, health_check
from omnisense_ai.config import AppConfig, CaptureConfig


def _config() -> AppConfig:
    return AppConfig(
        environment="test",
        log_level="INFO",
        capture=CaptureConfig(
            is_enabled=False,
            monitor_id="primary",
            interval_ms=1000,
            max_fps=1.0,
            region=None,
        ),
    )


def test_health_check_reports_created_foundation_status() -> None:
    status = health_check(_config())

    assert status == HealthStatus(
        status="ok",
        environment="test",
        runtime_state="created",
        generation=0,
    )
