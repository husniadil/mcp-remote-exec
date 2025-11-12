"""
Pydantic Models for Proxmox Plugin

Input validation for Proxmox container operations.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator

from mcp_remote_exec.common.enums import ResponseFormat
from mcp_remote_exec.common.constants import MAX_TIMEOUT
from mcp_remote_exec.common.validators import pydantic_permissions_field_validator


class ProxmoxContainerExecInput(BaseModel):
    """Input model for executing commands in a container"""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    ctid: int = Field(
        ..., description="Container ID (e.g., 100, 101, 102)", ge=100, le=999999999
    )
    command: str = Field(
        ...,
        description="Bash command to execute in the container",
        min_length=1,
        max_length=10000,
    )
    timeout: int = Field(
        default=30,
        description=f"Command timeout in seconds (default: 30, max: {MAX_TIMEOUT})",
        ge=1,
        le=MAX_TIMEOUT,
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.TEXT,
        description="Output format: 'text' or 'json'",
    )


class ProxmoxListContainersInput(BaseModel):
    """Input model for listing containers"""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    response_format: ResponseFormat = Field(
        default=ResponseFormat.TEXT,
        description="Output format: 'json' or 'text'",
    )


class ProxmoxContainerStatusInput(BaseModel):
    """Input model for getting container status"""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    ctid: int = Field(
        ..., description="Container ID to check status for", ge=100, le=999999999
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.TEXT,
        description="Output format: 'json' or 'text'",
    )


class ProxmoxContainerActionInput(BaseModel):
    """Input model for container actions (start/stop)"""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    ctid: int = Field(
        ..., description="Container ID to perform action on", ge=100, le=999999999
    )


class ProxmoxDownloadFileInput(BaseModel):
    """Input model for downloading files from container"""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    ctid: int = Field(
        ..., description="Container ID to download file from", ge=100, le=999999999
    )
    container_path: str = Field(
        ...,
        description="Path to file inside the container",
        min_length=1,
        max_length=4096,
    )
    local_path: str = Field(
        ...,
        description="Local path where file will be saved",
        min_length=1,
        max_length=4096,
    )
    overwrite: bool = Field(
        default=False,
        description="Whether to overwrite local file if it exists (default: False)",
    )


class ProxmoxUploadFileInput(BaseModel):
    """Input model for uploading files to container"""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    ctid: int = Field(
        ..., description="Container ID to upload file to", ge=100, le=999999999
    )
    local_path: str = Field(
        ...,
        description="Local path to file to upload",
        min_length=1,
        max_length=4096,
    )
    container_path: str = Field(
        ...,
        description="Destination path inside container",
        min_length=1,
        max_length=4096,
    )
    permissions: int | None = Field(
        None,
        description="File permissions as octal (e.g., 644, 755)",
        ge=0,
        le=777,
    )
    overwrite: bool = Field(
        default=False,
        description="Whether to overwrite container file if it exists (default: False)",
    )

    # Reusable permissions validator from common layer
    validate_permissions = field_validator("permissions")(
        pydantic_permissions_field_validator
    )
