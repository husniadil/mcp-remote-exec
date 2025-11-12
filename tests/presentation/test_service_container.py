"""
Tests for ServiceContainer

Basic tests for service container dataclass.
"""

import pytest
from unittest.mock import MagicMock
from mcp_remote_exec.presentation.service_container import ServiceContainer


@pytest.fixture
def mock_services():
    """Create mock services for testing"""
    return {
        "config": MagicMock(),
        "connection_manager": MagicMock(),
        "sftp_manager": MagicMock(),
        "command_service": MagicMock(),
        "file_service": MagicMock(),
        "output_formatter": MagicMock(),
    }


def test_service_container_creation(mock_services):
    """Test that ServiceContainer can be created with all required services"""
    container = ServiceContainer(
        config=mock_services["config"],
        connection_manager=mock_services["connection_manager"],
        sftp_manager=mock_services["sftp_manager"],
        command_service=mock_services["command_service"],
        file_service=mock_services["file_service"],
        output_formatter=mock_services["output_formatter"],
    )

    assert container is not None
    assert container.config == mock_services["config"]
    assert container.connection_manager == mock_services["connection_manager"]
    assert container.sftp_manager == mock_services["sftp_manager"]
    assert container.command_service == mock_services["command_service"]
    assert container.file_service == mock_services["file_service"]
    assert container.output_formatter == mock_services["output_formatter"]


def test_service_container_default_plugin_services(mock_services):
    """Test that ServiceContainer initializes empty plugin_services dict by default"""
    container = ServiceContainer(
        config=mock_services["config"],
        connection_manager=mock_services["connection_manager"],
        sftp_manager=mock_services["sftp_manager"],
        command_service=mock_services["command_service"],
        file_service=mock_services["file_service"],
        output_formatter=mock_services["output_formatter"],
    )

    assert container.plugin_services == {}
    assert isinstance(container.plugin_services, dict)


def test_service_container_default_enabled_plugins(mock_services):
    """Test that ServiceContainer initializes empty enabled_plugins set by default"""
    container = ServiceContainer(
        config=mock_services["config"],
        connection_manager=mock_services["connection_manager"],
        sftp_manager=mock_services["sftp_manager"],
        command_service=mock_services["command_service"],
        file_service=mock_services["file_service"],
        output_formatter=mock_services["output_formatter"],
    )

    assert container.enabled_plugins == set()
    assert isinstance(container.enabled_plugins, set)


def test_service_container_add_plugin_service(mock_services):
    """Test adding plugin services to container"""
    container = ServiceContainer(
        config=mock_services["config"],
        connection_manager=mock_services["connection_manager"],
        sftp_manager=mock_services["sftp_manager"],
        command_service=mock_services["command_service"],
        file_service=mock_services["file_service"],
        output_formatter=mock_services["output_formatter"],
    )

    # Add a plugin service
    mock_plugin_service = MagicMock()
    container.plugin_services["test_plugin"] = mock_plugin_service

    assert "test_plugin" in container.plugin_services
    assert container.plugin_services["test_plugin"] == mock_plugin_service


def test_service_container_add_enabled_plugin(mock_services):
    """Test adding enabled plugins to container"""
    container = ServiceContainer(
        config=mock_services["config"],
        connection_manager=mock_services["connection_manager"],
        sftp_manager=mock_services["sftp_manager"],
        command_service=mock_services["command_service"],
        file_service=mock_services["file_service"],
        output_formatter=mock_services["output_formatter"],
    )

    # Add enabled plugins
    container.enabled_plugins.add("proxmox")
    container.enabled_plugins.add("imagekit")

    assert "proxmox" in container.enabled_plugins
    assert "imagekit" in container.enabled_plugins
    assert len(container.enabled_plugins) == 2


def test_service_container_with_initial_plugin_services(mock_services):
    """Test ServiceContainer with pre-populated plugin services"""
    initial_plugins = {"plugin1": MagicMock(), "plugin2": MagicMock()}

    container = ServiceContainer(
        config=mock_services["config"],
        connection_manager=mock_services["connection_manager"],
        sftp_manager=mock_services["sftp_manager"],
        command_service=mock_services["command_service"],
        file_service=mock_services["file_service"],
        output_formatter=mock_services["output_formatter"],
        plugin_services=initial_plugins,
    )

    assert container.plugin_services == initial_plugins
    assert "plugin1" in container.plugin_services
    assert "plugin2" in container.plugin_services


def test_service_container_with_initial_enabled_plugins(mock_services):
    """Test ServiceContainer with pre-populated enabled plugins"""
    initial_enabled = {"proxmox", "imagekit"}

    container = ServiceContainer(
        config=mock_services["config"],
        connection_manager=mock_services["connection_manager"],
        sftp_manager=mock_services["sftp_manager"],
        command_service=mock_services["command_service"],
        file_service=mock_services["file_service"],
        output_formatter=mock_services["output_formatter"],
        enabled_plugins=initial_enabled,
    )

    assert container.enabled_plugins == initial_enabled
    assert "proxmox" in container.enabled_plugins
    assert "imagekit" in container.enabled_plugins
