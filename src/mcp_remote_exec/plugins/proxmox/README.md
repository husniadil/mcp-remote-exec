# Proxmox Plugin for SSH MCP Remote Exec

Container management tools for Proxmox Virtual Environment (VE).

## Overview

The Proxmox plugin extends SSH MCP Remote Exec with specialized tools for managing LXC containers on Proxmox VE. It wraps the `pct` (Proxmox Container Toolkit) commands with a user-friendly interface for AI assistants.

## Requirements

- **SSH Host**: Must be a Proxmox VE server
- **SSH User**: Must have permissions to run `pct` commands (typically root)
- **Activation**: Set `ENABLE_PROXMOX=true` in your `.env` file

## Architecture

The plugin follows the same 4-layer architecture as the core:

```
plugins/proxmox/
├── __init__.py       # Plugin registration and activation
├── models.py         # Pydantic input models for validation
├── services.py       # ProxmoxService (business logic)
└── tools.py          # MCP tool definitions
```

**Key Design**:

- **Reuses core SSH connection** - No separate connections needed
- **Command wrapping** - Transforms `proxmox_container_exec(100, "ls")` → `pct exec 100 -- bash -c 'ls'`
- **Output parsing** - Parses `pct list`, `pct status` output into structured data
- **Error handling** - Provides helpful suggestions when containers not found

## Configuration

```bash
# .env
I_ACCEPT_RISKS=true
HOST=192.168.1.100      # Your Proxmox host
SSH_USERNAME=root
SSH_PASSWORD=secret

# Activate Proxmox plugin
ENABLE_PROXMOX=true

# Optional: Shared limits (apply to all tools)
CHARACTER_LIMIT=25000
MAX_FILE_SIZE=10485760
TIMEOUT=30
```

## Available Tools

### Container Management (5 tools)

#### `proxmox_container_exec_command`

Execute bash commands inside LXC containers.

**Parameters**:

- `ctid` (int, required): Container ID (100-999999999)
- `command` (str, required): Bash command to execute
- `timeout` (int, optional): Command timeout in seconds (default: 30)
- `response_format` (str, optional): Output format - "text" or "json" (default: "text")

**Examples**:

```python
# Check disk space in container 100
proxmox_container_exec_command(ctid=100, command="df -h")

# Update packages with longer timeout
proxmox_container_exec_command(
    ctid=101,
    command="apt update && apt upgrade -y",
    timeout=300
)

# Get process list in JSON format
proxmox_container_exec_command(
    ctid=100,
    command="ps aux",
    response_format="json"
)
```

---

#### `proxmox_list_containers`

List all LXC containers on the Proxmox host.

**Parameters**:

- `response_format` (str, optional): Output format - "json" or "text" (default: "text")

**Examples**:

```python
# List containers in JSON format
proxmox_list_containers()

# List containers in human-readable table
proxmox_list_containers(response_format="text")
```

**JSON Output**:

```json
[
  { "ctid": 100, "status": "running", "name": "webserver" },
  { "ctid": 101, "status": "stopped", "name": "database" },
  { "ctid": 102, "status": "running", "name": "cache" }
]
```

**Text Output**:

```
CTID | Status  | Name
--------------------------------------------------
 100 | running | webserver
 101 | stopped | database
 102 | running | cache
```

---

#### `proxmox_container_status`

Get the current status of a specific container.

**Parameters**:

- `ctid` (int, required): Container ID
- `response_format` (str, optional): Output format - "json" or "text" (default: "text")

**Examples**:

```python
# Check status (default: text format)
proxmox_container_status(ctid=100)

# Check status in JSON format
proxmox_container_status(ctid=100, response_format="json")
```

**JSON Output**:

```json
{ "status": "running" }
```

**Text Output**:

```
Container 100 is running
```

---

#### `proxmox_start_container`

Start a stopped LXC container.

**Parameters**:

- `ctid` (int, required): Container ID to start

**Examples**:

```python
proxmox_start_container(ctid=100)
```

**Output**:

```json
{
  "success": true,
  "message": "Container 100 started successfully",
  "ctid": 100
}
```

---

#### `proxmox_stop_container`

Stop a running LXC container.

**Parameters**:

- `ctid` (int, required): Container ID to stop

**Examples**:

```python
proxmox_stop_container(ctid=100)
```

**Output**:

```json
{
  "success": true,
  "message": "Container 100 stopped successfully",
  "ctid": 100
}
```

---

### File Operations (2 tools)

#### `proxmox_download_file_from_container`

Download a file from inside a container to your local machine.

**Parameters**:

- `ctid` (int, required): Container ID
- `container_path` (str, required): Path to file inside container
- `local_path` (str, required): Local path where file will be saved
- `overwrite` (bool, optional): Overwrite local file if exists (default: False)

**How it works**:

1. Uses `pct pull` to transfer file from container to Proxmox host temp location
2. Downloads from host to local via SFTP
3. Cleans up temp file on host

**Examples**:

```python
# Download Nginx config
proxmox_download_file_from_container(
    ctid=100,
    container_path="/etc/nginx/nginx.conf",
    local_path="./nginx.conf"
)

# Download log file (overwrite if exists)
proxmox_download_file_from_container(
    ctid=100,
    container_path="/var/log/app.log",
    local_path="./container-100.log",
    overwrite=True
)
```

**Output**:

```json
{
  "success": true,
  "message": "File downloaded successfully from container 100",
  "ctid": 100,
  "container_path": "/etc/nginx/nginx.conf",
  "local_path": "./nginx.conf",
  "bytes_transferred": 2048
}
```

---

#### `proxmox_upload_file_to_container`

Upload a file from your local machine to inside a container.

**Parameters**:

- `ctid` (int, required): Container ID
- `local_path` (str, required): Local file path to upload
- `container_path` (str, required): Destination path inside container
- `permissions` (int, optional): File permissions as octal (default: 644)
- `overwrite` (bool, optional): Overwrite container file if exists (default: False)

**How it works**:

1. Uploads file from local to Proxmox host temp location via SFTP
2. Uses `pct push` to transfer from host to inside container
3. Sets file permissions with `chmod`
4. Cleans up temp file on host

**Examples**:

```python
# Upload configuration file
proxmox_upload_file_to_container(
    ctid=100,
    local_path="./nginx.conf",
    container_path="/etc/nginx/nginx.conf",
    permissions=644,
    overwrite=True
)

# Upload executable script
proxmox_upload_file_to_container(
    ctid=100,
    local_path="./deploy.sh",
    container_path="/root/deploy.sh",
    permissions=755
)
```

**Output**:

```json
{
  "success": true,
  "message": "File uploaded successfully to container 100",
  "ctid": 100,
  "local_path": "./nginx.conf",
  "container_path": "/etc/nginx/nginx.conf",
  "permissions": "644",
  "bytes_transferred": 2048
}
```

---

## Tool Separation: Core vs Plugin

Understanding when to use core tools vs plugin tools:

| Task                         | Tool to Use                                    | Why                      |
| ---------------------------- | ---------------------------------------------- | ------------------------ |
| Run command on Proxmox host  | `ssh_exec_command()`                           | Direct host access       |
| Run command in container     | `proxmox_container_exec_command()`             | Needs `pct exec` wrapper |
| Check Proxmox cluster status | `ssh_exec_command("pvecm status")`             | Host-level operation     |
| Check container resources    | `proxmox_container_exec_command(100, "df -h")` | Container operation      |
| Upload to Proxmox host       | `ssh_upload_file()`                            | Direct SFTP              |
| Upload to container          | `proxmox_upload_file_to_container()`           | Needs SFTP + `pct push`  |
| Download from Proxmox host   | `ssh_download_file()`                          | Direct SFTP              |
| Download from container      | `proxmox_download_file_from_container()`       | Needs `pct pull` + SFTP  |
| List containers              | `proxmox_list_containers()`                    | Parses `pct list` output |
| Manage containers            | `proxmox_start/stop_container()`               | Uses `pct start/stop`    |

**Rule of thumb**: If it operates on/inside containers, use plugin tools. If it operates on the Proxmox host itself, use core tools.

## Common Use Cases

### 1. Container Health Check

```python
# List all containers
containers = proxmox_list_containers()

# Check status of specific container
status = proxmox_container_status(ctid=100)

# Check resources inside container
proxmox_container_exec_command(ctid=100, command="df -h && free -h")
```

### 2. Deploy Application Configuration

```python
# Upload config file
proxmox_upload_file_to_container(
    ctid=100,
    local_path="./app.conf",
    container_path="/etc/app/app.conf",
    overwrite=True
)

# Restart service to apply changes
proxmox_container_exec_command(
    ctid=100,
    command="systemctl restart app"
)

# Verify service is running
proxmox_container_exec_command(
    ctid=100,
    command="systemctl status app"
)
```

### 3. Backup Container Logs

```python
# Download application log
proxmox_download_file_from_container(
    ctid=100,
    container_path="/var/log/app/app.log",
    local_path="./backups/container-100-app.log"
)

# Download system log
proxmox_download_file_from_container(
    ctid=100,
    container_path="/var/log/syslog",
    local_path="./backups/container-100-syslog"
)
```

### 4. Update Multiple Containers

```python
# List all containers
containers = proxmox_list_containers()

# Update each running container
for container in containers:
    if container["status"] == "running":
        proxmox_container_exec_command(
            ctid=container["ctid"],
            command="apt update && apt upgrade -y",
            timeout=300
        )
```

### 5. Container Lifecycle Management

```python
# Start container
proxmox_start_container(ctid=100)

# Wait and verify
import time
time.sleep(5)
status = proxmox_container_status(ctid=100)

# Run initialization script
if status["status"] == "running":
    proxmox_container_exec_command(
        ctid=100,
        command="/root/init.sh"
    )
```

## Error Handling

The plugin provides helpful error messages:

### Container Not Found

```json
{
  "success": false,
  "error": "Container 999 not found",
  "suggestion": "Use proxmox_list_containers to see available containers"
}
```

### File Already Exists

```json
{
  "success": false,
  "error": "File already exists in container: /etc/app/app.conf",
  "suggestion": "Set overwrite=true to replace existing file"
}
```

### Path Traversal Attempt

```json
{
  "success": false,
  "error": "Path cannot contain '..' (path traversal not allowed)"
}
```

## Security Considerations

1. **Container Access**: The plugin executes commands as root inside containers
2. **File Operations**: Can read/write any file in containers (respecting permissions)
3. **No Additional Safety**: Plugin relies on core's `I_ACCEPT_RISKS` check
4. **Path Validation**: Basic validation to prevent path traversal attacks
5. **No Host Operations**: Plugin intentionally excludes redundant host tools (use core tools instead)

## Troubleshooting

### Plugin Not Activating

```bash
# Check if ENABLE_PROXMOX is set
echo $ENABLE_PROXMOX  # Should output: true

# Check logs when starting
uv run mcp-remote-exec
# Look for: "Proxmox plugin enabled" and "Activated plugins: proxmox"
```

### Container Not Found

```python
# List available containers first
proxmox_list_containers()

# Verify ctid exists in the list
```

### Permission Denied

```python
# Check container status
proxmox_container_status(ctid=100)

# Container might be stopped - start it first
proxmox_start_container(ctid=100)
```

### File Transfer Issues

- **File size limits**: Respects `MAX_FILE_SIZE` from core config (default: 10MB)
- **Permissions**: Ensure SSH user has access to container
- **Disk space**: Check host and container have sufficient space

## Future Enhancements

Potential additions to the plugin:

- VM (qm) support in addition to containers
- Snapshot management
- Resource monitoring (CPU, memory, disk)
- Network configuration
- Template operations
- Backup/restore operations

## Contributing

To extend the plugin or add new tools, see the main project's CONTRIBUTING.md.

## License

Same as parent project (MIT License)
