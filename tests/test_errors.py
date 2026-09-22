from omnisense_ai.errors import ConfigurationError, ErrorCode, OmniSenseError


def test_configuration_error_is_typed_and_value_error_compatible() -> None:
    error = ConfigurationError("bad config")

    assert isinstance(error, OmniSenseError)
    assert isinstance(error, ValueError)
    assert error.code is ErrorCode.CONFIGURATION
    assert error.retryable is False
