"""
Base Plugin Interface for SSH MCP Remote Exec

Defines the contract that all plugins must implement.
"""

from abc import ABC, abstractmethod
from fastmcp import FastMCP
from mcp_remote_exec.presentation.service_container import ServiceContainer


class BasePlugin(ABC):
    """Abstract base class for MCP plugins

    Plugin Initialization Patterns:
    ===============================

    Plugins follow a two-phase registration process:
    1. is_enabled() - Called to determine if plugin should activate
    2. register_tools() - Called to register MCP tools if enabled

    Config Caching Pattern:
    -----------------------

    Plugins may optionally cache their configuration in __init__ if their
    service requires the config object during initialization.

    Pattern 1: Config Caching (when plugin service needs config object)
        class MyPlugin(BasePlugin):
            def __init__(self):
                self._config: MyPluginConfig | None = None

            def is_enabled(self, container):
                # Cache config for reuse in register_tools()
                self._config = MyPluginConfig.from_env()
                return self._config is not None

            def register_tools(self, mcp, container):
                # Reuse cached config
                service = MyPluginService(config=self._config, ...)
                container.plugin_services[self.name] = service

    Pattern 2: No Config Caching (when plugin uses only core SSH credentials)
        class MyPlugin(BasePlugin):
            # No __init__ needed

            def is_enabled(self, container):
                # Config used only for validation
                config = MyPluginConfig.from_env()
                return config is not None

            def register_tools(self, mcp, container):
                # Service doesn't need plugin-specific config
                service = MyPluginService(
                    command_service=container.command_service,
                    file_service=container.file_service
                )
                container.plugin_services[self.name] = service

    When to cache config:
    - Plugin service requires config object at initialization (e.g., API keys, endpoints)
    - Example: ImageKit plugin needs credentials for ImageKit API

    When NOT to cache config:
    - Plugin only validates enablement flag (ENABLE_XXX=true)
    - Plugin service uses only core SSH credentials from ServiceContainer
    - Example: Proxmox plugin uses existing SSH connection for pct commands

    Plugin Registration Flow:
    -------------------------
    1. PluginRegistry.discover_plugins() - Discovers available plugins
    2. PluginRegistry.register_all() - Two-phase registration:
       a. Pre-scan: Calls is_enabled() on all plugins, populates container.enabled_plugins
       b. Registration: Calls register_tools() on enabled plugins
    3. Plugins can check container.enabled_plugins to coordinate with other plugins
       (e.g., Proxmox checks if ImageKit is enabled to skip file transfer tools)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin identifier (e.g., 'proxmox', 'imagekit')

        This name is used as:
        - Key in container.plugin_services dict
        - Entry in container.enabled_plugins set
        - Tool name prefix for plugin tools

        Convention: Use lowercase, descriptive names (e.g., 'proxmox', 'imagekit', 'docker')
        """
        pass

    @abstractmethod
    def is_enabled(self, container: ServiceContainer) -> bool:
        """
        Check if plugin should be activated based on configuration.

        This method is called during the pre-scan phase before any tools are
        registered. It should:
        1. Check environment variables or config files for enablement
        2. Validate required credentials/configuration if applicable
        3. Optionally cache config for use in register_tools() (if service needs it)
        4. Return True if all requirements are met, False otherwise

        Standard pattern:
            config = MyPluginConfig.from_env()
            return config is not None

        With config caching (if service needs it):
            self._config = MyPluginConfig.from_env()
            return self._config is not None

        Args:
            container: Service container with config and services

        Returns:
            True if plugin should register its tools, False otherwise
        """
        pass

    @abstractmethod
    def register_tools(self, mcp: FastMCP, container: ServiceContainer) -> None:
        """
        Register plugin's MCP tools.

        This method is called only if is_enabled() returned True.
        It should:
        1. Create and initialize the plugin service
        2. Store service in container.plugin_services[self.name]
        3. Register MCP tools using @mcp.tool decorators
        4. Optionally check container.enabled_plugins for cross-plugin coordination

        Standard pattern:
            # Create service
            service = MyPluginService(
                command_service=container.command_service,
                file_service=container.file_service,
            )

            # Store in container
            container.plugin_services[self.name] = service

            # Register tools
            @mcp.tool(name="my_plugin_tool")
            async def my_tool(...):
                return service.do_something(...)

        Args:
            mcp: FastMCP server instance to register tools with
            container: Service container for accessing core services and coordination
        """
        pass
