import pytest

from omnisense_ai.security import SecurityConfig, SecurityService, SecurityStatus
from omnisense_ai.security.errors import SecurityDisabledError, SecurityInputError, SecurityPolicyError


def test_inspect_text_is_bounded_and_redacts_secret() -> None:
    result = SecurityService().inspect_text("hello api_key=super-secret-value")
    assert result.status is SecurityStatus.SAFE
    assert "[REDACTED]" in result.sanitized_text
    assert "super-secret-value" not in result.sanitized_text
    assert result.redacted is True
    assert result.inspected_at.tzinfo is not None


def test_inspect_text_removes_control_characters() -> None:
    result = SecurityService().inspect_text("hello\x00world\x1b")
    assert result.sanitized_text == "helloworld"
    assert "control_characters_removed" in result.reasons


def test_inspect_text_rejects_oversized_input() -> None:
    with pytest.raises(SecurityPolicyError):
        SecurityService(SecurityConfig(max_input_length=4)).inspect_text("12345")


def test_identifier_is_normalized() -> None:
    assert SecurityService().validate_identifier("  app_01  ") == "app_01"


@pytest.mark.parametrize("value", ["", "bad space", "bad\nvalue", "bad?query"])
def test_identifier_rejects_unsafe_values(value: str) -> None:
    with pytest.raises((SecurityInputError, SecurityPolicyError)):
        SecurityService().validate_identifier(value)


def test_identifier_length_is_bounded() -> None:
    with pytest.raises(SecurityPolicyError):
        SecurityService(SecurityConfig(max_identifier_length=3)).validate_identifier("abcd")


def test_https_url_is_allowed() -> None:
    assert SecurityService().validate_url("https://example.com/path") == "https://example.com/path"


def test_non_https_url_is_rejected_by_default() -> None:
    with pytest.raises(SecurityPolicyError):
        SecurityService().validate_url("http://example.com")


def test_url_credentials_are_rejected() -> None:
    with pytest.raises(SecurityPolicyError):
        SecurityService().validate_url("https://user:password@example.com")


def test_url_without_host_is_rejected() -> None:
    with pytest.raises(SecurityPolicyError):
        SecurityService().validate_url("https:///missing-host")


def test_metadata_is_bounded_and_redacted() -> None:
    result = SecurityService().validate_metadata({"component": "assistant", "token": "secret-value"})
    assert result["component"] == "assistant"
    assert result["token"] == "[REDACTED]"


def test_metadata_item_limit() -> None:
    with pytest.raises(SecurityPolicyError):
        SecurityService(SecurityConfig(max_metadata_items=1)).validate_metadata({"a": "1", "b": "2"})


def test_metadata_value_limit() -> None:
    with pytest.raises(SecurityPolicyError):
        SecurityService(SecurityConfig(max_metadata_value_length=3)).validate_metadata({"a": "1234"})


def test_disabled_service_rejects_operations() -> None:
    with pytest.raises(SecurityDisabledError):
        SecurityService(SecurityConfig(enabled=False)).inspect_text("hello")


def test_closed_service_rejects_operations() -> None:
    service = SecurityService()
    service.close()
    with pytest.raises(SecurityInputError):
        service.inspect_text("hello")


def test_custom_url_scheme_policy() -> None:
    service = SecurityService(SecurityConfig(allowed_url_schemes=frozenset({"https", "http"})))
    assert service.validate_url("http://example.com") == "http://example.com"
