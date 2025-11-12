"""Tests for Bootstrap Module (Composition Root)"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from fastmcp import FastMCP

from mcp_remote_exec.presentation import bootstrap
from mcp_remote_exec.presentation.service_container import ServiceContainer
from mcp_remote_exec.config.exceptions import ConfigError


@pytest.fixture(autouse=True)
def reset_app_context():
    """Reset global app context before each test"""
    # Store original value
    original = bootstrap._app_context

    # Reset to None
    bootstrap._app_context = None

    yield

    # Restore original value after test
    bootstrap._app_context = original


@pytest.fixture
def mock_mcp_server():
    """Create a mock FastMCP server"""
    return MagicMock(spec=FastMCP)


class TestGetContainerBeforeInitialization:
    """Tests for get_container() before initialization"""

    def test_get_container_before_initialize_raises_error(self):
        """Test that get_container() raises RuntimeError before initialize()"""
        with pytest.raises(RuntimeError) as exc_info:
            bootstrap.get_container()

        assert "not initialized" in str(exc_info.value).lower()
        assert "initialize" in str(exc_info.value).lower()


class TestInitialization:
    """Tests for bootstrap initialization"""

    @patch("mcp_remote_exec.presentation.bootstrap.SSHConfig")
    @patch("mcp_remote_exec.presentation.bootstrap.SSHConnectionManager")
    @patch("mcp_remote_exec.presentation.bootstrap.SFTPManager")
    @patch("mcp_remote_exec.presentation.bootstrap.CommandService")
    @patch("mcp_remote_exec.presentation.bootstrap.FileTransferService")
    @patch("mcp_remote_exec.presentation.bootstrap.OutputFormatter")
    @patch("mcp_remote_exec.plugins.registry.PluginRegistry")
    def test_initialize_creates_service_container(
        self,
        mock_plugin_registry,
        mock_output_formatter,
        mock_file_service,
        mock_command_service,
        mock_sftp_manager,
        mock_connection_manager,
        mock_ssh_config,
        mock_mcp_server,
    ):
        """Test that initialize() creates and returns a ServiceContainer"""
        # Setup mock config
        mock_config_instance = MagicMock()
        mock_config_instance.validate.return_value = (True, None)
        mock_config_instance.get_host.return_value = MagicMock(name="test.example.com")
        mock_ssh_config.return_value = mock_config_instance

        # Setup mock plugin registry
        mock_registry_instance = MagicMock()
        mock_registry_instance.discover_and_register.return_value = []
        mock_plugin_registry.return_value = mock_registry_instance

        # Initialize
        container = bootstrap.initialize(mock_mcp_server)

        # Verify container is created
        assert isinstance(container, ServiceContainer)
        assert container.config == mock_config_instance

    @patch("mcp_remote_exec.presentation.bootstrap.SSHConfig")
    def test_initialize_with_config_validation_error_raises(self, mock_ssh_config, mock_mcp_server):
        """Test that initialize() raises ConfigError when config validation fails"""
        # Setup mock config with validation failure
        mock_config_instance = MagicMock()
        mock_config_instance.validate.return_value = (False, "Missing HOST configuration")
        mock_ssh_config.return_value = mock_config_instance

        # Should raise ConfigError
        with pytest.raises(ConfigError) as exc_info:
            bootstrap.initialize(mock_mcp_server)

        assert "Missing HOST configuration" in str(exc_info.value)

    @patch("mcp_remote_exec.presentation.bootstrap.SSHConfig")
    @patch("mcp_remote_exec.presentation.bootstrap.SSHConnectionManager")
    @patch("mcp_remote_exec.presentation.bootstrap.SFTPManager")
    @patch("mcp_remote_exec.presentation.bootstrap.CommandService")
    @patch("mcp_remote_exec.presentation.bootstrap.FileTransferService")
    @patch("mcp_remote_exec.presentation.bootstrap.OutputFormatter")
    @patch("mcp_remote_exec.plugins.registry.PluginRegistry")
    def test_initialize_creates_all_services(
        self,
        mock_plugin_registry,
        mock_output_formatter,
        mock_file_service,
        mock_command_service,
        mock_sftp_manager,
        mock_connection_manager,
        mock_ssh_config,
        mock_mcp_server,
    ):
        """Test that initialize() creates all required services"""
        # Setup mocks
        mock_config_instance = MagicMock()
        mock_config_instance.validate.return_value = (True, None)
        mock_config_instance.get_host.return_value = MagicMock(name="test.example.com")
        mock_ssh_config.return_value = mock_config_instance

        mock_registry_instance = MagicMock()
        mock_registry_instance.discover_and_register.return_value = []
        mock_plugin_registry.return_value = mock_registry_instance

        # Initialize
        bootstrap.initialize(mock_mcp_server)

        # Verify all services were created
        mock_ssh_config.assert_called_once()
        mock_connection_manager.assert_called_once_with(mock_config_instance)
        mock_sftp_manager.assert_called_once()
        mock_command_service.assert_called_once()
        mock_file_service.assert_called_once()
        mock_output_formatter.assert_called_once_with(mock_config_instance)

    @patch("mcp_remote_exec.presentation.bootstrap.SSHConfig")
    @patch("mcp_remote_exec.presentation.bootstrap.SSHConnectionManager")
    @patch("mcp_remote_exec.presentation.bootstrap.SFTPManager")
    @patch("mcp_remote_exec.presentation.bootstrap.CommandService")
    @patch("mcp_remote_exec.presentation.bootstrap.FileTransferService")
    @patch("mcp_remote_exec.presentation.bootstrap.OutputFormatter")
    @patch("mcp_remote_exec.plugins.registry.PluginRegistry")
    def test_initialize_registers_plugins(
        self,
        mock_plugin_registry,
        mock_output_formatter,
        mock_file_service,
        mock_command_service,
        mock_sftp_manager,
        mock_connection_manager,
        mock_ssh_config,
        mock_mcp_server,
    ):
        """Test that initialize() discovers and registers plugins"""
        # Setup mocks
        mock_config_instance = MagicMock()
        mock_config_instance.validate.return_value = (True, None)
        mock_config_instance.get_host.return_value = MagicMock(name="test.example.com")
        mock_ssh_config.return_value = mock_config_instance

        mock_registry_instance = MagicMock()
        mock_registry_instance.discover_and_register.return_value = ["proxmox", "imagekit"]
        mock_plugin_registry.return_value = mock_registry_instance

        # Initialize
        container = bootstrap.initialize(mock_mcp_server)

        # Verify plugin registry was called
        mock_registry_instance.discover_and_register.assert_called_once()

        # Verify activated plugins were stored
        assert "_activated_plugins" in container.plugin_services
        assert container.plugin_services["_activated_plugins"] == ["proxmox", "imagekit"]

    @patch("mcp_remote_exec.presentation.bootstrap.SSHConfig")
    @patch("mcp_remote_exec.presentation.bootstrap.SSHConnectionManager")
    @patch("mcp_remote_exec.presentation.bootstrap.SFTPManager")
    @patch("mcp_remote_exec.presentation.bootstrap.CommandService")
    @patch("mcp_remote_exec.presentation.bootstrap.FileTransferService")
    @patch("mcp_remote_exec.presentation.bootstrap.OutputFormatter")
    @patch("mcp_remote_exec.plugins.registry.PluginRegistry")
    @patch("mcp_remote_exec.presentation.bootstrap._register_ssh_file_transfer_tools")
    def test_initialize_registers_ssh_tools_when_imagekit_disabled(
        self,
        mock_register_ssh_tools,
        mock_plugin_registry,
        mock_output_formatter,
        mock_file_service,
        mock_command_service,
        mock_sftp_manager,
        mock_connection_manager,
        mock_ssh_config,
        mock_mcp_server,
    ):
        """Test that SSH file transfer tools are registered when ImageKit is disabled"""
        # Setup mocks
        mock_config_instance = MagicMock()
        mock_config_instance.validate.return_value = (True, None)
        mock_config_instance.get_host.return_value = MagicMock(name="test.example.com")
        mock_ssh_config.return_value = mock_config_instance

        # No ImageKit plugin
        mock_registry_instance = MagicMock()
        mock_registry_instance.discover_and_register.return_value = ["proxmox"]
        mock_plugin_registry.return_value = mock_registry_instance

        # Initialize
        bootstrap.initialize(mock_mcp_server)

        # Verify SSH tools were registered
        mock_register_ssh_tools.assert_called_once_with(mock_mcp_server)

    @patch("mcp_remote_exec.presentation.bootstrap.SSHConfig")
    @patch("mcp_remote_exec.presentation.bootstrap.SSHConnectionManager")
    @patch("mcp_remote_exec.presentation.bootstrap.SFTPManager")
    @patch("mcp_remote_exec.presentation.bootstrap.CommandService")
    @patch("mcp_remote_exec.presentation.bootstrap.FileTransferService")
    @patch("mcp_remote_exec.presentation.bootstrap.OutputFormatter")
    @patch("mcp_remote_exec.plugins.registry.PluginRegistry")
    @patch("mcp_remote_exec.presentation.bootstrap._register_ssh_file_transfer_tools")
    def test_initialize_skips_ssh_tools_when_imagekit_enabled(
        self,
        mock_register_ssh_tools,
        mock_plugin_registry,
        mock_output_formatter,
        mock_file_service,
        mock_command_service,
        mock_sftp_manager,
        mock_connection_manager,
        mock_ssh_config,
        mock_mcp_server,
    ):
        """Test that SSH file transfer tools are NOT registered when ImageKit is enabled"""
        # Setup mocks
        mock_config_instance = MagicMock()
        mock_config_instance.validate.return_value = (True, None)
        mock_config_instance.get_host.return_value = MagicMock(name="test.example.com")
        mock_ssh_config.return_value = mock_config_instance

        # ImageKit plugin enabled - mock registry to populate enabled_plugins
        mock_registry_instance = MagicMock()

        # Simulate plugin registry behavior: populate enabled_plugins set during discover_and_register
        def populate_enabled_plugins(mcp, container):
            # Plugin registry adds enabled plugins to container during registration
            container.enabled_plugins.add("imagekit")
            container.enabled_plugins.add("proxmox")
            return ["imagekit", "proxmox"]

        mock_registry_instance.discover_and_register.side_effect = populate_enabled_plugins
        mock_plugin_registry.return_value = mock_registry_instance

        # Initialize
        bootstrap.initialize(mock_mcp_server)

        # Verify SSH tools were NOT registered
        mock_register_ssh_tools.assert_not_called()


class TestSingletonPattern:
    """Tests for singleton behavior of bootstrap"""

    @patch("mcp_remote_exec.presentation.bootstrap.SSHConfig")
    @patch("mcp_remote_exec.presentation.bootstrap.SSHConnectionManager")
    @patch("mcp_remote_exec.presentation.bootstrap.SFTPManager")
    @patch("mcp_remote_exec.presentation.bootstrap.CommandService")
    @patch("mcp_remote_exec.presentation.bootstrap.FileTransferService")
    @patch("mcp_remote_exec.presentation.bootstrap.OutputFormatter")
    @patch("mcp_remote_exec.plugins.registry.PluginRegistry")
    def test_initialize_twice_returns_same_instance(
        self,
        mock_plugin_registry,
        mock_output_formatter,
        mock_file_service,
        mock_command_service,
        mock_sftp_manager,
        mock_connection_manager,
        mock_ssh_config,
        mock_mcp_server,
    ):
        """Test that calling initialize() twice returns the same container instance"""
        # Setup mocks
        mock_config_instance = MagicMock()
        mock_config_instance.validate.return_value = (True, None)
        mock_config_instance.get_host.return_value = MagicMock(name="test.example.com")
        mock_ssh_config.return_value = mock_config_instance

        mock_registry_instance = MagicMock()
        mock_registry_instance.discover_and_register.return_value = []
        mock_plugin_registry.return_value = mock_registry_instance

        # Initialize twice
        container1 = bootstrap.initialize(mock_mcp_server)
        container2 = bootstrap.initialize(mock_mcp_server)

        # Should be the same instance
        assert container1 is container2

    @patch("mcp_remote_exec.presentation.bootstrap.SSHConfig")
    @patch("mcp_remote_exec.presentation.bootstrap.SSHConnectionManager")
    @patch("mcp_remote_exec.presentation.bootstrap.SFTPManager")
    @patch("mcp_remote_exec.presentation.bootstrap.CommandService")
    @patch("mcp_remote_exec.presentation.bootstrap.FileTransferService")
    @patch("mcp_remote_exec.presentation.bootstrap.OutputFormatter")
    @patch("mcp_remote_exec.plugins.registry.PluginRegistry")
    def test_get_container_after_initialize(
        self,
        mock_plugin_registry,
        mock_output_formatter,
        mock_file_service,
        mock_command_service,
        mock_sftp_manager,
        mock_connection_manager,
        mock_ssh_config,
        mock_mcp_server,
    ):
        """Test that get_container() returns the initialized container"""
        # Setup mocks
        mock_config_instance = MagicMock()
        mock_config_instance.validate.return_value = (True, None)
        mock_config_instance.get_host.return_value = MagicMock(name="test.example.com")
        mock_ssh_config.return_value = mock_config_instance

        mock_registry_instance = MagicMock()
        mock_registry_instance.discover_and_register.return_value = []
        mock_plugin_registry.return_value = mock_registry_instance

        # Initialize
        container1 = bootstrap.initialize(mock_mcp_server)

        # Get container
        container2 = bootstrap.get_container()

        # Should be the same instance
        assert container1 is container2
