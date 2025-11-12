"""Tests for ImageKit Plugin Registration"""

import os
import pytest
from unittest.mock import MagicMock, patch

from mcp_remote_exec.plugins.imagekit import ImageKitPlugin
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
def imagekit_plugin():
    """Create an ImageKitPlugin instance"""
    return ImageKitPlugin()


class TestImageKitPluginName:
    """Tests for plugin name property"""

    def test_plugin_name(self, imagekit_plugin):
        """Test that plugin has correct name"""
        assert imagekit_plugin.name == "imagekit"


class TestImageKitPluginIsEnabled:
    """Tests for is_enabled method"""

    @patch.dict(
        os.environ,
        {
            "ENABLE_IMAGEKIT": "true",
            "IMAGEKIT_PUBLIC_KEY": "test_public",
            "IMAGEKIT_PRIVATE_KEY": "test_private",
            "IMAGEKIT_URL_ENDPOINT": "https://ik.imagekit.io/test",
        },
    )
    def test_is_enabled_when_enabled_with_credentials(
        self, imagekit_plugin, mock_service_container
    ):
        """Test is_enabled returns True when enabled with credentials"""
        result = imagekit_plugin.is_enabled(mock_service_container)

        assert result is True
        assert imagekit_plugin._config is not None

    @patch.dict(
        os.environ,
        {
            "ENABLE_IMAGEKIT": "false",
            "IMAGEKIT_PUBLIC_KEY": "test_public",
            "IMAGEKIT_PRIVATE_KEY": "test_private",
            "IMAGEKIT_URL_ENDPOINT": "https://ik.imagekit.io/test",
        },
    )
    def test_is_enabled_when_disabled(self, imagekit_plugin, mock_service_container):
        """Test is_enabled returns False when ENABLE_IMAGEKIT=false"""
        result = imagekit_plugin.is_enabled(mock_service_container)

        assert result is False
        assert imagekit_plugin._config is None

    @patch.dict(
        os.environ,
        {
            "ENABLE_IMAGEKIT": "true",
            # Missing credentials
        },
    )
    def test_is_enabled_without_credentials(
        self, imagekit_plugin, mock_service_container
    ):
        """Test is_enabled returns False when credentials are missing"""
        result = imagekit_plugin.is_enabled(mock_service_container)

        assert result is False
        assert imagekit_plugin._config is None

    @patch.dict(os.environ, {}, clear=True)
    def test_is_enabled_when_not_set(self, imagekit_plugin, mock_service_container):
        """Test is_enabled returns False when not configured"""
        result = imagekit_plugin.is_enabled(mock_service_container)

        assert result is False


class TestImageKitPluginRegisterTools:
    """Tests for register_tools method"""

    def test_register_tools_creates_service(
        self, imagekit_plugin, mock_service_container
    ):
        """Test that register_tools creates and stores ImageKitService"""
        mock_mcp = MagicMock()
        imagekit_plugin._config = MagicMock()  # Simulate cached config

        with patch(
            "mcp_remote_exec.plugins.imagekit.register_imagekit_tools"
        ) as mock_register:
            imagekit_plugin.register_tools(mock_mcp, mock_service_container)

            # Service should be stored in container
            assert "imagekit" in mock_service_container.plugin_services
            service = mock_service_container.plugin_services["imagekit"]
            assert service is not None

            # Tools should be registered
            mock_register.assert_called_once()

    def test_register_tools_without_config(
        self, imagekit_plugin, mock_service_container
    ):
        """Test register_tools when config is missing"""
        mock_mcp = MagicMock()
        imagekit_plugin._config = None  # No cached config

        with patch(
            "mcp_remote_exec.plugins.imagekit.tools.register_imagekit_tools"
        ) as mock_register:
            imagekit_plugin.register_tools(mock_mcp, mock_service_container)

            # Should not register tools
            mock_register.assert_not_called()
            assert "imagekit" not in mock_service_container.plugin_services
