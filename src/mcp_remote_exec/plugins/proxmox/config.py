"""
Proxmox Configuration for SSH MCP Remote Exec

Handles Proxmox plugin enablement and configuration.

Configuration Pattern:
    ProxmoxConfig uses a check-then-use pattern where from_env() returns None if
    the plugin is not enabled. This is appropriate for optional plugin configuration -
    if Proxmox is not enabled, the plugin is simply not activated rather than causing
    application startup failure.

    Unlike ImageKit which requires additional credentials, Proxmox uses the existing
    SSH connection configuration, so it only needs an enablement flag.

    Compare with core configs (like SSHConfig) which use a fail-fast pattern that
    raises exceptions during initialization, since core configuration is required
    for the application to function.
"""

import os
from dataclasses import dataclass


@dataclass
class ProxmoxConfig:
    """Configuration for Proxmox container management plugin"""

    enabled: bool = True

    @classmethod
    def from_env(cls) -> "ProxmoxConfig | None":
        """
        Create config from environment variables.

        Returns:
            ProxmoxConfig if ENABLE_PROXMOX=true, None otherwise
        """
        enabled = os.getenv("ENABLE_PROXMOX", "false").lower() == "true"

        if not enabled:
            return None

        return cls(enabled=enabled)
