#!/usr/bin/env python3
"""
SSH MCP Remote Exec - Main Entry Point

This MCP server provides SSH access to remote servers, allowing AI assistants
to execute commands, transfer files, and manage systems through natural
language interfaces.

Usage:
    uv run mcp-remote-exec    # Start server for Claude Desktop
"""

import sys
import logging
from dotenv import load_dotenv

from mcp_remote_exec import __version__
from mcp_remote_exec.presentation.mcp_tools import mcp

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)


def run_stdio_mode() -> None:
    """
    Run MCP server in stdio mode.

    Initializes services, loads plugins, and starts the MCP server.
    Handles graceful shutdown on keyboard interrupt.

    Raises:
        SystemExit: On configuration errors or exceptions
    """
    try:
        # Eagerly initialize services to log activated plugins
        from mcp_remote_exec.presentation.mcp_tools import get_services

        get_services()

        # Start MCP server
        mcp.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def parse_command_line() -> None:
    """
    Parse and handle command line arguments.

    Checks for --help/-h and --version/-v flags and handles them appropriately.
    Exits the program if these flags are found.
    """
    if "--help" in sys.argv or "-h" in sys.argv:
        print_help()
        sys.exit(0)

    if "--version" in sys.argv or "-v" in sys.argv:
        print_version()
        sys.exit(0)


def print_help() -> None:
    """
    Print usage and help information to stdout.

    Displays command-line usage, options, and environment variable requirements.
    """
    print("""SSH MCP Remote Exec

USAGE:
    uv run mcp-remote-exec    # Start server for Claude Desktop
    mcp-remote-exec --help    # Show this help
    mcp-remote-exec --version # Show version

CONFIGURATION:
    Copy .env.example to .env and configure:
    - I_ACCEPT_RISKS=true (required - acknowledge SSH risks)
    - HOST=your-server-ip (SSH server address)
    - SSH_USERNAME=your-username
    - SSH_PASSWORD or SSH_KEY=path/to/key

For detailed configuration, see .env.example
""")


def print_version() -> None:
    """
    Print version information to stdout.

    Displays the current version of mcp-remote-exec.
    """
    print(f"mcp-remote-exec version {__version__}")


def main() -> None:
    """Main CLI entry point"""
    parse_command_line()
    run_stdio_mode()


# CLI entry point for installable package
if __name__ == "__main__":
    main()
