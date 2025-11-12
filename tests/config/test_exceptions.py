"""Tests for configuration exceptions"""

from mcp_remote_exec.config.exceptions import ConfigError


class TestConfigError:
    """Tests for ConfigError"""

    def test_basic_exception(self):
        """Test basic exception creation"""
        error = ConfigError("Configuration invalid")
        assert str(error) == "Configuration invalid"
        assert error.config_key is None
        assert error.reason is None

    def test_exception_with_config_key(self):
        """Test exception with config key"""
        error = ConfigError("Missing configuration", config_key="HOST")
        assert error.config_key == "HOST"
        assert str(error) == "Missing configuration"

    def test_exception_with_reason(self):
        """Test exception with reason"""
        error = ConfigError("Invalid value", reason="invalid")
        assert error.reason == "invalid"

    def test_exception_with_all_attributes(self):
        """Test exception with all attributes"""
        error = ConfigError(
            "SSH key file not found",
            config_key="SSH_KEY",
            reason="not_found",
        )
        assert str(error) == "SSH key file not found"
        assert error.config_key == "SSH_KEY"
        assert error.reason == "not_found"

    def test_exception_is_standard_exception(self):
        """Test that ConfigError inherits from Exception"""
        error = ConfigError("Config error")
        assert isinstance(error, Exception)

    def test_exception_with_various_reasons(self):
        """Test exception with various reason categories"""
        # Test missing reason
        error1 = ConfigError("Missing HOST", config_key="HOST", reason="missing")
        assert error1.reason == "missing"

        # Test invalid reason
        error2 = ConfigError("Invalid timeout", config_key="TIMEOUT", reason="invalid")
        assert error2.reason == "invalid"

        # Test not_found reason
        error3 = ConfigError("Key not found", config_key="SSH_KEY", reason="not_found")
        assert error3.reason == "not_found"

    def test_exception_message_formatting(self):
        """Test that exception message is preserved correctly"""
        message = "Risk acceptance not provided. Set I_ACCEPT_RISKS=true"
        error = ConfigError(message, config_key="I_ACCEPT_RISKS", reason="missing")
        assert str(error) == message
        assert message in repr(error)
