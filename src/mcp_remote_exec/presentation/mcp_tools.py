"""
MCP Tools for SSH MCP Remote Exec

Provides tools for SSH command execution and file transfers.

This module defines the MCP tools (presentation layer) and delegates initialization
to the bootstrap module (composition root). It only imports from the services and
presentation layers, maintaining proper architectural separation.
"""

import logging
from typing import Annotated

from fastmcp import FastMCP

from mcp_remote_exec.presentation import bootstrap
from mcp_remote_exec.presentation.models import (
    ResponseFormat,
    SSHExecCommandInput,
)

_log = logging.getLogger(__name__)

# Create FastMCP server (stdio mode, no app_lifespan)
mcp = FastMCP("mcp_remote_exec")


# ============================================================================
# Core MCP Tools
# ============================================================================


@mcp.tool(name="ssh_exec_command")
async def ssh_exec_command(
    command: Annotated[
        str, "Bash command to execute on the remote server (required)"
    ] = "",
    timeout: Annotated[int, "Command timeout in seconds (1-300, default: 30)"] = 30,
    response_format: Annotated[
        str,
        "Output format: 'text' for human-readable or 'json' for structured data",
    ] = "text",
) -> str:
    """Execute a bash command on your remote SSH server.

    Use this tool to run commands on your configured Linux/Unix server for:
    - System administration (checking disk space, memory usage)
    - Service management (starting/stopping services)
    - File operations (listing files, reading logs)
    - Software management (installing packages, updates)
    - System diagnostics (checking system status)

    Args:
        command: Bash command to execute (required)
        timeout: Command timeout in seconds (default: 30, max: 300)
        response_format: Output format - 'text' for human-readable or 'json' for structured data

    Returns:
        Formatted command output with execution metadata
    """
    try:
        # Validate input using Pydantic model
        input_data = SSHExecCommandInput(
            command=command,
            timeout=timeout,
            response_format=ResponseFormat(response_format.lower()),
        )

        # Get services from bootstrap module
        container = bootstrap.get_container()

        result = container.command_service.execute_command(
            command=input_data.command,
            timeout=input_data.timeout,
            response_format=input_data.response_format.value,
        )

        return result

    except ValueError as e:
        container = bootstrap.get_container()
        return container.output_formatter.format_error_result(
            f"Input validation error: {str(e)}"
        ).content
    except Exception as e:
        container = bootstrap.get_container()
        return container.output_formatter.format_error_result(
            f"Unexpected error: {str(e)}"
        ).content


# ============================================================================
# Application Initialization
# ============================================================================

# Initialize application on module load
# This call to bootstrap.initialize() is the composition root where all layers
# are wired together. It returns a ServiceContainer with all dependencies.
bootstrap.initialize(mcp)
