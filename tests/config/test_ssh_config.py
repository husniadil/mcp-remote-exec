"""Tests for SSH Configuration"""

import os
import pytest
from unittest.mock import patch

from mcp_remote_exec.config.exceptions import ConfigError
from mcp_remote_exec.config.ssh_config import SSHConfig, HostConfig, SecurityConfig
from mcp_remote_exec.config.constants import (
    DEFAULT_CHARACTER_LIMIT,
    DEFAULT_MAX_FILE_SIZE,
    DEFAULT_TIMEOUT,
    MAX_TIMEOUT,
    DEFAULT_SSH_PORT,
)


class TestHostConfig:
    """Tests for HostConfig dataclass"""

    def test_host_config_with_password(self):
        """Test HostConfig with password authentication"""
        config = HostConfig(
            name="test",
            host="example.com",
            port=22,
            username="user",
            password="pass",
        )
        assert config.has_auth() is True

    def test_host_config_with_key(self):
        """Test HostConfig with key authentication"""
        config = HostConfig(
            name="test",
            host="example.com",
            port=22,
            username="user",
            key_path="/path/to/key",
        )
        assert config.has_auth() is True

    def test_host_config_no_auth(self):
        """Test HostConfig without authentication"""
        config = HostConfig(
            name="test",
            host="example.com",
            port=22,
            username="user",
        )
        assert config.has_auth() is False


class TestSecurityConfig:
    """Tests for SecurityConfig dataclass"""

    def test_security_config_defaults(self):
        """Test SecurityConfig with default values"""
        config = SecurityConfig(
            accept_risks=True,
            character_limit=25000,
            max_file_size=10485760,
            default_timeout=30,
            max_timeout=300,
        )
        assert config.accept_risks is True
        assert config.strict_host_key_checking is True

    def test_security_config_custom_host_key_checking(self):
        """Test SecurityConfig with custom host key checking"""
        config = SecurityConfig(
            accept_risks=True,
            character_limit=25000,
            max_file_size=10485760,
            default_timeout=30,
            max_timeout=300,
            strict_host_key_checking=False,
        )
        assert config.strict_host_key_checking is False


class TestSSHConfig:
    """Tests for SSHConfig class"""

    def test_init_without_risk_acceptance(self):
        """Test initialization fails without risk acceptance"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigError, match="You must explicitly accept the risks"):
                SSHConfig()

    def test_init_with_risk_acceptance_false(self):
        """Test initialization fails with explicit false"""
        with patch.dict(os.environ, {"I_ACCEPT_RISKS": "false"}, clear=True):
            with pytest.raises(ConfigError, match="You must explicitly accept the risks"):
                SSHConfig()

    def test_init_without_host(self):
        """Test initialization fails without HOST"""
        with patch.dict(
            os.environ, {"I_ACCEPT_RISKS": "true"}, clear=True
        ):
            with pytest.raises(ConfigError, match="No SSH host configuration found"):
                SSHConfig()

    def test_init_without_authentication(self):
        """Test initialization fails without authentication method"""
        env = {
            "I_ACCEPT_RISKS": "true",
            "HOST": "test.example.com",
            "SSH_USERNAME": "user",
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ConfigError, match="No authentication configured"):
                SSHConfig()

    def test_init_with_password_auth(self):
        """Test successful initialization with password authentication"""
        env = {
            "I_ACCEPT_RISKS": "true",
            "HOST": "test.example.com",
            "SSH_USERNAME": "user",
            "SSH_PASSWORD": "password",
        }
        with patch.dict(os.environ, env, clear=True):
            config = SSHConfig()
            assert config.host.host == "test.example.com"
            assert config.host.username == "user"
            assert config.host.password == "password"
            assert config.host.port == 22
            assert config.security.accept_risks is True

    def test_init_with_key_auth(self, tmp_path):
        """Test successful initialization with SSH key authentication"""
        key_file = tmp_path / "test_key"
        key_file.write_text("fake ssh key")

        env = {
            "I_ACCEPT_RISKS": "true",
            "HOST": "test.example.com",
            "SSH_USERNAME": "user",
            "SSH_KEY": str(key_file),
        }
        with patch.dict(os.environ, env, clear=True):
            config = SSHConfig()
            assert config.host.key_path == str(key_file)
            assert config.host.password is None

    def test_init_with_nonexistent_key(self):
        """Test initialization fails with non-existent SSH key"""
        env = {
            "I_ACCEPT_RISKS": "true",
            "HOST": "test.example.com",
            "SSH_USERNAME": "user",
            "SSH_KEY": "/path/to/nonexistent/key",
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ConfigError, match="SSH key file not found"):
                SSHConfig()

    def test_init_with_custom_port(self):
        """Test initialization with custom SSH port"""
        env = {
            "I_ACCEPT_RISKS": "true",
            "HOST": "test.example.com",
            "SSH_USERNAME": "user",
            "SSH_PASSWORD": "password",
            "SSH_PORT": "2222",
        }
        with patch.dict(os.environ, env, clear=True):
            config = SSHConfig()
            assert config.host.port == 2222

    def test_init_with_custom_limits(self):
        """Test initialization with custom character and file size limits"""
        env = {
            "I_ACCEPT_RISKS": "true",
            "HOST": "test.example.com",
            "SSH_USERNAME": "user",
            "SSH_PASSWORD": "password",
            "CHARACTER_LIMIT": "50000",
            "MAX_FILE_SIZE": "20971520",
            "TIMEOUT": "60",
        }
        with patch.dict(os.environ, env, clear=True):
            config = SSHConfig()
            assert config.security.character_limit == 50000
            assert config.security.max_file_size == 20971520
            assert config.security.default_timeout == 60

    def test_init_with_strict_host_key_checking_false(self):
        """Test initialization with strict host key checking disabled"""
        env = {
            "I_ACCEPT_RISKS": "true",
            "HOST": "test.example.com",
            "SSH_USERNAME": "user",
            "SSH_PASSWORD": "password",
            "SSH_STRICT_HOST_KEY_CHECKING": "false",
        }
        with patch.dict(os.environ, env, clear=True):
            config = SSHConfig()
            assert config.security.strict_host_key_checking is False

    def test_init_with_strict_host_key_checking_true(self):
        """Test initialization with strict host key checking enabled"""
        env = {
            "I_ACCEPT_RISKS": "true",
            "HOST": "test.example.com",
            "SSH_USERNAME": "user",
            "SSH_PASSWORD": "password",
            "SSH_STRICT_HOST_KEY_CHECKING": "true",
        }
        with patch.dict(os.environ, env, clear=True):
            config = SSHConfig()
            assert config.security.strict_host_key_checking is True

    def test_get_host(self):
        """Test get_host method returns correct host config"""
        env = {
            "I_ACCEPT_RISKS": "true",
            "HOST": "test.example.com",
            "SSH_USERNAME": "user",
            "SSH_PASSWORD": "password",
        }
        with patch.dict(os.environ, env, clear=True):
            config = SSHConfig()
            host = config.get_host()
            assert isinstance(host, HostConfig)
            assert host.host == "test.example.com"

    def test_validate_success(self):
        """Test validate method with valid configuration"""
        env = {
            "I_ACCEPT_RISKS": "true",
            "HOST": "test.example.com",
            "SSH_USERNAME": "user",
            "SSH_PASSWORD": "password",
        }
        with patch.dict(os.environ, env, clear=True):
            config = SSHConfig()
            is_valid, error = config.validate()
            assert is_valid is True
            assert error is None

    def test_repr(self):
        """Test string representation"""
        env = {
            "I_ACCEPT_RISKS": "true",
            "HOST": "test.example.com",
            "SSH_USERNAME": "user",
            "SSH_PASSWORD": "password",
        }
        with patch.dict(os.environ, env, clear=True):
            config = SSHConfig()
            repr_str = repr(config)
            assert "SSHConfig" in repr_str
            assert "user@test.example.com:22" in repr_str
            assert "risks_accepted=True" in repr_str

    def test_default_constants(self):
        """Test default constants are set correctly"""
        assert DEFAULT_CHARACTER_LIMIT == 25000
        assert DEFAULT_MAX_FILE_SIZE == 10485760
        assert DEFAULT_TIMEOUT == 30
        assert MAX_TIMEOUT == 300
        assert DEFAULT_SSH_PORT == 22
