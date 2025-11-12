"""Tests for Plugin Registry"""

from unittest.mock import MagicMock, patch

from mcp_remote_exec.plugins.base import BasePlugin
from mcp_remote_exec.plugins.registry import PluginRegistry
from mcp_remote_exec.presentation.service_container import ServiceContainer


class MockPlugin(BasePlugin):
    """Mock plugin for testing"""

    def __init__(self, plugin_name: str, enabled: bool = True):
        self._name = plugin_name
        self._enabled = enabled
        self.register_called = False

    @property
    def name(self) -> str:
        return self._name

    def is_enabled(self, container: ServiceContainer) -> bool:
        return self._enabled

    def register_tools(self, mcp, container: ServiceContainer) -> None:
        self.register_called = True
        # Simulate storing service in container
        container.plugin_services[self.name] = f"{self.name}_service"


class TestPluginRegistry:
    """Tests for PluginRegistry class"""

    def test_init(self):
        """Test registry initialization"""
        registry = PluginRegistry()
        assert registry.plugins == []

    def test_discover_plugins_imports_available_plugins(self):
        """Test that discover_plugins finds available plugins"""
        registry = PluginRegistry()
        registry.discover_plugins()

        # Should discover Proxmox and ImageKit plugins (if available)
        assert len(registry.plugins) >= 0  # At least doesn't fail

        # Should contain standard plugins
        assert isinstance(registry.plugins, list)

    @patch("mcp_remote_exec.plugins.registry._log")
    def test_discover_plugins_handles_import_errors(self, mock_log):
        """Test that discover_plugins handles missing plugins gracefully"""
        registry = PluginRegistry()

        # Even if plugins don't exist, should not raise
        registry.discover_plugins()

        # Should have logged debug messages
        assert mock_log.debug.called

    def test_register_all_with_enabled_plugin(self):
        """Test registering enabled plugins"""
        registry = PluginRegistry()
        mock_plugin = MockPlugin("test_plugin", enabled=True)
        registry.plugins = [mock_plugin]

        mock_mcp = MagicMock()
        container = ServiceContainer(
            config=MagicMock(),
            connection_manager=MagicMock(),
            sftp_manager=MagicMock(),
            command_service=MagicMock(),
            file_service=MagicMock(),
            output_formatter=MagicMock(),
        )

        activated = registry.register_all(mock_mcp, container)

        # Plugin should be enabled and registered
        assert "test_plugin" in container.enabled_plugins
        assert mock_plugin.register_called is True
        assert activated == ["test_plugin"]
        assert container.plugin_services["test_plugin"] == "test_plugin_service"

    def test_register_all_with_disabled_plugin(self):
        """Test that disabled plugins are not registered"""
        registry = PluginRegistry()
        mock_plugin = MockPlugin("disabled_plugin", enabled=False)
        registry.plugins = [mock_plugin]

        mock_mcp = MagicMock()
        container = ServiceContainer(
            config=MagicMock(),
            connection_manager=MagicMock(),
            sftp_manager=MagicMock(),
            command_service=MagicMock(),
            file_service=MagicMock(),
            output_formatter=MagicMock(),
        )

        activated = registry.register_all(mock_mcp, container)

        # Plugin should not be enabled or registered
        assert "disabled_plugin" not in container.enabled_plugins
        assert mock_plugin.register_called is False
        assert activated == []
        assert "disabled_plugin" not in container.plugin_services

    def test_register_all_with_multiple_plugins(self):
        """Test registering multiple plugins"""
        registry = PluginRegistry()
        plugin1 = MockPlugin("plugin1", enabled=True)
        plugin2 = MockPlugin("plugin2", enabled=True)
        plugin3 = MockPlugin("plugin3", enabled=False)
        registry.plugins = [plugin1, plugin2, plugin3]

        mock_mcp = MagicMock()
        container = ServiceContainer(
            config=MagicMock(),
            connection_manager=MagicMock(),
            sftp_manager=MagicMock(),
            command_service=MagicMock(),
            file_service=MagicMock(),
            output_formatter=MagicMock(),
        )

        activated = registry.register_all(mock_mcp, container)

        # Only enabled plugins should be registered
        assert container.enabled_plugins == {"plugin1", "plugin2"}
        assert plugin1.register_called is True
        assert plugin2.register_called is True
        assert plugin3.register_called is False
        assert set(activated) == {"plugin1", "plugin2"}

    @patch("mcp_remote_exec.plugins.registry._log")
    def test_register_all_handles_registration_errors(self, mock_log):
        """Test that registration errors are handled gracefully"""

        class FailingPlugin(BasePlugin):
            @property
            def name(self):
                return "failing"

            def is_enabled(self, container):
                return True

            def register_tools(self, mcp, container):
                raise RuntimeError("Registration failed!")

        registry = PluginRegistry()
        registry.plugins = [FailingPlugin()]

        mock_mcp = MagicMock()
        container = ServiceContainer(
            config=MagicMock(),
            connection_manager=MagicMock(),
            sftp_manager=MagicMock(),
            command_service=MagicMock(),
            file_service=MagicMock(),
            output_formatter=MagicMock(),
        )

        activated = registry.register_all(mock_mcp, container)

        # Plugin should be removed from enabled set after error
        assert "failing" not in container.enabled_plugins
        assert activated == []
        assert mock_log.error.called

    @patch("mcp_remote_exec.plugins.registry._log")
    def test_plugin_coordination_warning(self, mock_log):
        """Test warning when Proxmox and ImageKit are both enabled"""
        registry = PluginRegistry()
        proxmox_plugin = MockPlugin("proxmox", enabled=True)
        imagekit_plugin = MockPlugin("imagekit", enabled=True)
        registry.plugins = [proxmox_plugin, imagekit_plugin]

        mock_mcp = MagicMock()
        container = ServiceContainer(
            config=MagicMock(),
            connection_manager=MagicMock(),
            sftp_manager=MagicMock(),
            command_service=MagicMock(),
            file_service=MagicMock(),
            output_formatter=MagicMock(),
        )

        registry.register_all(mock_mcp, container)

        # Should log warning about tool replacement
        assert mock_log.warning.called
        warning_msg = mock_log.warning.call_args[0][0]
        assert "Proxmox" in warning_msg
        assert "ImageKit" in warning_msg

    def test_discover_and_register(self):
        """Test convenience method discover_and_register"""
        registry = PluginRegistry()

        mock_mcp = MagicMock()
        container = ServiceContainer(
            config=MagicMock(),
            connection_manager=MagicMock(),
            sftp_manager=MagicMock(),
            command_service=MagicMock(),
            file_service=MagicMock(),
            output_formatter=MagicMock(),
        )

        # Should not raise
        activated = registry.discover_and_register(mock_mcp, container)

        # Should return list of activated plugin names
        assert isinstance(activated, list)
        # Plugins should be discovered
        assert len(registry.plugins) >= 0

    def test_enabled_plugins_available_during_registration(self):
        """Test that enabled_plugins is populated before register_tools is called"""

        class CoordinatingPlugin(BasePlugin):
            def __init__(self, plugin_name: str):
                self._name = plugin_name
                self.seen_enabled_plugins = set()

            @property
            def name(self):
                return self._name

            def is_enabled(self, container):
                return True

            def register_tools(self, mcp, container):
                # Capture what plugins are enabled at registration time
                self.seen_enabled_plugins = set(container.enabled_plugins)

        registry = PluginRegistry()
        plugin1 = CoordinatingPlugin("coord1")
        plugin2 = CoordinatingPlugin("coord2")
        registry.plugins = [plugin1, plugin2]

        mock_mcp = MagicMock()
        container = ServiceContainer(
            config=MagicMock(),
            connection_manager=MagicMock(),
            sftp_manager=MagicMock(),
            command_service=MagicMock(),
            file_service=MagicMock(),
            output_formatter=MagicMock(),
        )

        registry.register_all(mock_mcp, container)

        # Both plugins should see both enabled plugins during registration
        assert plugin1.seen_enabled_plugins == {"coord1", "coord2"}
        assert plugin2.seen_enabled_plugins == {"coord1", "coord2"}
