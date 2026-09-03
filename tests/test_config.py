import pytest

from omnisense_ai.config import get_environment_secret, load_config


def test_load_config_uses_defaults() -> None:
    config = load_config({})

    assert config.environment == "development"
    assert config.log_level == "INFO"
    assert config.capture.is_enabled is False
    assert config.capture.monitor_id == "primary"
    assert config.capture.interval_ms == 1000
    assert config.capture.max_fps == 1.0
    assert config.capture.region is None


def test_load_config_normalizes_values() -> None:
    config = load_config({"OMNISENSE_ENVIRONMENT": " test ", "OMNISENSE_LOG_LEVEL": "warning"})

    assert config.environment == "test"
    assert config.log_level == "WARNING"


def test_load_config_parses_capture_settings() -> None:
    config = load_config(
        {
            "OMNISENSE_CAPTURE_ENABLED": "true",
            "OMNISENSE_CAPTURE_MONITOR_ID": "2",
            "OMNISENSE_CAPTURE_INTERVAL_MS": "500",
            "OMNISENSE_CAPTURE_MAX_FPS": "2.5",
            "OMNISENSE_CAPTURE_REGION": "10,20,300,200",
        }
    )

    assert config.capture.is_enabled is True
    assert config.capture.monitor_id == "2"
    assert config.capture.interval_ms == 500
    assert config.capture.max_fps == 2.5
    assert config.capture.region == (10, 20, 300, 200)


@pytest.mark.parametrize(
    ("key", "value", "match"),
    [
        ("OMNISENSE_CAPTURE_ENABLED", "maybe", "boolean"),
        ("OMNISENSE_CAPTURE_INTERVAL_MS", "99", "at least"),
        ("OMNISENSE_CAPTURE_MAX_FPS", "0", "greater than 0"),
        ("OMNISENSE_CAPTURE_MAX_FPS", "60", "at most"),
        ("OMNISENSE_CAPTURE_REGION", "1,2,3", "x,y,width,height"),
        ("OMNISENSE_CAPTURE_REGION", "1,2,0,4", "positive"),
    ],
)
def test_load_config_rejects_invalid_capture_settings(key: str, value: str, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        load_config({key: value})


def test_load_config_rejects_invalid_log_level() -> None:
    with pytest.raises(ValueError, match="OMNISENSE_LOG_LEVEL"):
        load_config({"OMNISENSE_LOG_LEVEL": "verbose"})


def test_secret_is_loaded_only_from_environment_mapping() -> None:
    secret = get_environment_secret("OMNISENSE_API_KEY", {"OMNISENSE_API_KEY": "not-logged"})

    assert secret == "not-logged"


def test_secret_name_must_not_be_empty() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        get_environment_secret("", {})
