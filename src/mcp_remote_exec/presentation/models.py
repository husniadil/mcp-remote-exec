"""
Request Models for SSH MCP Remote Exec

Pydantic models for input validation and type checking in FastMCP tools.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator

from mcp_remote_exec.common.enums import ResponseFormat
from mcp_remote_exec.common.constants import MAX_TIMEOUT
from mcp_remote_exec.common.validators import pydantic_permissions_field_validator


class SSHExecCommandInput(BaseModel):
    """Input model for executing SSH commands"""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    command: str = Field(
        ...,
        description="Bash command to execute (required)",
        min_length=1,
        max_length=10000,
    )

    timeout: int = Field(
        30,
        description=f"Command timeout in seconds (default: 30, max: {MAX_TIMEOUT})",
        ge=1,
        le=MAX_TIMEOUT,
    )

    response_format: ResponseFormat = Field(
        default=ResponseFormat.TEXT,
        description="Output format: 'text' for human-readable or 'json' for structured data",
    )


class SSHUploadFileInput(BaseModel):
    """Input model for uploading files to remote SSH server"""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    local_path: str = Field(
        ...,
        description="Local file path to upload - absolute or relative (required)",
        min_length=1,
        max_length=4096,
    )

    remote_path: str = Field(
        ...,
        description="Remote destination path on your SSH server (required)",
        min_length=1,
        max_length=4096,
    )

    overwrite: bool = Field(
        default=False,
        description="Overwrite existing files (default: False, will fail if file exists)",
    )

    permissions: int | None = Field(
        None,
        description=(
            "File permissions in octal notation expressed as decimal integer. "
            "Common values: 644 (rw-r--r--), 755 (rwxr-xr-x), 600 (rw-------), 700 (rwx------). "
            "Each digit must be 0-7. Examples: 644, 755, 600, 700, 444, 400."
        ),
        ge=0,
        le=777,
    )

    # Reusable permissions validator from common layer
    validate_permissions = field_validator("permissions")(
        pydantic_permissions_field_validator
    )


class SSHDownloadFileInput(BaseModel):
    """Input model for downloading files from remote SSH server"""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    remote_path: str = Field(
        ...,
        description="Remote file path on your SSH server to download (required)",
        min_length=1,
        max_length=4096,
    )

    local_path: str = Field(
        ...,
        description="Local destination path - absolute or relative (required)",
        min_length=1,
        max_length=4096,
    )

    overwrite: bool = Field(
        default=False,
        description="Overwrite existing local files (default: False, will fail if file exists)",
    )
