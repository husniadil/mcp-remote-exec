# ImageKit File Transfer Plugin

The ImageKit plugin enables two-phase file transfers for scenarios where the MCP server runs behind an HTTP gateway, making direct SFTP connections between client and server impossible.

## Problem Statement

When running the MCP server through an HTTP gateway:

- Direct SFTP connections don't work because "local" paths refer to the gateway server, not the actual client machine
- The client (AI assistant) cannot directly transfer files to/from the remote SSH server
- Standard `ssh_upload_file` and `ssh_download_file` tools become unusable

## Solution

ImageKit acts as a temporary storage bridge for file transfers:

1. **Upload**: Client → ImageKit → Server
2. **Download**: Server → ImageKit → Client

The plugin provides a two-phase transfer protocol with short-lived tokens for security.

## Architecture

### Components

- **ImageKitConfig**: Manages ImageKit credentials and configuration
- **ImageKitClient**: Wraps ImageKit SDK operations
- **TransferManager**: Tracks active transfers with automatic cleanup
- **ImageKitService**: Business logic for two-phase transfers
- **MCP Tools**: 4 tools for upload/download workflows

### Integration

When the ImageKit plugin is enabled:

- SSH file transfer tools (`ssh_upload_file`, `ssh_download_file`) are NOT registered
- ImageKit tools are registered instead
- Proxmox plugin continues using SFTP for internal operations (works fine server-side)

## Configuration

### Environment Variables

```bash
# Required for ImageKit plugin
IMAGEKIT_PUBLIC_KEY=your_public_key_here
IMAGEKIT_PRIVATE_KEY=your_private_key_here
IMAGEKIT_URL_ENDPOINT=https://ik.imagekit.io/your_id

# Enable the plugin
ENABLE_IMAGEKIT=true

# Optional: Folder to organize transfer files (default: /mcp-remote-exec)
# This helps organize temporary files and avoid conflicts with existing files
IMAGEKIT_FOLDER=/mcp-remote-exec

# Optional: Transfer timeout in seconds (default: 3600 = 1 hour)
IMAGEKIT_TRANSFER_TIMEOUT=3600
```

### Setup

1. Create an ImageKit account at https://imagekit.io
2. Get your API credentials from the ImageKit dashboard
3. Add credentials to your `.env` file
4. Set `ENABLE_IMAGEKIT=true`

## Available Tools

### 1. imagekit_request_upload

**Purpose**: Initiate file upload from client to server

**Step 1 of 3** in the upload process.

**Input**:

- `remote_path` (string): Destination path on server (e.g., `/data/file.txt`)
- `permissions` (int, optional): File permissions as octal (e.g., 644, 755)
- `overwrite` (bool): Whether to overwrite existing file (default: false)

**Output**:

```json
{
  "transfer_id": "abc-123-def-456",
  "upload_command": "curl -X POST 'https://upload.imagekit.io/...' ...",
  "expires_in": 3600
}
```

**Example**:

```python
imagekit_request_upload(
    remote_path="/data/app.conf",
    permissions=644,
    overwrite=False
)
```

### 2. imagekit_confirm_upload

**Purpose**: Complete upload after client uploads to ImageKit

**Step 3 of 3** in the upload process (step 2 is executing the curl command).

**Input**:

- `transfer_id` (string): Transfer ID from `imagekit_request_upload`

**Output**:

```json
{
  "success": true,
  "message": "Successfully uploaded to /data/app.conf",
  "remote_path": "/data/app.conf",
  "bytes_transferred": 1024
}
```

**Example**:

```python
imagekit_confirm_upload(transfer_id="abc-123-def-456")
```

### 3. imagekit_request_download

**Purpose**: Initiate file download from server to client

**Step 1 of 3** in the download process.

**Input**:

- `remote_path` (string): Source path on server (e.g., `/data/file.txt`)

**Output**:

```json
{
  "transfer_id": "abc-123-def-456",
  "download_url": "https://ik.imagekit.io/...",
  "download_command": "curl -o '<YOUR_FILE_PATH>' 'https://...'",
  "expires_in": 3600
}
```

**Example**:

```python
imagekit_request_download(remote_path="/data/app.conf")
```

### 4. imagekit_confirm_download

**Purpose**: Complete download and cleanup ImageKit

**Step 3 of 3** in the download process (step 2 is executing the curl command).

**Input**:

- `transfer_id` (string): Transfer ID from `imagekit_request_download`

**Output**:

```json
{
  "success": true,
  "message": "Download completed and cleaned up",
  "remote_path": "/data/app.conf"
}
```

**Example**:

```python
imagekit_confirm_download(transfer_id="abc-123-def-456")
```

## Usage Workflows

### Upload Workflow

```
1. Client: imagekit_request_upload(remote_path="/data/file.txt")
   Server: Returns upload_command and transfer_id

2. Client: Execute the upload_command from your terminal:
   $ curl -X POST 'https://upload.imagekit.io/...' -F 'file=@/local/file.txt' ...

3. Client: imagekit_confirm_upload(transfer_id="abc-123-def")
   Server: Downloads from ImageKit, saves to /data/file.txt, cleans up
```

### Download Workflow

```
1. Client: imagekit_request_download(remote_path="/data/file.txt")
   Server: Uploads to ImageKit, returns download_url and transfer_id

2. Client: Execute the download_command from your terminal:
   $ curl -o '/local/file.txt' 'https://ik.imagekit.io/...'

3. Client: imagekit_confirm_download(transfer_id="abc-123-def")
   Server: Deletes file from ImageKit
```

### Proxmox Container Upload (with ImageKit)

```
1. Client: imagekit_request_upload(remote_path="/tmp/app.conf")
   Server: Returns upload_command

2. Client: Execute curl command to upload file

3. Client: imagekit_confirm_upload(transfer_id="abc-123-def")
   Server: File now at /tmp/app.conf on Proxmox host

4. Client: proxmox_upload_file_to_container(
       ctid=100,
       local_path="/tmp/app.conf",
       container_path="/etc/app/app.conf"
   )
   Server: Uses SFTP internally to move file to container
```

## Security Features

1. **Short-lived tokens**: Upload/download tokens expire after configured timeout (default: 1 hour)
2. **Path validation**: Prevents directory traversal attacks (`..` in paths)
3. **Automatic cleanup**: Files deleted from ImageKit after successful transfer
4. **Transfer expiration**: Old transfer states automatically cleaned up
5. **File existence checks**: Prevents accidental overwrites unless explicitly allowed

## State Management

The plugin tracks active transfers in memory:

```python
{
  "transfer_id": {
    "operation": "upload" | "download",
    "remote_path": "/path/on/server",
    "imagekit_file_id": "ik_file_id",
    "timestamp": datetime,
    "permissions": 644,
    "overwrite": false
  }
}
```

Expired transfers (older than timeout) are automatically cleaned up on each request.

## Error Handling

Common errors and solutions:

### "Transfer not found or expired"

- The transfer ID is invalid or the transfer timed out
- Start a new transfer with `imagekit_request_upload/download`

### "File not found on ImageKit"

- The upload didn't complete successfully
- Verify the curl command executed without errors
- Check ImageKit dashboard for upload status

### "Remote file already exists"

- File exists and `overwrite=false`
- Either delete the remote file or set `overwrite=true`

### "IMAGEKIT_PUBLIC_KEY not set"

- ImageKit credentials not configured
- Add credentials to `.env` file

## Limitations

1. **File size**: Subject to ImageKit free tier limits (typically 25MB per file)
2. **Transfer timeout**: Files must be transferred within the timeout period (default: 1 hour)
3. **Client execution**: Requires client to execute curl commands manually
4. **Network dependency**: Requires both server and client to reach ImageKit

## Comparison with Direct SFTP

| Feature              | SFTP            | ImageKit                                      |
| -------------------- | --------------- | --------------------------------------------- |
| Setup                | SSH credentials | ImageKit account + credentials                |
| Transfer method      | Direct          | Two-phase via ImageKit                        |
| HTTP gateway support | ❌ No           | ✅ Yes                                        |
| File size limit      | Server config   | ImageKit limits                               |
| Security             | SSH keys        | Short-lived tokens                            |
| Client steps         | 1 tool call     | 3 steps (request → upload/download → confirm) |

## Integration with Proxmox Plugin

The ImageKit and Proxmox plugins work together seamlessly:

- **Client ↔ Host transfers**: Use ImageKit tools
- **Host ↔ Container transfers**: Proxmox uses SFTP internally (transparent to user)

When both plugins are enabled:

1. Proxmox operations continue working normally
2. File transfers to/from Proxmox host use ImageKit
3. Server-side SFTP still used for `pct push/pull` operations

## Development

### Adding to Plugin Registry

The plugin is automatically discovered by the registry when available:

```python
# In plugins/registry.py
try:
    from mcp_remote_exec.plugins.imagekit import ImageKitPlugin
    self.plugins.append(ImageKitPlugin())
except ImportError:
    pass
```

### Testing

```bash
# Set up test environment
export IMAGEKIT_PUBLIC_KEY=test_public_key
export IMAGEKIT_PRIVATE_KEY=test_private_key
export IMAGEKIT_URL_ENDPOINT=https://ik.imagekit.io/test_id
export ENABLE_IMAGEKIT=true

# Run server
uv run mcp-remote-exec
```

## Troubleshooting

### Plugin not activating

Check logs for:

```
ImageKit plugin disabled: credentials not configured
ImageKit plugin disabled: ENABLE_IMAGEKIT not set to true
```

Solution: Verify all environment variables are set correctly.

### Upload/download failures

1. Check ImageKit dashboard for file status
2. Verify curl command executed successfully
3. Check transfer hasn't expired
4. Review server logs for detailed error messages

### SFTP still used instead of ImageKit

Verify:

- `ENABLE_IMAGEKIT=true` is set
- Plugin logs show "ImageKit plugin enabled"
- Tool list shows ImageKit tools, not SSH file transfer tools

## Future Enhancements

- [ ] Support for large file uploads (chunked transfers)
- [ ] Progress reporting for long transfers
- [ ] Automatic retry on transient failures
- [ ] Alternative storage bridges (S3, GCS, etc.)
- [ ] Direct client integration (no manual curl execution)
