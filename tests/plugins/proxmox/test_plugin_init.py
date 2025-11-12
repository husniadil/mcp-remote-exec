"""Tests for Proxmox Plugin Registration"""

import os
import pytest
from unittest.mock import MagicMock, patch

from mcp_remote_exec.plugins.proxmox import ProxmoxPlugin
from mcp_remote_exec.presentation.service_container import ServiceContainer


@pytest.fixture
def mock_service_container():
    """Create a mock ServiceContainer"""
    container = MagicMock(spec=ServiceContainer)
    container.enabled_plugins = set()
    container.plugin_services = {}
    container.command_service = MagicMock()
    container.file_service = MagicMock()
    return container


@pytest.fixture
def proxmox_plugin():
    """Create a ProxmoxPlugin instance"""
    return ProxmoxPlugin()


class TestProxmoxPluginName:
    """Tests for plugin name property"""

    def test_plugin_name(self, proxmox_plugin):
        """Test that plugin has correct name"""
        assert proxmox_plugin.name == "proxmox"


class TestProxmoxPluginIsEnabled:
    """Tests for is_enabled method"""

    @patch.dict(os.environ, {"ENABLE_PROXMOX": "true"})
    def test_is_enabled_when_enabled(self, proxmox_plugin, mock_service_container):
        """Test is_enabled returns True when ENABLE_PROXMOX=true"""
        result = proxmox_plugin.is_enabled(mock_service_container)

        assert result is True

    @patch.dict(os.environ, {"ENABLE_PROXMOX": "false"})
    def test_is_enabled_when_disabled(self, proxmox_plugin, mock_service_container):
        """Test is_enabled returns False when ENABLE_PROXMOX=false"""
        result = proxmox_plugin.is_enabled(mock_service_container)

        assert result is False

    @patch.dict(os.environ, {}, clear=True)
    def test_is_enabled_when_not_set(self, proxmox_plugin, mock_service_container):
        """Test is_enabled returns False when ENABLE_PROXMOX is not set"""
        result = proxmox_plugin.is_enabled(mock_service_container)

        assert result is False


class TestProxmoxPluginRegisterTools:
    """Tests for register_tools method"""

    def test_register_tools_creates_service(
        self, proxmox_plugin, mock_service_container
    ):
        """Test that register_tools creates and stores ProxmoxService"""
        mock_mcp = MagicMock()

        proxmox_plugin.register_tools(mock_mcp, mock_service_container)

        # Service should be stored in container
        assert "proxmox" in mock_service_container.plugin_services
        service = mock_service_container.plugin_services["proxmox"]
        assert service is not None

    def test_register_tools_without_imagekit(
        self, proxmox_plugin, mock_service_container
    ):
        """Test register_tools when ImageKit is not enabled"""
        mock_mcp = MagicMock()
        # ImageKit not in enabled_plugins

        with patch(
            "mcp_remote_exec.plugins.proxmox.tools.register_proxmox_tools"
        ) as mock_reg_tools, patch(
            "mcp_remote_exec.plugins.proxmox.tools.register_proxmox_file_tools"
        ) as mock_reg_file_tools:
            proxmox_plugin.register_tools(mock_mcp, mock_service_container)

            # Both tool sets should be registered
            mock_reg_tools.assert_called_once()
            mock_reg_file_tools.assert_called_once()

    def test_register_tools_with_imagekit(self, proxmox_plugin, mock_service_container):
        """Test register_tools when ImageKit is enabled"""
        mock_mcp = MagicMock()
        mock_service_container.enabled_plugins = {"imagekit"}  # ImageKit enabled

        with patch(
            "mcp_remote_exec.plugins.proxmox.tools.register_proxmox_tools"
        ) as mock_reg_tools, patch(
            "mcp_remote_exec.plugins.proxmox.tools.register_proxmox_file_tools"
        ) as mock_reg_file_tools:
            proxmox_plugin.register_tools(mock_mcp, mock_service_container)

            # Only container management tools should be registered
            mock_reg_tools.assert_called_once()
            mock_reg_file_tools.assert_not_called()
