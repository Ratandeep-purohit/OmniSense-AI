from omnisense_ai.app import HealthStatus, health_check
from omnisense_ai.config import AppConfig, CaptureConfig


def test_health_check_reports_ok_status() -> None:
    status = health_check(
        AppConfig(
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
    )

    assert status == HealthStatus(status="ok", environment="test")
