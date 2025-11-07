# SSH MCP Remote Exec

A Model Context Protocol (MCP) server that provides SSH access to remote servers, allowing AI assistants to execute commands, transfer files, and manage systems through natural language interfaces.

## ⚠️ DISCLAIMER

**ENGLISH:**

**USE AT YOUR OWN RISK.** This software provides direct SSH access and command execution capabilities on your remote infrastructure. The developer(s) of this software are **NOT responsible** for any damage, data loss, system failures, security breaches, or any other issues that may arise from using this software.

By using this software, you acknowledge that:

- You understand the risks of giving an AI system SSH access to your infrastructure
- You are solely responsible for reviewing and approving commands before execution
- You have proper backups and disaster recovery procedures in place
- You will not hold the developer(s) liable for any damages or losses

**This software is provided "AS IS" without warranty of any kind, express or implied.**

## Architecture

This MCP server is built with a clean 4-layer architecture (bottom-up):

- **Layer 1: Configuration** - SSH host setup, security settings, configuration management
- **Layer 2: Data Access** - SSH connections, SFTP operations, domain exceptions
- **Layer 3: Services** - Business logic, validation, output formatting
- **Layer 4: Presentation** - FastMCP tools, input models, AI interface

## Features

### Core Features

- ✅ **Execute bash commands** on remote SSH servers
- ✅ **File transfer operations** (upload/download) with SFTP
- ✅ **Connection management** with automatic cleanup
- ✅ **Security features** - Risk acceptance, validation, timeouts
- ✅ **Stdio mode** - Native Claude Desktop integration
- ✅ **CLI tool** - Installable as `uv run mcp-remote-exec`

### Plugin System

- ✅ **Extensible architecture** - Add domain-specific functionality
- ✅ **Conditional activation** - Enable plugins via environment variables
- ✅ **Proxmox plugin** - Container management for Proxmox VE (LXC containers)
- ✅ **ImageKit plugin** - Two-phase file transfers for HTTP gateway scenarios

## Plugins

### ImageKit Plugin

The ImageKit plugin enables file transfers when the MCP server runs behind an HTTP gateway, where direct SFTP connections don't work. It uses ImageKit as a temporary storage bridge for two-phase transfers.

**Activation**: Set ImageKit credentials and `ENABLE_IMAGEKIT=true` in your `.env` file

**Requirements**: ImageKit account (free tier available at https://imagekit.io)

**When to use**:

- MCP server runs through HTTP gateway (not direct connection)
- Direct SFTP between client and server isn't possible
- Need secure file transfers with short-lived tokens

**Available Tools** (4 tools):

- `imagekit_request_upload` - Initiate upload (step 1/3)
- `imagekit_confirm_upload` - Complete upload (step 3/3)
- `imagekit_request_download` - Initiate download (step 1/3)
- `imagekit_confirm_download` - Complete download (step 3/3)

**How it works**:

Upload: Client → ImageKit → Server  
Download: Server → ImageKit → Client

**Example Configuration**:

```bash
# .env
I_ACCEPT_RISKS=true
HOST=192.168.1.100
SSH_USERNAME=root
SSH_PASSWORD=secret

# ImageKit credentials
IMAGEKIT_PUBLIC_KEY=your_public_key
IMAGEKIT_PRIVATE_KEY=your_private_key
IMAGEKIT_URL_ENDPOINT=https://ik.imagekit.io/your_id
IMAGEKIT_FOLDER=/mcp-remote-exec  # Optional: organize files in a folder
ENABLE_IMAGEKIT=true
```

**Example Usage**:

```python
# Upload file to server
imagekit_request_upload(remote_path="/data/file.txt", permissions=644)
# Returns curl command - execute it to upload file
# Then confirm:
imagekit_confirm_upload(transfer_id="abc-123-def")

# Download file from server
imagekit_request_download(remote_path="/data/file.txt")
# Returns download URL - execute curl to download
# Then confirm cleanup:
imagekit_confirm_download(transfer_id="abc-123-def")
```

**Tool Replacement**:

When ImageKit plugin is enabled (`ENABLE_IMAGEKIT=true` with valid credentials):

- ❌ `ssh_upload_file` - NOT registered (use `imagekit_request_upload` + `imagekit_confirm_upload`)
- ❌ `ssh_download_file` - NOT registered (use `imagekit_request_download` + `imagekit_confirm_download`)
- ❌ `proxmox_upload_file_to_container` - NOT registered (ImageKit provides unified file transfer)
- ❌ `proxmox_download_file_from_container` - NOT registered (ImageKit provides unified file transfer)
- ✅ `ssh_exec_command` - Still available
- ✅ All Proxmox container management tools (`proxmox_container_exec_command`, etc.) - Still available

**Note**: ImageKit tools support Proxmox containers via the `ctid` parameter, providing a unified interface for all file transfers.

For detailed documentation, see [plugins/imagekit/README.md](src/mcp_remote_exec/plugins/imagekit/README.md)

### Proxmox Plugin

The Proxmox plugin provides container management tools for Proxmox VE. It enables AI assistants to manage LXC containers through specialized commands.

**Activation**: Set `ENABLE_PROXMOX=true` in your `.env` file

**Requirements**: Your SSH host must be a Proxmox VE server

**Available Tools**:

Container management (always available - 5 tools):

- `proxmox_container_exec_command` - Execute commands inside containers
- `proxmox_list_containers` - List all LXC containers
- `proxmox_container_status` - Get container status (running/stopped)
- `proxmox_start_container` - Start a stopped container
- `proxmox_stop_container` - Stop a running container

File transfer (conditional - 2 tools, disabled if ImageKit is enabled):

- `proxmox_download_file_from_container` - Download files from containers
- `proxmox_upload_file_to_container` - Upload files to containers

**Tool Separation**:

- **Core tools** handle Proxmox host operations (use `ssh_exec_command`, `ssh_upload_file`, etc.)
- **Plugin tools** handle container-specific operations (use `proxmox_*` tools)

**Note**: If ImageKit plugin is enabled, Proxmox file transfer tools are replaced by ImageKit tools which support the `ctid` parameter for container operations

**Example Configuration**:

```bash
# .env
I_ACCEPT_RISKS=true
HOST=192.168.1.100    # Your Proxmox host
SSH_USERNAME=root
SSH_PASSWORD=secret
ENABLE_PROXMOX=true   # Activate plugin
```

**Example Usage**:

```python
# Host operations (use core tools)
ssh_exec_command("pvecm status")                   # Check cluster status
ssh_exec_command("df -h")                          # Check host disk space
ssh_download_file("/etc/pve/storage.cfg", "./storage.cfg")

# Container operations (use plugin tools)
proxmox_list_containers()                          # List all containers
proxmox_container_exec_command(ctid=100, command="apt update")  # Update container
proxmox_upload_file_to_container(ctid=100, local_path="./app.conf", container_path="/etc/app/app.conf")
```

For detailed documentation, see [plugins/proxmox/README.md](src/mcp_remote_exec/plugins/proxmox/README.md)

## Installation

### Prerequisites

- Python 3.12
- SSH access to remote servers
- AI assistant compatible with MCP (e.g., Claude Desktop)

### Quick Install

```bash
# Clone the repository
git clone https://github.com/husniadil/mcp-remote-exec.git
cd mcp-remote-exec

# Install dependencies and setup package
uv sync

# Verify installation
uv run mcp-remote-exec --version
```

### Install from Source

```bash
# Install in development mode
pip install -e .
# Or
python -m pip install -e .
```

## Configuration

Copy the example configuration and modify it:

```bash
cp .env.example .env
nano .env  # Edit your configuration
```

### Required Configuration

```bash
# REQUIRED: Accept risks
I_ACCEPT_RISKS=true

# SSH host configuration
HOST=192.168.1.100
SSH_USERNAME=root
SSH_PASSWORD=your_password

# OR use SSH key authentication
SSH_KEY=/path/to/your/private_key
```

### Optional Settings

```bash
# Maximum character limit for command output (default: 25000)
CHARACTER_LIMIT=25000

# Maximum file size for transfers in bytes (default: 10MB)
MAX_FILE_SIZE=10485760

# Default timeout for commands (default: 30 seconds)
TIMEOUT=30

# Optional: SSH port (default: 22)
SSH_PORT=22

# SSH host key verification (default: true)
# true = Reject connections to unknown hosts (secure, requires known_hosts)
# false = Auto-accept unknown hosts (convenient for containers/dev, less secure)
SSH_STRICT_HOST_KEY_CHECKING=true
```

**Command Input Limits:**

- Maximum command length: 10,000 characters
- Maximum command timeout: 300 seconds (5 minutes)

## Usage

### CLI Commands

```bash
# Help and version
uv run mcp-remote-exec --help    # Long form
uv run mcp-remote-exec -h        # Short form
uv run mcp-remote-exec --version # Long form
uv run mcp-remote-exec -v        # Short form

# Run server
uv run mcp-remote-exec              # Start stdio mode (Claude Desktop)
```

### Claude Desktop Setup

1. Open Claude Desktop configuration:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add this configuration:

```json
{
  "mcpServers": {
    "mcp_remote_exec": {
      "command": "uv",
      "args": ["run", "mcp-remote-exec"],
      "env": {
        "I_ACCEPT_RISKS": "true",
        "HOST": "192.168.1.100",
        "SSH_USERNAME": "root",
        "SSH_PASSWORD": "your_password"
      }
    }
  }
}
```

3. Restart Claude Desktop

## MCP Tools

The server provides these tools for AI assistants.

### Command Execution

- `ssh_exec_command` - Execute bash commands on remote server
  - **Output Limit**: Results are truncated to 25,000 characters by default (configurable via `CHARACTER_LIMIT`)
  - **Response Formats**:
    - `text`: Human-readable output with sections for STDOUT, STDERR, and exit code
    - `json`: Structured data with separate stdout/stderr, truncation flags, and original lengths

### File Operations

- `ssh_upload_file` - Upload files to remote server
  - **Default Behavior**: Fails if remote file exists (set `overwrite=true` to replace)
  - **File Size Limit**: 10MB by default (configurable via `MAX_FILE_SIZE`)
  - **Permissions**: Optional parameter to set file permissions using octal notation
    - Specify as decimal integer representing octal value
    - Example: `permissions=644` sets file to `rw-r--r--` (owner read/write, group read, others read)
    - Example: `permissions=755` sets file to `rwxr-xr-x` (owner all, group/others read+execute)
    - Example: `permissions=600` sets file to `rw-------` (owner read/write only)

- `ssh_download_file` - Download files from remote server
  - **Default Behavior**: Fails if local file exists (set `overwrite=true` to replace)
  - **File Size Limit**: 10MB by default (configurable via `MAX_FILE_SIZE`)
  - **Safety**: Both upload and download default to `overwrite=false` to prevent accidental data loss

## Usage Examples

### Command Execution Examples

```
Check disk space: df -h
Show running processes: ps aux
Install packages: apt install nginx
View log files: tail -f /var/log/app.log
System information: uname -a
```

### File Transfer Examples

```
Download log: /var/log/nginx/access.log to ./nginx.log
Upload config: ./config.yaml to /etc/app/config.yaml
Download backup: /backups/database.sql to ./backup.sql
Upload script: ./install.sh to /opt/scripts/install.sh
```

## Development

### Running Tests

```bash
# Run unit tests
uv run pytest tests/ -v

# Run tests with coverage report
uv run pytest tests/ -v --cov=src/mcp_remote_exec --cov-report=term-missing --cov-report=html

# Using taskipy shortcuts
uv run task test         # Run all tests
uv run task test-cov     # Run tests with coverage

# Run in development mode
uv run mcp-remote-exec --help

# Test with local configuration
cp .env.example .env
# Edit .env with your test SSH server
uv run mcp-remote-exec
```

### Project Structure

```
src/mcp_remote_exec/
├── main.py                    # CLI entry point
├── config/                    # Configuration layer
│   ├── __init__.py
│   └── ssh_config.py
├── data_access/               # SSH/SFTP operations
│   ├── __init__.py
│   ├── exceptions.py
│   ├── ssh_connection_manager.py
│   └── sftp_manager.py
├── services/                  # Business logic
│   ├── __init__.py
│   ├── command_service.py
│   ├── file_transfer_service.py
│   └── output_formatter.py
└── presentation/              # FastMCP tools
    ├── __init__.py
    ├── mcp_tools.py
    └── request_models.py
```

## Security Best Practices

1. **Risk Acceptance**: Always set `I_ACCEPT_RISKS=true` after understanding implications
2. **Authentication**: Use SSH keys instead of passwords when possible
3. **Access Control**: Limit SSH user permissions on remote servers
4. **Monitoring**: Monitor logs for suspicious activity
5. **Backups**: Maintain backups before making changes
6. **Command Review**: Always review dangerous commands before execution

## Troubleshooting

### Configuration Errors

```
No SSH host configuration found
```

- Ensure `.env` file exists with `HOST` set
- Check environment variable formatting

### Authentication Errors

```
Authentication failed
```

- Verify SSH credentials in `.env`
- Check SSH user permissions on remote server
- Test SSH connection manually: `ssh user@host`

### Connection Errors

```
SSH connection failed
```

- Check network connectivity to remote server
- Verify SSH port (default 22) is open
- Check firewall rules

### SSH Key Errors

```
SSH key file not found
```

- Verify the `SSH_KEY` environment variable points to an existing private key file
- Check file path is absolute or correctly relative to working directory
- Ensure the key file has proper permissions (typically 600: `-rw-------`)
- Test key file: `ssh -i /path/to/key user@host`

```
Failed to load private key
```

- The key file exists but is corrupted or in unsupported format
- Supported formats: RSA, Ed25519, ECDSA
- **Ed25519 Support**: Requires Paramiko >= 3.x for Ed25519 key support. Earlier versions only support RSA and ECDSA
- Test key validity: `ssh-keygen -y -f /path/to/key`
- If key is encrypted with passphrase, it must be decrypted first

### Host Key Verification Errors

```
Server 'hostname' not found in known_hosts
```

**Problem**: The SSH host's key is not in the known_hosts file, causing strict host key checking to fail.

**Solutions**:

**Option 1: Add host to known_hosts (Recommended for production)**

```bash
# On the system running mcp-remote-exec
ssh-keyscan -H your.server.com >> ~/.ssh/known_hosts

# For Docker containers, add to the container's known_hosts
docker exec container_name ssh-keyscan -H your.server.com >> /home/appuser/.ssh/known_hosts
```

**Option 2: Disable strict checking (Convenient for dev/containers)**

```bash
# In .env file
SSH_STRICT_HOST_KEY_CHECKING=false
```

**When to use each option**:

- **Strict checking (true)**: Production, security-critical environments
- **Auto-accept (false)**: Development, Docker containers, trusted networks, frequently changing hosts

### Command Execution Errors

```
Command execution timeout
```

- Increase `TIMEOUT` setting in `.env`
- Check if remote server is responsive
- Verify command doesn't require user input

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details

## Support

- **Issues**: [GitHub Issues](https://github.com/husniadil/mcp-remote-exec/issues)
- **Discussions**: [GitHub Discussions](https://github.com/husniadil/mcp-remote-exec/discussions)

## Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp)
- Follows [Model Context Protocol](https://modelcontextprotocol.io/) specification
- Uses [Paramiko](https://www.paramiko.org/) for SSH connections

---

**Made with ❤️ for the MCP and SSH community**

⭐ If you find this useful, please star the repository!
