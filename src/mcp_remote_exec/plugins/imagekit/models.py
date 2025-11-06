"""
Data models for ImageKit plugin
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class TransferOperation(str, Enum):
    """Type of file transfer operation"""

    UPLOAD = "upload"
    DOWNLOAD = "download"


class TransferState(BaseModel):
    """State of an active file transfer"""

    model_config = ConfigDict(use_enum_values=True)

    transfer_id: str
    operation: TransferOperation
    remote_path: str
    imagekit_file_id: str | None = None
    timestamp: datetime
    permissions: int | None = None
    overwrite: bool = False
    ctid: int | None = None  # Optional: Proxmox container ID for auto-push


class UploadRequestResult(BaseModel):
    """Result of upload request"""

    transfer_id: str
    upload_command: str
    expires_in: int


class DownloadRequestResult(BaseModel):
    """Result of download request"""

    transfer_id: str
    download_url: str
    download_command: str
    expires_in: int


class TransferConfirmResult(BaseModel):
    """Result of transfer confirmation"""

    success: bool
    message: str
    remote_path: str | None = None
    bytes_transferred: int = 0


class ImageKitRequestUploadInput(BaseModel):
    """Input for imagekit_request_upload tool"""

    remote_path: str = Field(..., min_length=1)
    permissions: int | None = Field(None, ge=0, le=777)
    overwrite: bool = False
    ctid: int | None = Field(
        None, ge=100, le=999999999
    )  # Optional Proxmox container ID


class ImageKitConfirmUploadInput(BaseModel):
    """Input for imagekit_confirm_upload tool"""

    transfer_id: str = Field(..., min_length=1)
    file_id: str | None = Field(
        None, min_length=1
    )  # Optional: bypass search if provided


class ImageKitRequestDownloadInput(BaseModel):
    """Input for imagekit_request_download tool"""

    remote_path: str = Field(..., min_length=1)
    ctid: int | None = Field(
        None, ge=100, le=999999999
    )  # Optional Proxmox container ID


class ImageKitConfirmDownloadInput(BaseModel):
    """Input for imagekit_confirm_download tool"""

    transfer_id: str = Field(..., min_length=1)
