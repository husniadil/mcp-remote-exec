"""Tests for Proxmox Plugin Configuration"""

import os
import pytest
from unittest.mock import patch

from mcp_remote_exec.plugins.proxmox.config import ProxmoxConfig


class TestProxmoxConfigFromEnv:
    """Tests for ProxmoxConfig.from_env() method"""

    @patch.dict(os.environ, {"ENABLE_PROXMOX": "true"})
    def test_from_env_enabled(self):
        """Test from_env() returns config when ENABLE_PROXMOX=true"""
        config = ProxmoxConfig.from_env()

        assert config is not None
        assert isinstance(config, ProxmoxConfig)
        assert config.enabled is True

    @patch.dict(os.environ, {"ENABLE_PROXMOX": "false"})
    def test_from_env_disabled_explicit(self):
        """Test from_env() returns None when ENABLE_PROXMOX=false"""
        config = ProxmoxConfig.from_env()

        assert config is None

    @patch.dict(os.environ, {}, clear=True)
    def test_from_env_disabled_missing(self):
        """Test from_env() returns None when ENABLE_PROXMOX is not set"""
        config = ProxmoxConfig.from_env()

        assert config is None

    @patch.dict(os.environ, {"ENABLE_PROXMOX": "TRUE"})
    def test_from_env_case_insensitive_true(self):
        """Test from_env() handles TRUE in uppercase"""
        config = ProxmoxConfig.from_env()

        assert config is not None
        assert config.enabled is True

    @patch.dict(os.environ, {"ENABLE_PROXMOX": "False"})
    def test_from_env_case_insensitive_false(self):
        """Test from_env() handles False in mixed case"""
        config = ProxmoxConfig.from_env()

        assert config is None

    @patch.dict(os.environ, {"ENABLE_PROXMOX": "yes"})
    def test_from_env_invalid_value(self):
        """Test from_env() returns None for invalid values (not 'true')"""
        config = ProxmoxConfig.from_env()

        assert config is None

    @patch.dict(os.environ, {"ENABLE_PROXMOX": "1"})
    def test_from_env_numeric_value(self):
        """Test from_env() returns None for numeric values"""
        config = ProxmoxConfig.from_env()

        assert config is None

    @patch.dict(os.environ, {"ENABLE_PROXMOX": ""})
    def test_from_env_empty_string(self):
        """Test from_env() returns None for empty string"""
        config = ProxmoxConfig.from_env()

        assert config is None


class TestProxmoxConfigDataclass:
    """Tests for ProxmoxConfig dataclass"""

    def test_default_values(self):
        """Test ProxmoxConfig with default values"""
        config = ProxmoxConfig()

        assert config.enabled is True

    def test_custom_values(self):
        """Test ProxmoxConfig with custom values"""
        config = ProxmoxConfig(enabled=False)

        assert config.enabled is False

    def test_config_is_immutable_like(self):
        """Test ProxmoxConfig fields can be modified (dataclass, not frozen)"""
        config = ProxmoxConfig(enabled=True)
        config.enabled = False

        assert config.enabled is False
